from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.models import Branch, Inventory, Product, ProductVariant, Reservation, Sale, SaleItem
from app.modules.reports import ai_service
from app.modules.reports.schemas import ReportAssistantRequest, ReportAssistantResponse, ReportFilters, ReportSnapshot


def validate_report_filters(date_from: datetime | None, date_to: datetime | None) -> None:
    if date_from is not None and date_to is not None and date_from > date_to:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_DATE_RANGE", "message": "date_from must be earlier than or equal to date_to."},
        )


def _sale_filters(statement, date_from: datetime | None, date_to: datetime | None, branch_id: int | None):
    statement = statement.where(Sale.status == "CONFIRMED")
    if date_from is not None:
        statement = statement.where(Sale.created_at >= date_from)
    if date_to is not None:
        statement = statement.where(Sale.created_at <= date_to)
    if branch_id is not None:
        statement = statement.where(Sale.branch_id == branch_id)
    return statement


def revenue_summary(db: Session, date_from: datetime | None, date_to: datetime | None, branch_id: int | None) -> dict[str, object]:
    validate_report_filters(date_from, date_to)
    row = db.execute(_sale_filters(select(func.count(Sale.id), func.coalesce(func.sum(Sale.subtotal), 0), func.coalesce(func.sum(Sale.discount), 0), func.coalesce(func.sum(Sale.total), 0)), date_from, date_to, branch_id)).one()
    return {"sales_count": row[0], "subtotal": row[1], "discount": row[2], "total": row[3]}


def sales_by_branch(db: Session, date_from: datetime | None, date_to: datetime | None, branch_id: int | None) -> list[dict[str, object]]:
    validate_report_filters(date_from, date_to)
    statement = select(Sale.branch_id, Branch.name, func.count(Sale.id), func.coalesce(func.sum(Sale.total), 0)).outerjoin(Branch, Sale.branch_id == Branch.id).group_by(Sale.branch_id, Branch.name).order_by(func.coalesce(func.sum(Sale.total), 0).desc())
    return [{"branch_id": item[0], "branch_name": item[1] or "Digital", "sales_count": item[2], "total": item[3]} for item in db.execute(_sale_filters(statement, date_from, date_to, branch_id)).all()]


def top_products(db: Session, date_from: datetime | None, date_to: datetime | None, branch_id: int | None, limit: int = 10) -> list[dict[str, object]]:
    validate_report_filters(date_from, date_to)
    statement = select(Product.id, Product.name, func.coalesce(func.sum(SaleItem.quantity), 0), func.coalesce(func.sum(SaleItem.line_total), 0)).join(ProductVariant, SaleItem.product_variant_id == ProductVariant.id).join(Product, ProductVariant.product_id == Product.id).join(Sale, SaleItem.sale_id == Sale.id).group_by(Product.id, Product.name).order_by(func.coalesce(func.sum(SaleItem.quantity), 0).desc()).limit(limit)
    return [{"product_id": item[0], "product_name": item[1], "units_sold": item[2], "revenue": item[3]} for item in db.execute(_sale_filters(statement, date_from, date_to, branch_id)).all()]


def low_stock(db: Session, branch_id: int | None, threshold: int = 10) -> list[dict[str, object]]:
    available = Inventory.stock_quantity - Inventory.reserved_quantity
    statement = select(Inventory, Branch, Product, ProductVariant).join(Branch, Inventory.branch_id == Branch.id).join(ProductVariant, Inventory.product_variant_id == ProductVariant.id).join(Product, ProductVariant.product_id == Product.id).where(available <= threshold).order_by(available.asc(), Product.name).limit(50)
    if branch_id is not None:
        statement = statement.where(Inventory.branch_id == branch_id)
    return [{"inventory_id": inventory.id, "branch_id": branch.id, "branch_name": branch.name, "product_id": product.id, "product_name": product.name, "sku": variant.sku, "available_quantity": inventory.stock_quantity - inventory.reserved_quantity} for inventory, branch, product, variant in db.execute(statement).all()]


def reservations_summary(db: Session, branch_id: int | None) -> list[dict[str, object]]:
    statement = select(Reservation.status, func.count(Reservation.id)).group_by(Reservation.status).order_by(Reservation.status)
    if branch_id is not None:
        statement = statement.where(Reservation.branch_id == branch_id)
    return [{"status": item[0], "count": item[1]} for item in db.execute(statement).all()]


def sales_by_channel(db: Session, date_from: datetime | None, date_to: datetime | None, branch_id: int | None) -> list[dict[str, object]]:
    validate_report_filters(date_from, date_to)
    statement = select(Sale.channel, func.count(Sale.id), func.coalesce(func.sum(Sale.total), 0)).group_by(Sale.channel).order_by(Sale.channel)
    return [{"channel": item[0], "sales_count": item[1], "total": item[2]} for item in db.execute(_sale_filters(statement, date_from, date_to, branch_id)).all()]


def dashboard(db: Session, date_from: datetime | None, date_to: datetime | None, branch_id: int | None) -> dict[str, object]:
    validate_report_filters(date_from, date_to)
    return {
        "revenue": revenue_summary(db, date_from, date_to, branch_id),
        "sales_by_branch": sales_by_branch(db, date_from, date_to, branch_id),
        "top_products": top_products(db, date_from, date_to, branch_id),
        "low_stock": low_stock(db, branch_id),
        "reservations": reservations_summary(db, branch_id),
        "sales_by_channel": sales_by_channel(db, date_from, date_to, branch_id),
    }


def report_snapshot(db: Session, date_from: datetime | None, date_to: datetime | None, branch_id: int | None) -> ReportSnapshot:
    payload = dashboard(db, date_from, date_to, branch_id)
    snapshot = ReportSnapshot(filters=ReportFilters(date_from=date_from, date_to=date_to, branch_id=branch_id), **payload)
    if snapshot.revenue.sales_count == 0 and not snapshot.low_stock and not snapshot.reservations:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REPORT_DATA_NOT_FOUND", "message": "No report data is available for the selected filters."},
        )
    return snapshot


def assistant_report(db: Session, request: ReportAssistantRequest) -> ReportAssistantResponse:
    explicit_filters = ReportFilters(date_from=request.date_from, date_to=request.date_to, branch_id=request.branch_id)
    validate_report_filters(explicit_filters.date_from, explicit_filters.date_to)
    intent, provider, intent_fallback = ai_service.interpret_intent(request.prompt, explicit_filters)
    filters = intent.filters
    validate_report_filters(filters.date_from, filters.date_to)

    if intent.kind == "top_products":
        data = top_products(db, filters.date_from, filters.date_to, filters.branch_id)
    elif intent.kind == "sales_by_branch":
        data = sales_by_branch(db, filters.date_from, filters.date_to, filters.branch_id)
    elif intent.kind == "inventory":
        data = low_stock(db, filters.branch_id)
    elif intent.kind == "reservations":
        data = reservations_summary(db, filters.branch_id)
    else:
        data = dashboard(db, filters.date_from, filters.date_to, filters.branch_id)

    narrative, narrative_fallback = ai_service.build_narrative(intent, data, provider, prompt=request.prompt)
    return ReportAssistantResponse(
        intent=intent,
        filters=filters,
        data=data,
        narrative=narrative,
        provider=provider,
        fallback_used=intent_fallback or narrative_fallback,
    )
