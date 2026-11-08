import os
from datetime import UTC, datetime
from types import SimpleNamespace
from decimal import Decimal

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["OPENAI_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import get_db  # noqa: E402
from app.core.models import Base, Branch, Category, City, Color, Inventory, Permission, Product, ProductVariant, Role, RolePermission, Sale, SaleItem, Season, Size, Tenant, User  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.reports import ai_service  # noqa: E402

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)


def override_get_db():
    with Session(engine) as session:
        yield session


client = TestClient(app)
_previous_get_db_override = None


def setup_function() -> None:
    global _previous_get_db_override
    _previous_get_db_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    with Session(engine) as db:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        admin_role = Role(code="ADMIN", name="Administrador")
        seller_role = Role(code="SELLER", name="Vendedor")
        reports_role = Role(code="REPORTS", name="Reportes")
        reports_permission = Permission(code="reports.read", name="Consultar reportes")
        db.add_all([admin_role, seller_role, reports_role, reports_permission])
        db.flush()
        db.add(RolePermission(role_id=reports_role.id, permission_id=reports_permission.id))
        db.add_all(
            [
                User(role=admin_role, first_name="Admin", last_name="Reports", email="admin-reports@example.com", phone="70000090", password_hash=hash_password("Admin123!")),
                User(role=seller_role, first_name="Seller", last_name="Reports", email="seller-reports@example.com", phone="70000091", password_hash=hash_password("Seller123!")),
                User(role=reports_role, first_name="Reader", last_name="Reports", email="reader-reports@example.com", phone="70000092", password_hash=hash_password("Reader123!")),
            ]
        )
        db.commit()


def teardown_function() -> None:
    ai_service.settings.openai_api_key = None
    if _previous_get_db_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = _previous_get_db_override


def _headers(email: str = "admin-reports@example.com", password: str = "Admin123!") -> dict[str, str]:
    tokens = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _seed_report_data() -> None:
    with Session(engine) as db:
        category = Category(name="Assistant Category")
        size = Size(name="Assistant M")
        color = Color(name="Assistant Blue", hex_code="#0000FF")
        season = Season(name="Assistant Season")
        city = City(name="La Paz")
        db.add_all([category, size, color, season, city])
        db.flush()
        branch = Branch(city_id=city.id, name="Sucursal Central", address="Av. Principal 123", phone="70000000")
        shirt = Product(category_id=category.id, season_id=season.id, code="AST-001", name="Camisa Urbana", slug="camisa-urbana", price=Decimal("150.00"))
        jacket = Product(category_id=category.id, season_id=season.id, code="AST-002", name="Chaqueta Denim", slug="chaqueta-denim", price=Decimal("300.00"))
        db.add_all([branch, shirt, jacket])
        db.flush()
        shirt_variant = ProductVariant(product_id=shirt.id, size_id=size.id, color_id=color.id, sku="AST-001-M-BLUE")
        jacket_variant = ProductVariant(product_id=jacket.id, size_id=size.id, color_id=color.id, sku="AST-002-M-BLUE")
        db.add_all([shirt_variant, jacket_variant])
        db.flush()
        db.add_all(
            [
                Inventory(branch_id=branch.id, product_variant_id=shirt_variant.id, stock_quantity=5, reserved_quantity=1),
                Inventory(branch_id=branch.id, product_variant_id=jacket_variant.id, stock_quantity=20, reserved_quantity=0),
            ]
        )
        sale = Sale(
            order_number="AST-0001",
            branch_id=branch.id,
            channel="PHYSICAL",
            status="CONFIRMED",
            subtotal=Decimal("900.00"),
            discount=Decimal("0.00"),
            total=Decimal("900.00"),
            created_at=datetime(2024, 5, 20, 12, 0, tzinfo=UTC),
        )
        db.add(sale)
        db.flush()
        db.add_all(
            [
                SaleItem(sale_id=sale.id, product_variant_id=shirt_variant.id, quantity=4, unit_price=Decimal("150.00"), discount=Decimal("0.00"), line_total=Decimal("600.00")),
                SaleItem(sale_id=sale.id, product_variant_id=jacket_variant.id, quantity=1, unit_price=Decimal("300.00"), discount=Decimal("0.00"), line_total=Decimal("300.00")),
            ]
        )
        db.commit()


