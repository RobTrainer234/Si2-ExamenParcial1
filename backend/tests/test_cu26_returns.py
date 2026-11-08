
import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "cu26-test-secret"
os.environ["OPENAI_API_KEY"] = ""

from app.core.database import get_db
from app.core.models import (
    Base,
    Branch,
    CreditNoteRedemption,
    Category,
    City,
    Color,
    Devolucion,
    Inventory,
    InventoryMovement,
    Payment,
    Permission,
    Product,
    ProductVariant,
    Promotion,
    PromotionProduct,
    Role,
    Sale,
    Size,
    Tenant,
    User,
)
from app.core.security import hash_password
from app.main import app
from app.modules.commerce.schemas import CreditNoteSettlementResponse, ReturnLookupResponse, SaleReturnRequest, SaleReturnResponse
from app.modules.commerce.service import _credit_note_payment_idempotency_key


def test_credit_note_payment_keys_are_target_scoped_and_fit_payment_column() -> None:
    first = _credit_note_payment_idempotency_key(tenant_id=7, credit_note_id=11, sale_id=101, request_idempotency_key="same-request")
    second = _credit_note_payment_idempotency_key(tenant_id=7, credit_note_id=11, sale_id=202, request_idempotency_key="same-request")

    assert first != second
    assert len(first) <= Payment.__table__.c.idempotency_key.type.length
    assert len(second) <= Payment.__table__.c.idempotency_key.type.length


def test_return_request_requires_line_quantities_and_idempotency_key() -> None:
    request = SaleReturnRequest(reason="Customer returned item", idempotency_key="return-key-001", beneficiary_customer_id=42, items=[{"sale_item_id": 7, "quantity": 1, "condition": "SELLABLE"}])
    assert request.items[0].quantity == 1
    assert request.items[0].condition == "SELLABLE"


def test_return_request_rejects_duplicate_sale_lines() -> None:
    with pytest.raises(ValidationError):
        SaleReturnRequest(reason="Duplicate lines", idempotency_key="return-key-002", beneficiary_customer_id=42, items=[{"sale_item_id": 7, "quantity": 1, "condition": "SELLABLE"}, {"sale_item_id": 7, "quantity": 1, "condition": "DAMAGED"}])


def test_return_ledger_models_support_credit_note_and_restock_movement() -> None:
    assert hasattr(Devolucion, "beneficiario_id")
    assert hasattr(Devolucion, "idempotency_key")
    constraints = [item for item in Devolucion.__table_args__ if hasattr(item, "columns")]
    assert any(tuple(column.name for column in item.columns) == ("tenant_id", "idempotency_key") for item in constraints)
    movement_constraints = [item for item in InventoryMovement.__table_args__ if hasattr(item, "sqltext")]
    assert any("RESTOCK" in str(item.sqltext) for item in movement_constraints)
    assert Decimal("0.00") == Decimal("0.00")


def test_return_contract_rejects_blank_reason_and_exposes_return_fields() -> None:
    with pytest.raises(ValidationError):
        SaleReturnRequest(reason="   ", idempotency_key="return-key-003")
    assert SaleReturnResponse.model_fields["return_id"].annotation is int
    assert SaleReturnResponse.model_fields["credit_note_amount"].annotation is Decimal
    assert ReturnLookupResponse.model_fields["items"].annotation
    assert ReturnLookupResponse.model_fields["customer_id"].annotation == int | None


def test_return_lookup_uses_returnable_quantity_not_exchange_dto() -> None:
    assert "remaining_returnable_quantity" in ReturnLookupResponse.model_fields["items"].annotation.__args__[0].model_fields


