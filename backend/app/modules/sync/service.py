from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.models import (
    Branch,
    Category,
    Inventory,
    InventoryMovement,
    Payment,
    Product,
    ProductVariant,
    Reservation,
    ReservationItem,
    Sale,
    SaleItem,
    SyncOperation,
    User,
)
from app.modules.auth.dependencies import require_branch_access
from app.modules.sync.schemas import (
    SyncConflictDetail,
    SyncTransactionBatchRequest,
    SyncTransactionBatchResponse,
    SyncTransactionItemRequest,
    SyncTransactionItemResult,
)


def resolve_sync_branch(db: Session, current_user: User, branch_id: int | None) -> Branch:
    if current_user.role.code == "PLATFORM_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "TENANT_OPERATION_FORBIDDEN_FOR_PLATFORM_ADMIN",
                "message": "El administrador de plataforma no tiene acceso a sincronización de catálogo.",
            },
        )

    target_branch_id = branch_id
    if target_branch_id is None:
        if current_user.branches:
            target_branch_id = current_user.branches[0].id
        else:
            stmt = select(Branch).where(Branch.is_active.is_(True))
            if current_user.tenant_id is not None:
                stmt = stmt.where(Branch.tenant_id == current_user.tenant_id)
            first_branch = db.scalar(stmt.order_by(Branch.id))
            if first_branch is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "BRANCH_NOT_FOUND", "message": "No se encontraron sucursales activas para la sincronización."},
                )
            target_branch_id = first_branch.id

    require_branch_access(current_user, target_branch_id)
    branch = db.get(Branch, target_branch_id)
    if branch is None or not branch.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BRANCH_NOT_FOUND", "message": "Sucursal no encontrada o inactiva."},
        )
    return branch


def get_sync_catalog(
    db: Session,
    current_user: User,
    branch_id: int | None = None,
    since: datetime | None = None,
) -> dict[str, Any]:
    branch = resolve_sync_branch(db, current_user, branch_id)
    tenant_id = current_user.tenant_id
    tenant_name = current_user.tenant.name if current_user.tenant is not None else "Empresa"

    now = datetime.now(UTC)
    catalog_version = f"cat-v1-{int(now.timestamp())}"

    # 1. Categories
    cat_stmt = select(Category).where(Category.is_active.is_(True))
    if tenant_id is not None:
        cat_stmt = cat_stmt.where(Category.tenant_id == tenant_id)
    categories = db.scalars(cat_stmt.order_by(Category.name)).all()

    # 2. Products
    prod_stmt = select(Product).options(joinedload(Product.category), joinedload(Product.images)).where(Product.is_active.is_(True))
    if tenant_id is not None:
        prod_stmt = prod_stmt.where(Product.tenant_id == tenant_id)
    products = db.scalars(prod_stmt.order_by(Product.name)).unique().all()

    # 3. Variants
    var_stmt = select(ProductVariant).options(
        joinedload(ProductVariant.size),
        joinedload(ProductVariant.color),
        joinedload(ProductVariant.product),
    ).where(ProductVariant.is_active.is_(True))
    if tenant_id is not None:
        var_stmt = var_stmt.where(ProductVariant.tenant_id == tenant_id)
    variants = db.scalars(var_stmt.order_by(ProductVariant.id)).all()

    # 4. Local Inventory for the target branch
    inv_stmt = select(Inventory).where(Inventory.branch_id == branch.id)
    if tenant_id is not None:
        inv_stmt = inv_stmt.where(Inventory.tenant_id == tenant_id)
    inventory_records = db.scalars(inv_stmt).all()

    # Serialize items
    serialized_categories = [
        {
            "id": cat.id,
            "name": cat.name,
            "is_active": cat.is_active,
        }
        for cat in categories
    ]

    serialized_products = []
    for prod in products:
        primary_img = None
        if prod.images:
            sorted_imgs = sorted(prod.images, key=lambda i: (not i.is_primary, i.sort_order))
            primary_img = sorted_imgs[0].image_url
        serialized_products.append(
            {
                "id": prod.id,
                "category_id": prod.category_id,
                "category_name": prod.category.name if prod.category else "",
                "name": prod.name,
                "code": prod.code,
                "slug": prod.slug,
                "description": prod.description,
                "audience": prod.audience,
                "size_system": prod.size_system,
                "price": prod.price,
                "image_url": primary_img,
                "is_active": prod.is_active,
            }
        )

    serialized_variants = [
        {
            "id": var.id,
            "product_id": var.product_id,
            "sku": var.sku,
            "size_id": var.size_id,
            "size_name": var.size.name if var.size else None,
            "size_type": var.size.size_type if var.size else None,
            "sort_order": var.size.sort_order if var.size else None,
            "color_id": var.color_id,
            "color_name": var.color.name if var.color else None,
            "price": var.product.price if var.product else 0,
            "is_active": var.is_active,
        }
        for var in variants
    ]

    serialized_inventory = [
        {
            "product_variant_id": inv.product_variant_id,
            "stock_quantity": inv.stock_quantity,
            "reserved_quantity": inv.reserved_quantity,
            "available_quantity": max(0, inv.stock_quantity - inv.reserved_quantity),
        }
        for inv in inventory_records
    ]

    return {
        "metadata": {
            "tenant_id": tenant_id,
            "tenant_name": tenant_name,
            "branch_id": branch.id,
            "branch_name": branch.name,
            "sync_timestamp": now,
            "catalog_version": catalog_version,
        },
        "categories": serialized_categories,
        "products": serialized_products,
        "variants": serialized_variants,
        "inventory": serialized_inventory,
    }