def test_assistant_local_top_products_uses_grounded_report_data() -> None:
    ai_service.settings.openai_api_key = None
    _seed_report_data()

    response = client.post("/api/v1/reports/assistant", headers=_headers(), json={"prompt": "Mostrame los productos más vendidos de mayo"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "local"
    assert body["fallback_used"] is True
    assert body["intent"]["kind"] == "top_products"
    assert body["data"][0]["product_name"] == "Camisa Urbana"
    assert body["data"][0]["units_sold"] == 4
    assert "Camisa Urbana" in body["narrative"]


def test_assistant_falls_back_when_openai_response_is_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    ai_service.settings.openai_api_key = "test-key"
    _seed_report_data()

    def invalid_provider(_: dict[str, object]) -> dict[str, object]:
        return {"output_text": "no es json"}

    monkeypatch.setattr(ai_service, "_post_openai", invalid_provider)

    response = client.post("/api/v1/reports/assistant", headers=_headers(), json={"prompt": "Necesito revisar el inventario bajo"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "local"
    assert body["fallback_used"] is True
    assert body["intent"]["kind"] == "inventory"
    assert body["data"][0]["product_name"] == "Camisa Urbana"


def test_assistant_requires_reports_read_permission() -> None:
    unauthenticated = client.post("/api/v1/reports/assistant", json={"prompt": "Resumen del dashboard"})
    forbidden = client.post("/api/v1/reports/assistant", headers=_headers("seller-reports@example.com", "Seller123!"), json={"prompt": "Resumen del dashboard"})

    assert unauthenticated.status_code == 401
    assert forbidden.status_code == 403


def test_assistant_uses_mocked_openai_intent_without_trusting_model_numbers(monkeypatch: pytest.MonkeyPatch) -> None:
    ai_service.settings.openai_api_key = "test-key"
    _seed_report_data()
    calls = {"count": 0}

    def mocked_provider(_: dict[str, object]) -> dict[str, object]:
        calls["count"] += 1
        if calls["count"] == 1:
            return {"output_text": '{"kind":"sales_by_branch","filters":{"date_from":null,"date_to":null,"branch_id":null},"reasoning":"Pedido por sucursal."}'}
        return {"output_text": "La sucursal central concentra las ventas confirmadas según los datos suministrados."}

    monkeypatch.setattr(ai_service, "_post_openai", mocked_provider)

    response = client.post("/api/v1/reports/assistant", headers=_headers(), json={"prompt": "Dame ventas por sucursal"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "openai"
    assert body["fallback_used"] is False
    assert body["intent"]["kind"] == "sales_by_branch"
    assert body["data"][0]["branch_name"] == "Sucursal Central"
    assert body["data"][0]["total"] == "900.00"
    assert calls["count"] == 2


@pytest.mark.parametrize(
    ("format_name", "media_type", "filename"),
    [("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "assistant.xlsx"), ("pdf", "application/pdf", "assistant.pdf")],
)
def test_assistant_export_posts_typed_request_and_returns_binary(monkeypatch: pytest.MonkeyPatch, format_name: str, media_type: str, filename: str) -> None:
    captured: dict[str, object] = {}

    def fake_assistant_report(_: object, request: object) -> object:
        captured["request"] = request
        return SimpleNamespace(
            intent=SimpleNamespace(kind="top_products"),
            data=[{"product_name": "Camisa", "units_sold": 3, "revenue": Decimal("450.00")}],
            narrative="Reporte generado",
        )

    def fake_export_dynamic_report(**kwargs: object) -> object:
        captured["export"] = kwargs
        return SimpleNamespace(content=b"binary-report", media_type=media_type, filename=filename)

    monkeypatch.setattr("app.modules.reports.router.service.assistant_report", fake_assistant_report)
    monkeypatch.setattr("app.modules.reports.router.export_service.export_dynamic_report", fake_export_dynamic_report)
    payload = {"prompt": "Productos vendidos", "date_from": "2024-05-01T00:00:00Z", "date_to": "2024-05-31T00:00:00Z", "branch_id": 7}

    response = client.post(f"/api/v1/reports/assistant/export/{format_name}", headers=_headers(), json=payload)

    assert response.status_code == 200
    assert response.content == b"binary-report"
    assert response.headers["content-type"].startswith(media_type)
    assert response.headers["content-disposition"] == f'attachment; filename="{filename}"'
    request = captured["request"]
    assert request.prompt == payload["prompt"]
    assert request.branch_id == payload["branch_id"]
    assert request.date_from.isoformat().startswith("2024-05-01T00:00:00")
    assert captured["export"]["format_name"] == format_name


@pytest.mark.parametrize(
    ("intent_kind", "data", "expected_values"),
    [
        ("revenue_by_category", [{"category_name": "Vestidos", "sales_count": 2, "units_sold": 3, "total_revenue": "450.00", "percentage": 75}], ["Vestidos", "450.00"]),
        ("top_products", [{"product_name": "Camisa", "units_sold": 3, "revenue": "450.00"}], ["Camisa", "450.00"]),
        ("sales_by_branch", [{"branch_name": "Central", "sales_count": 2, "total": "450.00"}], ["Central", "450.00"]),
        ("inventory", [{"branch_name": "Central", "product_name": "Camisa", "sku": "SKU-1", "available_quantity": 4}], ["Camisa", 4]),
        ("reservations", [{"status": "PENDING", "count": 2}], ["PENDING", 2]),
        ("sales_by_channel", [{"channel": "ONLINE", "sales_count": 2, "total": "450.00"}], ["ONLINE", "450.00"]),
        (
            "dashboard",
            {
                "revenue": {"total": "900.00", "sales_count": 3},
                "sales_by_branch": [{"branch_name": "Central", "total": "900.00"}],
                "top_products": [{"product_name": "Camisa", "units_sold": 4}],
                "low_stock": [{"product_name": "Pantalón", "available_quantity": 1}],
                "reservations": [{"status": "PENDING", "count": 2}],
                "sales_by_channel": [{"channel": "ONLINE", "sales_count": 2}],
            },
            ["900.00", "Central", "Camisa", "Pantalón", "PENDING", "ONLINE"],
        ),
        ("otro_resultado", {"clave": "valor real", "total": 7}, ["valor real", 7]),
    ],
)
def test_assistant_export_includes_actual_data_for_every_result_shape(
    monkeypatch: pytest.MonkeyPatch, intent_kind: str, data: object, expected_values: list[object]
) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "app.modules.reports.router.service.assistant_report",
        lambda *_: SimpleNamespace(intent=SimpleNamespace(kind=intent_kind), data=data, narrative="Narrativa"),
    )
    monkeypatch.setattr(
        "app.modules.reports.router.export_service.export_dynamic_report",
        lambda **kwargs: captured.update(export=kwargs) or SimpleNamespace(content=b"ok", media_type="text/plain", filename="out"),
    )

    response = client.post("/api/v1/reports/assistant/export/xlsx", headers=_headers(), json={"prompt": "Consulta"})

    assert response.status_code == 200
    exported = captured["export"]
    rows = exported["rows"]
    flattened = [value for row in rows for value in row]
    for expected in expected_values:
        assert expected in flattened or str(expected) in flattened
    assert rows
    assert any("Consulta" not in row for row in rows)


def test_assistant_export_rejects_unsupported_format() -> None:
    response = client.post("/api/v1/reports/assistant/export/pptx", headers=_headers(), json={"prompt": "Productos vendidos"})

    assert response.status_code == 422


def test_assistant_export_requires_authentication_and_reports_permission() -> None:
    unauthenticated = client.post("/api/v1/reports/assistant/export/xlsx", json={"prompt": "Productos vendidos"})
    forbidden = client.post("/api/v1/reports/assistant/export/xlsx", headers=_headers("seller-reports@example.com", "Seller123!"), json={"prompt": "Productos vendidos"})

    assert unauthenticated.status_code == 401
    assert forbidden.status_code == 403


def test_assistant_export_denies_tenant_feature_before_assistant(monkeypatch: pytest.MonkeyPatch) -> None:
    with Session(engine) as db:
        tenant = Tenant(name="Reports Tenant")
        db.add(tenant)
        db.flush()
        db.query(User).filter(User.email == "admin-reports@example.com").update({"tenant_id": tenant.id})
        db.commit()

    assistant_called = False

    def fail_assistant(_: object, __: object) -> object:
        nonlocal assistant_called
        assistant_called = True
        raise AssertionError("assistant work must not start when the feature is denied")

    monkeypatch.setattr("app.modules.reports.router.check_tenant_feature", lambda *_: False)
    monkeypatch.setattr("app.modules.reports.router.service.assistant_report", fail_assistant)

    response = client.post("/api/v1/reports/assistant/export/xlsx", headers=_headers(), json={"prompt": "Productos vendidos"})

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "FEATURE_NOT_IN_PLAN"
    assert assistant_called is False


def test_assistant_inventory_urgent_replenishment_intent() -> None:
    ai_service.settings.openai_api_key = None
    _seed_report_data()

    query = "¿Cuáles productos tienen bajo stock y requieren reposición urgente?"
    response = client.post("/api/v1/reports/assistant", headers=_headers(), json={"prompt": query})

    assert response.status_code == 200
    body = response.json()
    assert body["intent"]["kind"] == "inventory"
    assert body["provider"] == "local"
    assert len(body["data"]) >= 1
    assert body["data"][0]["product_name"] == "Camisa Urbana"
    assert body["data"][0]["available_quantity"] == 4
    assert "bajo stock" in body["narrative"].lower()
    assert "Camisa Urbana" in body["narrative"]