def test_return_lookup_includes_original_customer_id_without_other_pii():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    sale = _cu26_create_confirmed_sale(world, headers, customer_id=world["customer_id"])
    response = CU26_CLIENT.get(f"/api/v1/returns/lookup/{sale['order_number']}", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["customer_id"] == world["customer_id"]
    assert set(response.json()) == {"sale_id", "order_number", "sale_date", "branch_id", "status", "customer_id", "items"}


CU26_ENGINE = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
CU26_CLIENT = TestClient(app)


def _cu26_db():
    with Session(CU26_ENGINE) as db:
        yield db


@pytest.fixture(autouse=True)
def _reset_cu26_database():
    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _cu26_db
    Base.metadata.drop_all(CU26_ENGINE)
    Base.metadata.create_all(CU26_ENGINE)
    yield
    if previous is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous


def _seed_cu26_world(*, customer_tenant: bool = True, cashier_branch: bool = True, discounted: bool = False):
    with Session(CU26_ENGINE) as db:
        role_cashier = Role(code="CASHIER", name="Cashier")
        role_client = Role(code="CLIENT", name="Client")
        permissions = [Permission(code=code, name=code) for code in ("sales.create", "sales.read", "payments.cash")]
        db.add_all([role_cashier, role_client, *permissions])
        db.flush()
        role_cashier.permissions.extend(permissions)
        tenant = Tenant(name="CU26 Tenant Synthetic")
        other_tenant = Tenant(name="CU26 Other Tenant Synthetic")
        city = City(name="CU26 Synthetic City")
        category = Category(name="CU26 Synthetic Category")
        size = Size(name="CU26 Synthetic Size")
        color = Color(name="CU26 Synthetic Color", hex_code="#262626")
        db.add_all([tenant, other_tenant, city, category, size, color])
        db.flush()
        branch = Branch(tenant_id=tenant.id, city_id=city.id, name="CU26 Synthetic Branch", address="Synthetic 26", phone="70000026")
        same_tenant_branch = Branch(tenant_id=tenant.id, city_id=city.id, name="CU26 Same Tenant Branch", address="Synthetic 26B", phone="70000032")
        other_branch = Branch(tenant_id=other_tenant.id, city_id=city.id, name="CU26 Other Branch", address="Synthetic 27", phone="70000027")
        product = Product(tenant_id=tenant.id, category_id=category.id, code="CU26-SYN-P", name="CU26 Synthetic Product", slug="cu26-synthetic-product", price=Decimal("4.00"))
        db.add_all([branch, same_tenant_branch, other_branch, product])
        db.flush()
        variant = ProductVariant(tenant_id=tenant.id, product_id=product.id, size_id=size.id, color_id=color.id, sku="CU26-SYN-SKU")
        db.add(variant)
        db.flush()
        inventory = Inventory(tenant_id=tenant.id, branch_id=branch.id, product_variant_id=variant.id, stock_quantity=10)
        same_tenant_inventory = Inventory(tenant_id=tenant.id, branch_id=same_tenant_branch.id, product_variant_id=variant.id, stock_quantity=10)
        db.add_all([inventory, same_tenant_inventory])
        if discounted:
            promotion = Promotion(tenant_id=tenant.id, name="CU26 Synthetic Discount", discount_type="PERCENT", discount_value=Decimal("16.67"), starts_at=datetime.now(UTC) - timedelta(days=1), ends_at=datetime.now(UTC) + timedelta(days=1))
            db.add(promotion)
            db.flush()
            db.add(PromotionProduct(promotion_id=promotion.id, product_id=product.id))
        customer = User(tenant_id=tenant.id if customer_tenant else other_tenant, role=role_client, first_name="CU26", last_name="Customer", email="cu26.customer.synthetic@cu26mail.com", phone="70000028", password_hash=hash_password("Pass123!"))
        other_customer = User(tenant_id=other_tenant.id, role=role_client, first_name="CU26", last_name="Other", email="cu26.other.synthetic@cu26mail.com", phone="70000029", password_hash=hash_password("Pass123!"))
        cashier = User(tenant_id=tenant.id, role=role_cashier, first_name="CU26", last_name="Cashier", email="cu26.cashier.synthetic@cu26mail.com", phone="70000030", password_hash=hash_password("Pass123!"))
        other_cashier = User(tenant_id=tenant.id, role=role_cashier, first_name="CU26", last_name="OtherCashier", email="cu26.othercashier.synthetic@cu26mail.com", phone="70000031", password_hash=hash_password("Pass123!"))
        if cashier_branch:
            cashier.branches.extend([branch, same_tenant_branch])
        other_cashier.branches.append(other_branch)
        db.add_all([customer, other_customer, cashier, other_cashier])
        db.commit()
        return {"tenant_id": tenant.id, "other_tenant_id": other_tenant.id, "branch_id": branch.id, "same_tenant_branch_id": same_tenant_branch.id, "other_branch_id": other_branch.id, "variant_id": variant.id, "inventory_id": inventory.id, "customer_id": customer.id, "other_customer_id": other_customer.id, "cashier_email": cashier.email, "other_cashier_email": other_cashier.email}


def _cu26_login(email: str):
    response = CU26_CLIENT.post("/api/v1/auth/login", json={"email": email, "password": "Pass123!"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _cu26_create_confirmed_sale(world: dict, headers: dict, *, customer_id: int | None = None, quantity: int = 3):
    sale_response = CU26_CLIENT.post("/api/v1/sales/physical", headers=headers, json={"branch_id": world["branch_id"], "customer_id": customer_id, "items": [{"product_variant_id": world["variant_id"], "quantity": quantity}]})
    assert sale_response.status_code == 201, sale_response.text
    sale = sale_response.json()
    payment_response = CU26_CLIENT.post(f"/api/v1/sales/{sale['id']}/cash-payment", headers=headers, json={"method": "CASH", "amount": sale["total"]})
    assert payment_response.status_code == 200, payment_response.text
    return sale


def _cu26_create_credit_note(world: dict, headers: dict, *, quantity: int = 1):
    original = _cu26_create_confirmed_sale(world, headers, customer_id=world["customer_id"], quantity=quantity)
    returned = CU26_CLIENT.post(
        f"/api/v1/sales/{original['id']}/return",
        headers=headers,
        json={"reason": "CU26 lookup", "idempotency_key": f"cu26-lookup-return-{quantity}", "items": [{"sale_item_id": original["items"][0]["id"], "quantity": quantity, "condition": "SELLABLE"}]},
    )
    assert returned.status_code == 200, returned.text
    return returned.json()["credit_note_code"]


def test_credit_note_lookup_returns_current_balance_without_mutation():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    code = _cu26_create_credit_note(world, headers, quantity=2)
    with Session(CU26_ENGINE) as db:
        before_notes = db.query(Devolucion).count()
        before_redemptions = db.query(CreditNoteRedemption).count()
    response = CU26_CLIENT.post("/api/v1/credit-notes/lookup", headers=headers, json={"credit_note_code": code, "customer_id": world["customer_id"], "branch_id": world["branch_id"]})
    assert response.status_code == 200, response.text
    assert response.json() == {"available_balance": "8.00", "customer_id": world["customer_id"], "expires_at": None}
    with Session(CU26_ENGINE) as db:
        assert db.query(Devolucion).count() == before_notes
        assert db.query(CreditNoteRedemption).count() == before_redemptions


def test_credit_note_lookup_hides_wrong_unknown_and_foreign_codes_with_same_failure():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    code = _cu26_create_credit_note(world, headers)
    with Session(CU26_ENGINE) as db:
        db.add(Devolucion(tenant_id=world["other_tenant_id"], sucursal_id=world["other_branch_id"], venta_id=1, cajero_id=1, numero_devolucion="DEV-CU26-FOREIGN", total_devuelto=Decimal("4.00"), saldo_nota_credito=Decimal("4.00"), tipo_reembolso="NOTA_CREDITO", codigo_nota_credito="NC-FOREIGN-CU26", beneficiario_id=world["other_customer_id"], idempotency_key="cu26-foreign-note", motivo="CU26 foreign", estado="COMPLETADA"))
        db.commit()
    cases = [
        {"credit_note_code": code, "customer_id": world["other_customer_id"], "branch_id": world["branch_id"]},
        {"credit_note_code": "NC-UNKNOWN-CU26", "customer_id": world["customer_id"], "branch_id": world["branch_id"]},
        {"credit_note_code": "NC-FOREIGN-CU26", "customer_id": world["customer_id"], "branch_id": world["branch_id"]},
    ]
    responses = [CU26_CLIENT.post("/api/v1/credit-notes/lookup", headers=headers, json=case) for case in cases]
    assert [response.status_code for response in responses] == [400, 400, 400]
    assert responses[0].json()["detail"]["code"] == "INVALID_CREDIT_NOTE_LOOKUP"
    assert responses[1].json()["detail"] == responses[0].json()["detail"]
    assert responses[2].json()["detail"] == responses[0].json()["detail"]
    denied = CU26_CLIENT.post("/api/v1/credit-notes/lookup", headers=headers, json={"credit_note_code": code, "customer_id": world["customer_id"], "branch_id": world["other_branch_id"]})
    assert denied.status_code in {403, 404}


def test_credit_note_lookup_rejects_exhausted_note_with_stable_conflict():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    code = _cu26_create_credit_note(world, headers)
    target = CU26_CLIENT.post("/api/v1/sales/physical", headers=headers, json={"branch_id": world["branch_id"], "customer_id": world["customer_id"], "items": [{"product_variant_id": world["variant_id"], "quantity": 1}]})
    settled = CU26_CLIENT.post(f"/api/v1/sales/{target.json()['id']}/credit-note-settlement", headers=headers, json={"credit_note_code": code, "idempotency_key": "cu26-lookup-exhaust-settle"})
    assert settled.status_code == 200, settled.text
    response = CU26_CLIENT.post("/api/v1/credit-notes/lookup", headers=headers, json={"credit_note_code": code, "customer_id": world["customer_id"], "branch_id": world["branch_id"]})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "EXHAUSTED_CREDIT_NOTE"


def test_credit_note_lookup_allows_same_tenant_cross_branch():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    code = _cu26_create_credit_note(world, headers)
    response = CU26_CLIENT.post("/api/v1/credit-notes/lookup", headers=headers, json={"credit_note_code": code, "customer_id": world["customer_id"], "branch_id": world["same_tenant_branch_id"]})
    assert response.status_code == 200, response.text
    assert response.json()["customer_id"] == world["customer_id"]


def test_credit_note_lookup_requires_typed_request_fields():
    with pytest.raises(ValidationError):
        from app.modules.commerce.schemas import CreditNoteLookupRequest

        CreditNoteLookupRequest(credit_note_code="NC-1", customer_id=1)


def test_credit_note_settlement_applies_note_and_confirms_target_sale():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    original = _cu26_create_confirmed_sale(world, headers, customer_id=world["customer_id"], quantity=3)
    returned = CU26_CLIENT.post(
        f"/api/v1/sales/{original['id']}/return",
        headers=headers,
        json={"reason": "CU26 credit note", "idempotency_key": "cu26-credit-return-001", "items": [{"sale_item_id": original["items"][0]["id"], "quantity": 3, "condition": "SELLABLE"}]},
    )
    assert returned.status_code == 200, returned.text
    target = CU26_CLIENT.post(
        "/api/v1/sales/physical",
        headers=headers,
        json={"branch_id": world["branch_id"], "customer_id": world["customer_id"], "items": [{"product_variant_id": world["variant_id"], "quantity": 1}]},
    )
    assert target.status_code == 201, target.text
    response = CU26_CLIENT.post(
        f"/api/v1/sales/{target.json()['id']}/credit-note-settlement",
        headers=headers,
        json={"credit_note_code": returned.json()["credit_note_code"], "idempotency_key": "cu26-credit-settle-001"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "CONFIRMED"
    assert len(response.json()["payments"]) == 1
    assert response.json()["payments"][0]["method"] == "CREDIT_NOTE"
    assert response.json()["payments"][0]["amount"] == "4.00"


def test_credit_note_settlement_collects_exact_cash_remainder_and_is_retry_safe():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    original = _cu26_create_confirmed_sale(world, headers, customer_id=world["customer_id"], quantity=1)
    returned = CU26_CLIENT.post(f"/api/v1/sales/{original['id']}/return", headers=headers, json={"reason": "CU26 partial note", "idempotency_key": "cu26-credit-return-002", "items": [{"sale_item_id": original["items"][0]["id"], "quantity": 1, "condition": "SELLABLE"}]})
    assert returned.status_code == 200, returned.text
    target = CU26_CLIENT.post("/api/v1/sales/physical", headers=headers, json={"branch_id": world["branch_id"], "customer_id": world["customer_id"], "items": [{"product_variant_id": world["variant_id"], "quantity": 3}]})
    settlement = {"credit_note_code": returned.json()["credit_note_code"], "idempotency_key": "cu26-credit-settle-002", "method": "CASH", "amount": "10.00"}
    response = CU26_CLIENT.post(f"/api/v1/sales/{target.json()['id']}/credit-note-settlement", headers=headers, json=settlement)
    assert response.status_code == 200, response.text
    replay = CU26_CLIENT.post(f"/api/v1/sales/{target.json()['id']}/credit-note-settlement", headers=headers, json=settlement)
    assert replay.status_code == 200, replay.text
    assert [payment["method"] for payment in response.json()["payments"]] == ["CREDIT_NOTE", "CASH"]
    assert [payment["amount"] for payment in response.json()["payments"]] == ["4.00", "8.00"]
    assert response.json()["payments"][1]["change_amount"] == "2.00"
    assert response.json()["redemption_id"] > 0
    assert response.json()["applied_amount"] == "4.00"
    assert response.json()["post_redemption_balance"] == "0.00"
    assert response.json()["cash_change"] == "2.00"
    with Session(CU26_ENGINE) as db:
        assert db.query(CreditNoteRedemption).count() == 1
        assert db.query(Payment).filter(Payment.sale_id == target.json()["id"]).count() == 2
        assert db.get(Inventory, world["inventory_id"]).stock_quantity == 7


def test_credit_note_settlement_response_exposes_redemption_contract():
    fields = CreditNoteSettlementResponse.model_fields
    assert fields["redemption_id"].annotation is int
    assert fields["applied_amount"].annotation is Decimal
    assert fields["post_redemption_balance"].annotation is Decimal
    assert fields["cash_change"].annotation is Decimal


def test_credit_note_settlement_rejects_insufficient_cash_without_side_effects():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    original = _cu26_create_confirmed_sale(world, headers, customer_id=world["customer_id"], quantity=1)
    returned = CU26_CLIENT.post(f"/api/v1/sales/{original['id']}/return", headers=headers, json={"reason": "CU26 insufficient cash", "idempotency_key": "cu26-insufficient-return", "items": [{"sale_item_id": original["items"][0]["id"], "quantity": 1}]})
    target = CU26_CLIENT.post("/api/v1/sales/physical", headers=headers, json={"branch_id": world["branch_id"], "customer_id": world["customer_id"], "items": [{"product_variant_id": world["variant_id"], "quantity": 3}]})
    response = CU26_CLIENT.post(f"/api/v1/sales/{target.json()['id']}/credit-note-settlement", headers=headers, json={"credit_note_code": returned.json()["credit_note_code"], "idempotency_key": "cu26-insufficient-settle", "method": "CASH", "amount": "1.00"})
    assert response.status_code == 400
    with Session(CU26_ENGINE) as db:
        assert db.scalar(select(Sale).where(Sale.id == target.json()["id"])).status == "PENDING"
        assert db.query(CreditNoteRedemption).count() == 0
        assert db.query(Payment).filter(Payment.sale_id == target.json()["id"]).count() == 0


def test_credit_note_settlement_rejects_unexpected_tender_when_note_covers_total():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    original = _cu26_create_confirmed_sale(world, headers, customer_id=world["customer_id"], quantity=3)
    returned = CU26_CLIENT.post(f"/api/v1/sales/{original['id']}/return", headers=headers, json={"reason": "CU26 full note", "idempotency_key": "cu26-full-return", "items": [{"sale_item_id": original["items"][0]["id"], "quantity": 3}]})
    target = CU26_CLIENT.post("/api/v1/sales/physical", headers=headers, json={"branch_id": world["branch_id"], "customer_id": world["customer_id"], "items": [{"product_variant_id": world["variant_id"], "quantity": 1}]})
    response = CU26_CLIENT.post(f"/api/v1/sales/{target.json()['id']}/credit-note-settlement", headers=headers, json={"credit_note_code": returned.json()["credit_note_code"], "idempotency_key": "cu26-full-settle", "method": "CASH", "amount": "4.00"})
    assert response.status_code == 400
    with Session(CU26_ENGINE) as db:
        assert db.query(CreditNoteRedemption).count() == 0
        assert db.query(Payment).filter(Payment.sale_id == target.json()["id"]).count() == 0


def test_credit_note_settlement_accepts_exact_card_remainder_and_requires_reference():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    original = _cu26_create_confirmed_sale(world, headers, customer_id=world["customer_id"], quantity=1)
    returned = CU26_CLIENT.post(f"/api/v1/sales/{original['id']}/return", headers=headers, json={"reason": "CU26 card remainder", "idempotency_key": "cu26-card-return", "items": [{"sale_item_id": original["items"][0]["id"], "quantity": 1}]})
    target = CU26_CLIENT.post("/api/v1/sales/physical", headers=headers, json={"branch_id": world["branch_id"], "customer_id": world["customer_id"], "items": [{"product_variant_id": world["variant_id"], "quantity": 3}]})
    missing_reference = CU26_CLIENT.post(f"/api/v1/sales/{target.json()['id']}/credit-note-settlement", headers=headers, json={"credit_note_code": returned.json()["credit_note_code"], "idempotency_key": "cu26-card-missing", "method": "CARD", "amount": "8.00"})
    assert missing_reference.status_code == 400
    exact = CU26_CLIENT.post(f"/api/v1/sales/{target.json()['id']}/credit-note-settlement", headers=headers, json={"credit_note_code": returned.json()["credit_note_code"], "idempotency_key": "cu26-card-exact", "method": "CARD", "amount": "8.00", "transaction_reference": "card-cu26-001"})
    assert exact.status_code == 200, exact.text
    assert exact.json()["payments"][-1]["amount"] == "8.00"


def test_credit_note_settlement_same_key_on_different_sale_conflicts_without_mutation():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    original = _cu26_create_confirmed_sale(world, headers, customer_id=world["customer_id"], quantity=1)
    returned = CU26_CLIENT.post(f"/api/v1/sales/{original['id']}/return", headers=headers, json={"reason": "CU26 conflict note", "idempotency_key": "cu26-conflict-return", "items": [{"sale_item_id": original["items"][0]["id"], "quantity": 1}]})
    first = CU26_CLIENT.post("/api/v1/sales/physical", headers=headers, json={"branch_id": world["branch_id"], "customer_id": world["customer_id"], "items": [{"product_variant_id": world["variant_id"], "quantity": 3}]})
    second = CU26_CLIENT.post("/api/v1/sales/physical", headers=headers, json={"branch_id": world["branch_id"], "customer_id": world["customer_id"], "items": [{"product_variant_id": world["variant_id"], "quantity": 3}]})
    key = "cu26-cross-sale-key"
    first_response = CU26_CLIENT.post(f"/api/v1/sales/{first.json()['id']}/credit-note-settlement", headers=headers, json={"credit_note_code": returned.json()["credit_note_code"], "idempotency_key": key, "method": "CASH", "amount": "10.00"})
    second_response = CU26_CLIENT.post(f"/api/v1/sales/{second.json()['id']}/credit-note-settlement", headers=headers, json={"credit_note_code": returned.json()["credit_note_code"], "idempotency_key": key, "method": "CASH", "amount": "10.00"})
    assert first_response.status_code == 200
    assert second_response.status_code == 409
    with Session(CU26_ENGINE) as db:
        assert db.query(CreditNoteRedemption).count() == 1
        assert db.scalar(select(Sale).where(Sale.id == second.json()["id"])).status == "PENDING"


def test_credit_note_settlement_allows_authorized_same_tenant_cross_branch_redemption():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    original = _cu26_create_confirmed_sale(world, headers, customer_id=world["customer_id"], quantity=1)
    returned = CU26_CLIENT.post(f"/api/v1/sales/{original['id']}/return", headers=headers, json={"reason": "CU26 cross branch", "idempotency_key": "cu26-cross-branch-return", "items": [{"sale_item_id": original["items"][0]["id"], "quantity": 1}]})
    target = CU26_CLIENT.post("/api/v1/sales/physical", headers=headers, json={"branch_id": world["same_tenant_branch_id"], "customer_id": world["customer_id"], "items": [{"product_variant_id": world["variant_id"], "quantity": 1}]})
    assert target.status_code == 201, target.text
    response = CU26_CLIENT.post(f"/api/v1/sales/{target.json()['id']}/credit-note-settlement", headers=headers, json={"credit_note_code": returned.json()["credit_note_code"], "idempotency_key": "cu26-cross-branch-settle"})
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "CONFIRMED"


def test_credit_note_settlement_rejects_unknown_original_and_exhausted_notes():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    original = _cu26_create_confirmed_sale(world, headers, customer_id=world["customer_id"], quantity=1)
    returned = CU26_CLIENT.post(f"/api/v1/sales/{original['id']}/return", headers=headers, json={"reason": "CU26 validation matrix", "idempotency_key": "cu26-validation-return", "items": [{"sale_item_id": original["items"][0]["id"], "quantity": 1}]})
    target = CU26_CLIENT.post("/api/v1/sales/physical", headers=headers, json={"branch_id": world["branch_id"], "customer_id": world["customer_id"], "items": [{"product_variant_id": world["variant_id"], "quantity": 1}]})
    unknown = CU26_CLIENT.post(f"/api/v1/sales/{target.json()['id']}/credit-note-settlement", headers=headers, json={"credit_note_code": "NC-UNKNOWN-CU26", "idempotency_key": "cu26-unknown-note"})
    assert unknown.status_code == 400
    same_sale = CU26_CLIENT.post(f"/api/v1/sales/{original['id']}/credit-note-settlement", headers=headers, json={"credit_note_code": returned.json()["credit_note_code"], "idempotency_key": "cu26-original-note"})
    assert same_sale.status_code == 409
    settled = CU26_CLIENT.post(f"/api/v1/sales/{target.json()['id']}/credit-note-settlement", headers=headers, json={"credit_note_code": returned.json()["credit_note_code"], "idempotency_key": "cu26-exhaust-note"})
    assert settled.status_code == 200
    another = CU26_CLIENT.post("/api/v1/sales/physical", headers=headers, json={"branch_id": world["branch_id"], "customer_id": world["customer_id"], "items": [{"product_variant_id": world["variant_id"], "quantity": 1}]})
    exhausted = CU26_CLIENT.post(f"/api/v1/sales/{another.json()['id']}/credit-note-settlement", headers=headers, json={"credit_note_code": returned.json()["credit_note_code"], "idempotency_key": "cu26-exhausted-note"})
    assert exhausted.status_code == 409


def test_credit_note_redemption_model_has_no_expiry_and_tenant_code_constraint():
    assert not hasattr(Devolucion, "expires_at")
    constraints = [item for item in Devolucion.__table_args__ if hasattr(item, "columns")]
    assert any(tuple(column.name for column in item.columns) == ("tenant_id", "codigo_nota_credito") for item in constraints)


def test_return_credit_notes_conserve_discounted_line_cents_exactly():
    world = _seed_cu26_world(discounted=True)
    headers = _cu26_login(world["cashier_email"])
    sale = _cu26_create_confirmed_sale(world, headers, customer_id=world["customer_id"])
    sale_item_id = sale["items"][0]["id"]
    amounts = []
    for index in range(3):
        response = CU26_CLIENT.post(f"/api/v1/sales/{sale['id']}/return", headers=headers, json={"reason": "  CU26 cents check  ", "idempotency_key": f"cu26-cents-{index:03d}", "items": [{"sale_item_id": sale_item_id, "quantity": 1, "condition": "SELLABLE"}]})
        assert response.status_code == 200, response.text
        amounts.append(Decimal(response.json()["credit_note_amount"]))
    assert amounts == [Decimal("3.33"), Decimal("3.33"), Decimal("3.34")]
    assert sum(amounts) == Decimal("10.00")
    with Session(CU26_ENGINE) as db:
        ledgers = db.scalars(select(Devolucion).order_by(Devolucion.id)).all()
        assert [ledger.motivo for ledger in ledgers] == ["CU26 cents check"] * 3


def test_damaged_return_records_return_without_available_stock_or_restock():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    sale = _cu26_create_confirmed_sale(world, headers, customer_id=world["customer_id"], quantity=1)
    response = CU26_CLIENT.post(f"/api/v1/sales/{sale['id']}/return", headers=headers, json={"reason": "  CU26 damaged intake  ", "idempotency_key": "cu26-damaged-001", "items": [{"sale_item_id": sale["items"][0]["id"], "quantity": 1, "condition": "DAMAGED"}]})
    assert response.status_code == 200, response.text
    with Session(CU26_ENGINE) as db:
        inventory = db.get(Inventory, world["inventory_id"])
        movements = db.scalars(select(InventoryMovement).where(InventoryMovement.reference_type == "sale_return")).all()
        assert inventory.stock_quantity == 10 - 1
        assert [movement.movement_type for movement in movements] == ["RETURN"]
        assert movements[0].stock_before == movements[0].stock_after == 9
        assert movements[0].reason == "Ingreso para inspección: CU26 damaged intake"
        assert db.scalar(select(Devolucion).where(Devolucion.id == response.json()["return_id"])).motivo == "CU26 damaged intake"


def test_identical_return_replay_returns_complete_receipt_without_duplicate_ledger_or_movements():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    sale = _cu26_create_confirmed_sale(world, headers, customer_id=world["customer_id"], quantity=1)
    request = {"reason": "CU26 replay receipt", "idempotency_key": "cu26-replay-receipt", "items": [{"sale_item_id": sale["items"][0]["id"], "quantity": 1, "condition": "SELLABLE"}]}
    first = CU26_CLIENT.post(f"/api/v1/sales/{sale['id']}/return", headers=headers, json=request)
    assert first.status_code == 200, first.text
    with Session(CU26_ENGINE) as db:
        ledger_count = db.query(Devolucion).count()
        movement_count = db.query(InventoryMovement).filter(InventoryMovement.reference_type == "sale_return").count()
    replay = CU26_CLIENT.post(f"/api/v1/sales/{sale['id']}/return", headers=headers, json=request)
    assert replay.status_code == 200, replay.text
    for response in (first, replay):
        assert {"return_id", "credit_note_code", "credit_note_amount"}.issubset(response.json())
    assert replay.json()["return_id"] == first.json()["return_id"]
    assert replay.json()["credit_note_code"] == first.json()["credit_note_code"]
    with Session(CU26_ENGINE) as db:
        assert db.query(Devolucion).count() == ledger_count == 1
        assert db.query(InventoryMovement).filter(InventoryMovement.reference_type == "sale_return").count() == movement_count


def test_return_beneficiary_is_required_same_tenant_and_matches_existing_customer():
    world = _seed_cu26_world()
    headers = _cu26_login(world["cashier_email"])
    anonymous_sale = _cu26_create_confirmed_sale(world, headers)
    missing = CU26_CLIENT.post(f"/api/v1/sales/{anonymous_sale['id']}/return", headers=headers, json={"reason": "CU26 anonymous", "idempotency_key": "cu26-anon-001", "items": [{"sale_item_id": anonymous_sale["items"][0]["id"], "quantity": 1}]})
    assert missing.status_code == 400
    foreign = CU26_CLIENT.post(f"/api/v1/sales/{anonymous_sale['id']}/return", headers=headers, json={"reason": "CU26 foreign", "beneficiary_customer_id": world["other_customer_id"], "idempotency_key": "cu26-anon-002", "items": [{"sale_item_id": anonymous_sale["items"][0]["id"], "quantity": 1}]})
    assert foreign.status_code == 400
    accepted = CU26_CLIENT.post(f"/api/v1/sales/{anonymous_sale['id']}/return", headers=headers, json={"reason": "CU26 same tenant", "beneficiary_customer_id": world["customer_id"], "idempotency_key": "cu26-anon-003", "items": [{"sale_item_id": anonymous_sale["items"][0]["id"], "quantity": 1}]})
    assert accepted.status_code == 200, accepted.text
    existing_sale = _cu26_create_confirmed_sale(world, headers, customer_id=world["customer_id"])
    mismatch = CU26_CLIENT.post(f"/api/v1/sales/{existing_sale['id']}/return", headers=headers, json={"reason": "CU26 mismatch", "beneficiary_customer_id": world["other_customer_id"], "idempotency_key": "cu26-existing-001", "items": [{"sale_item_id": existing_sale["items"][0]["id"], "quantity": 1}]})
    assert mismatch.status_code == 400


def test_return_customer_lookup_is_active_and_same_tenant_only():
    world = _seed_cu26_world()
    with Session(CU26_ENGINE) as db:
        inactive = db.get(User, world["customer_id"])
        inactive.is_active = False
        db.commit()
    headers = _cu26_login(world["cashier_email"])
    response = CU26_CLIENT.get("/api/v1/returns/customers?q=CU26", headers=headers)
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert world["customer_id"] not in ids
    assert world["other_customer_id"] not in ids


def test_cashier_from_another_branch_cannot_lookup_or_process_return():
    world = _seed_cu26_world()
    owner_headers = _cu26_login(world["cashier_email"])
    sale = _cu26_create_confirmed_sale(world, owner_headers, customer_id=world["customer_id"])
    other_headers = _cu26_login(world["other_cashier_email"])
    lookup = CU26_CLIENT.get(f"/api/v1/returns/lookup/{sale['order_number']}", headers=other_headers)
    process = CU26_CLIENT.post(f"/api/v1/sales/{sale['id']}/return", headers=other_headers, json={"reason": "CU26 branch guard", "idempotency_key": "cu26-branch-001", "items": [{"sale_item_id": sale["items"][0]["id"], "quantity": 1}]})
    assert lookup.status_code in {403, 404}
    assert process.status_code in {403, 404}
    with Session(CU26_ENGINE) as db:
        assert db.scalar(select(Devolucion).where(Devolucion.idempotency_key == "cu26-branch-001")) is None
        assert db.scalar(select(InventoryMovement).where(InventoryMovement.reference_type == "sale_return")) is None