def _record_failed_sync_op(
    db: Session,
    current_user: User,
    branch: Branch,
    op_req: SyncTransactionItemRequest,
    status_str: str,
    conflict: SyncConflictDetail,
) -> SyncTransactionItemResult:
    now = datetime.now(UTC)
    sync_op = SyncOperation(
        tenant_id=current_user.tenant_id,
        client_operation_id=op_req.client_operation_id,
        branch_id=branch.id,
        user_id=current_user.id,
        operation_type=op_req.operation_type,
        status=status_str,
        payload=op_req.model_dump(mode="json"),
        conflict_detail=conflict.model_dump(mode="json"),
        processed_at=now,
    )
    db.add(sync_op)
    db.commit()
    return SyncTransactionItemResult(
        client_operation_id=op_req.client_operation_id,
        operation_type=op_req.operation_type,
        status=status_str,
        conflict_detail=conflict,
        processed_at=now,
    )


def _process_offline_sale(
    db: Session,
    current_user: User,
    branch: Branch,
    op_req: SyncTransactionItemRequest,
) -> SyncTransactionItemResult:
    payload = op_req.sale_payload
    if payload is None or not payload.items:
        conflict = SyncConflictDetail(code="INVALID_PAYLOAD", message="La venta no contiene items válidos.")
        return _record_failed_sync_op(db, current_user, branch, op_req, "REJECTED", conflict)

    # Check stock for all items
    insufficient_conflict = None
    locked_inventories: list[tuple[Inventory, int, Decimal]] = []

    for item in payload.items:
        inv = db.scalar(
            select(Inventory).where(
                Inventory.tenant_id == current_user.tenant_id,
                Inventory.branch_id == branch.id,
                Inventory.product_variant_id == item.product_variant_id,
            )
        )
        if inv is None:
            variant = db.get(ProductVariant, item.product_variant_id)
            sku = variant.sku if variant else f"VAR-{item.product_variant_id}"
            insufficient_conflict = SyncConflictDetail(
                code="INSUFFICIENT_STOCK",
                message=f"No existe registro de inventario para la variante {sku} en esta sucursal.",
                variant_id=item.product_variant_id,
                sku=sku,
                requested_quantity=item.quantity,
                available_quantity=0,
            )
            break

        available = inv.stock_quantity - inv.reserved_quantity
        if available < item.quantity:
            sku = inv.product_variant.sku if inv.product_variant else f"VAR-{item.product_variant_id}"
            insufficient_conflict = SyncConflictDetail(
                code="INSUFFICIENT_STOCK",
                message=f"Stock insuficiente para {sku}. Solicitado: {item.quantity}, disponible: {max(0, available)}.",
                variant_id=item.product_variant_id,
                sku=sku,
                requested_quantity=item.quantity,
                available_quantity=max(0, available),
            )
            break
        locked_inventories.append((inv, item.quantity, item.unit_price))

    if insufficient_conflict is not None:
        db.rollback()
        return _record_failed_sync_op(db, current_user, branch, op_req, "CONFLICT", insufficient_conflict)

    now = datetime.now(UTC)
    order_number = f"OFF-{int(now.timestamp())}-{uuid4().hex[:6].upper()}"
    gross_subtotal = Decimal("0")
    sale_items = []

    for inv, qty, unit_price in locked_inventories:
        line_total = unit_price * qty
        gross_subtotal += line_total
        sale_items.append(
            SaleItem(
                product_variant_id=inv.product_variant_id,
                quantity=qty,
                unit_price=unit_price,
                discount=Decimal("0"),
                line_total=line_total,
            )
        )

    sale_total = payload.total if payload.total > 0 else (gross_subtotal - payload.discount)
    sale = Sale(
        tenant_id=current_user.tenant_id,
        order_number=order_number,
        customer_id=payload.customer_id,
        branch_id=branch.id,
        cashier_id=current_user.id,
        channel="PHYSICAL",
        status="COMPLETED",
        fulfillment_type="PICKUP",
        subtotal=gross_subtotal,
        discount=payload.discount,
        total=sale_total,
        items=sale_items,
    )
    db.add(sale)
    db.flush()

    payment = Payment(
        tenant_id=current_user.tenant_id,
        sale_id=sale.id,
        method="CASH",
        provider="CASH_REGISTER",
        transaction_reference=f"CASH-{order_number}",
        status="APPROVED",
        amount=sale_total,
        received_amount=sale_total,
        change_amount=Decimal("0"),
        paid_at=payload.created_at or now,
    )
    db.add(payment)

    customer_summary = ""
    if payload.customer_name or payload.customer_nit:
        parts = [p for p in [payload.customer_name, f"CI/NIT: {payload.customer_nit}" if payload.customer_nit else None, f"Tel: {payload.customer_phone}" if payload.customer_phone else None] if p]
        customer_summary = f" ({' · '.join(parts)})"

    for inv, qty, _ in locked_inventories:
        stock_before = inv.stock_quantity
        inv.stock_quantity -= qty
        movement = InventoryMovement(
            tenant_id=current_user.tenant_id,
            inventory_id=inv.id,
            movement_type="SALE",
            quantity=qty,
            stock_before=stock_before,
            stock_after=inv.stock_quantity,
            reason=f"Venta presencial offline confirmada{customer_summary}"[:255],
            reference_type="sale",
            reference_id=sale.id,
            created_by=current_user.id,
        )
        db.add(movement)

    sync_op = SyncOperation(
        tenant_id=current_user.tenant_id,
        client_operation_id=op_req.client_operation_id,
        branch_id=branch.id,
        user_id=current_user.id,
        operation_type="SALE",
        status="CONFIRMED",
        payload=op_req.model_dump(mode="json"),
        conflict_detail=None,
        sale_id=sale.id,
        processed_at=now,
    )
    db.add(sync_op)
    db.commit()

    return SyncTransactionItemResult(
        client_operation_id=op_req.client_operation_id,
        operation_type="SALE",
        status="CONFIRMED",
        sale_id=sale.id,
        order_number=sale.order_number,
        processed_at=sync_op.processed_at,
    )


def _process_offline_reservation(
    db: Session,
    current_user: User,
    branch: Branch,
    op_req: SyncTransactionItemRequest,
) -> SyncTransactionItemResult:
    payload = op_req.reservation_payload
    if payload is None or not payload.items:
        conflict = SyncConflictDetail(code="INVALID_PAYLOAD", message="La reserva no contiene items válidos.")
        return _record_failed_sync_op(db, current_user, branch, op_req, "REJECTED", conflict)

    insufficient_conflict = None
    locked_inventories: list[tuple[Inventory, int]] = []

    for item in payload.items:
        inv = db.scalar(
            select(Inventory).where(
                Inventory.tenant_id == current_user.tenant_id,
                Inventory.branch_id == branch.id,
                Inventory.product_variant_id == item.product_variant_id,
            )
        )
        if inv is None:
            insufficient_conflict = SyncConflictDetail(
                code="INSUFFICIENT_STOCK",
                message=f"No existe registro de inventario para la variante {item.product_variant_id}.",
                variant_id=item.product_variant_id,
                requested_quantity=item.quantity,
                available_quantity=0,
            )
            break

        available = inv.stock_quantity - inv.reserved_quantity
        if available < item.quantity:
            insufficient_conflict = SyncConflictDetail(
                code="INSUFFICIENT_STOCK",
                message=f"Disponibilidad insuficiente para reserva. Solicitado: {item.quantity}, disponible: {max(0, available)}.",
                variant_id=item.product_variant_id,
                requested_quantity=item.quantity,
                available_quantity=max(0, available),
            )
            break
        locked_inventories.append((inv, item.quantity))

    if insufficient_conflict is not None:
        db.rollback()
        return _record_failed_sync_op(db, current_user, branch, op_req, "CONFLICT", insufficient_conflict)

    now = datetime.now(UTC)
    scheduled_for = payload.scheduled_for or (now + timedelta(days=2))
    expires_at = scheduled_for + timedelta(hours=2)

    customer_id = payload.customer_id if payload.customer_id is not None else current_user.id

    customer_parts = [
        f"Cliente: {payload.customer_name}" if payload.customer_name else None,
        f"CI/NIT: {payload.customer_nit}" if payload.customer_nit else None,
        f"Tel: {payload.customer_phone}" if payload.customer_phone else None,
    ]
    customer_meta = " | ".join(p for p in customer_parts if p)
    combined_notes = payload.notes or ""
    if customer_meta:
        combined_notes = f"{customer_meta} — {combined_notes}" if combined_notes else customer_meta

    reservation = Reservation(
        tenant_id=current_user.tenant_id,
        customer_id=customer_id,
        branch_id=branch.id,
        scheduled_for=scheduled_for,
        expires_at=expires_at,
        notes=combined_notes[:255] if combined_notes else None,
        status="PENDING",
    )
    db.add(reservation)
    db.flush()

    for inv, qty in locked_inventories:
        unit_price = Decimal("0")
        if inv.product_variant and inv.product_variant.product:
            unit_price = inv.product_variant.product.price
        else:
            variant = db.get(ProductVariant, inv.product_variant_id)
            if variant and variant.product:
                unit_price = variant.product.price

        res_item = ReservationItem(
            reservation_id=reservation.id,
            product_variant_id=inv.product_variant_id,
            quantity=qty,
            unit_price=unit_price,
        )
        db.add(res_item)
        inv.reserved_quantity += qty

    sync_op = SyncOperation(
        tenant_id=current_user.tenant_id,
        client_operation_id=op_req.client_operation_id,
        branch_id=branch.id,
        user_id=current_user.id,
        operation_type="RESERVATION",
        status="CONFIRMED",
        payload=op_req.model_dump(mode="json"),
        conflict_detail=None,
        reservation_id=reservation.id,
        processed_at=now,
    )
    db.add(sync_op)
    db.commit()

    return SyncTransactionItemResult(
        client_operation_id=op_req.client_operation_id,
        operation_type="RESERVATION",
        status="CONFIRMED",
        reservation_id=reservation.id,
        processed_at=sync_op.processed_at,
    )


def process_sync_transactions_batch(
    db: Session,
    current_user: User,
    batch: SyncTransactionBatchRequest,
) -> SyncTransactionBatchResponse:
    results: list[SyncTransactionItemResult] = []
    tenant_id = current_user.tenant_id

    for op_req in batch.operations:
        existing = db.scalar(
            select(SyncOperation).where(
                SyncOperation.tenant_id == tenant_id,
                SyncOperation.client_operation_id == op_req.client_operation_id,
            )
        )
        if existing is not None:
            order_number = existing.sale.order_number if existing.sale else None
            conflict = SyncConflictDetail(**existing.conflict_detail) if existing.conflict_detail else None
            results.append(
                SyncTransactionItemResult(
                    client_operation_id=existing.client_operation_id,
                    operation_type=existing.operation_type,
                    status=existing.status,
                    sale_id=existing.sale_id,
                    order_number=order_number,
                    reservation_id=existing.reservation_id,
                    conflict_detail=conflict,
                    processed_at=existing.processed_at,
                )
            )
            continue

        branch = db.get(Branch, op_req.branch_id)
        if branch is None or not branch.is_active or branch.tenant_id != tenant_id:
            conflict = SyncConflictDetail(
                code="BRANCH_NOT_FOUND",
                message="Sucursal no encontrada, inactiva o no pertenece a la empresa.",
            )
            fallback_branch_id = branch.id if branch else (current_user.branches[0].id if current_user.branches else op_req.branch_id)
            sync_op = SyncOperation(
                tenant_id=tenant_id,
                client_operation_id=op_req.client_operation_id,
                branch_id=fallback_branch_id,
                user_id=current_user.id,
                operation_type=op_req.operation_type,
                status="REJECTED",
                payload=op_req.model_dump(mode="json"),
                conflict_detail=conflict.model_dump(mode="json"),
            )
            db.add(sync_op)
            db.commit()
            results.append(
                SyncTransactionItemResult(
                    client_operation_id=op_req.client_operation_id,
                    operation_type=op_req.operation_type,
                    status="REJECTED",
                    conflict_detail=conflict,
                    processed_at=sync_op.processed_at,
                )
            )
            continue

        if op_req.operation_type == "SALE":
            results.append(_process_offline_sale(db, current_user, branch, op_req))
        elif op_req.operation_type == "RESERVATION":
            results.append(_process_offline_reservation(db, current_user, branch, op_req))
        else:
            conflict = SyncConflictDetail(
                code="UNSUPPORTED_OPERATION",
                message=f"Tipo de operación no soportado: {op_req.operation_type}",
            )
            results.append(
                SyncTransactionItemResult(
                    client_operation_id=op_req.client_operation_id,
                    operation_type=op_req.operation_type,
                    status="REJECTED",
                    conflict_detail=conflict,
                    processed_at=datetime.now(UTC),
                )
            )

    confirmed_count = sum(1 for r in results if r.status == "CONFIRMED")
    conflict_count = sum(1 for r in results if r.status in ("CONFLICT", "REJECTED"))

    return SyncTransactionBatchResponse(
        processed_count=len(results),
        confirmed_count=confirmed_count,
        conflict_count=conflict_count,
        results=results,
    )


def get_sync_transaction_status(
    db: Session,
    current_user: User,
    client_operation_id: str,
) -> SyncTransactionItemResult:
    op = db.scalar(
        select(SyncOperation).where(
            SyncOperation.tenant_id == current_user.tenant_id,
            SyncOperation.client_operation_id == client_operation_id,
        )
    )
    if op is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "OPERATION_NOT_FOUND", "message": "Operación de sincronización no encontrada."},
        )
    order_number = op.sale.order_number if op.sale else None
    conflict = SyncConflictDetail(**op.conflict_detail) if op.conflict_detail else None
    return SyncTransactionItemResult(
        client_operation_id=op.client_operation_id,
        operation_type=op.operation_type,
        status=op.status,
        sale_id=op.sale_id,
        order_number=order_number,
        reservation_id=op.reservation_id,
        conflict_detail=conflict,
        processed_at=op.processed_at,
    )


