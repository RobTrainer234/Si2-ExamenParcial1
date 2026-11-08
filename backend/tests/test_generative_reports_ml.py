from datetime import datetime, timedelta, timezone
from decimal import Decimal
import io
import zipfile

import pytest
from openpyxl import load_workbook
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

try:
    from app.core.database import get_db
    from app.core.models import (
        Base,
        Branch,
        Category,
        City,
        Color,
        Product,
        ProductVariant,
        Role,
        Sale,
        SaleItem,
        Size,
        Subscription,
        SubscriptionPlan,
        Tenant,
        User,
    )
    from app.core.security import hash_password
    from app.main import app
    from app.modules.reports import ai_service, export_service, ml_service, router as reports_router
    from app.modules.reports.schemas import ReportAssistantIntent, ReportAssistantRequest, ReportFilters
except ModuleNotFoundError:
    from backend.app.core.database import get_db
    from backend.app.core.models import (
        Base,
        Branch,
        Category,
        City,
        Color,
        Product,
        ProductVariant,
        Role,
        Sale,
        SaleItem,
        Size,
        Subscription,
        SubscriptionPlan,
        Tenant,
        User,
    )
    from backend.app.core.security import hash_password
    from backend.app.main import app
    from backend.app.modules.reports import ai_service, export_service, ml_service, router as reports_router
    from backend.app.modules.reports.schemas import ReportAssistantIntent, ReportAssistantRequest, ReportFilters


def test_cu15_2_gemini_extra_fields_fall_back_to_local(monkeypatch: pytest.MonkeyPatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": (
                                        '{"kind":"inventory","filters":{"date_from":null,"date_to":null,'
                                        '"branch_id":null,"tenant_id":42},"reasoning":"safe",'
                                        '"sql":"SELECT * FROM tenants"}'
                                    )
                                }
                            ]
                        }
                    }
                ]
            }

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def post(self, *_args, **_kwargs):
            return FakeResponse()

    monkeypatch.setattr(ai_service.settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(ai_service.settings, "openai_api_key", "")
    monkeypatch.setattr(ai_service.httpx, "Client", FakeClient)

    intent, provider, fallback_used = ai_service.interpret_intent("Mostrame el stock", ReportFilters())

    assert provider == "local"
    assert fallback_used is True
    assert "sql" not in intent.model_dump()
    assert "tenant_id" not in intent.filters.model_dump()


def test_cu15_2_openai_intent_schema_is_strict_and_allowlisted():
    payload = ai_service._openai_intent_payload("Mostrame el stock", ReportFilters())
    schema = payload["text"]["format"]["schema"]

    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {"kind", "filters", "reasoning"}
    assert "sql" not in schema["properties"]
    filters_schema = schema["properties"]["filters"]
    assert filters_schema["additionalProperties"] is False
    assert set(filters_schema["properties"]) == {"date_from", "date_to", "branch_id"}
    assert "sql" not in filters_schema["properties"]
    assert "tenant_id" not in filters_schema["properties"]


def _seed_ml_tenant(
    session: Session,
    tenant_name: str,
    has_generative: bool = True,
    role_admin: Role | None = None,
) -> tuple[Tenant, User, str]:
    plan = SubscriptionPlan(
        code=f"PLAN_{tenant_name.upper()[:15]}",
        name=f"Plan {tenant_name}",
        max_active_branches=5,
        generative_reports_enabled=has_generative,
    )
    tenant = Tenant(name=tenant_name, status="ACTIVE")
    tenant.subscriptions.append(
        Subscription(
            plan=plan,
            status="ACTIVE",
            valid_from=datetime.now(timezone.utc) - timedelta(days=30),
            valid_until=datetime.now(timezone.utc) + timedelta(days=335),
        )
    )
    session.add_all([plan, tenant])
    session.flush()

    if role_admin is None:
        role_admin = session.scalar(select(Role).where(Role.code == "ADMIN"))
        if role_admin is None:
            role_admin = Role(code="ADMIN", name="Administrador")
            session.add(role_admin)
            session.flush()

    raw_password = f"SecretPass_{tenant_name}1!"
    user = User(
        tenant_id=tenant.id,
        role_id=role_admin.id,
        email=f"admin@{tenant_name.lower().replace(' ', '')}.com",
        phone="70000001",
        password_hash=hash_password(raw_password),
        first_name="Admin",
        last_name=tenant_name,
        is_active=True,
    )
    session.add(user)
    session.flush()
    return tenant, user, raw_password


def test_cu15_1_tenantless_assistant_routes_deny_before_work(monkeypatch: pytest.MonkeyPatch):
    user = User(tenant_id=None)
    request = ReportAssistantRequest(prompt="Ventas por sucursal")
    db = type("Db", (), {})()
    monkeypatch.setattr(reports_router, "check_tenant_feature", lambda *args: pytest.fail("feature check must not run"))
    monkeypatch.setattr(reports_router.service, "assistant_report", lambda *args, **kwargs: pytest.fail("service must not run"))

    for handler in (reports_router.report_assistant, reports_router.export_assistant_report):
        with pytest.raises(HTTPException) as exc_info:
            if handler is reports_router.report_assistant:
                handler(user, request, db)
            else:
                handler(user, "pdf", request, db)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "TENANT_CONTEXT_REQUIRED"


def test_cu15_1_assistant_service_rejects_unbound_or_mismatched_session_before_ai(monkeypatch: pytest.MonkeyPatch):
    request = ReportAssistantRequest(prompt="Ventas por sucursal")
    monkeypatch.setattr(ai_service, "interpret_intent", lambda *args, **kwargs: pytest.fail("AI interpretation must not run"))

    for info in ({}, {"tenant_context_active": True, "tenant_id": 2}):
        db = type("Db", (), {"info": info})()
        with pytest.raises(HTTPException) as exc_info:
            reports_router.service.assistant_report(db, request, tenant_id=1)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "TENANT_CONTEXT_REQUIRED"


def test_cu15_1_assistant_rejects_foreign_branch_with_non_enumerating_404(monkeypatch: pytest.MonkeyPatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        role = Role(code="ADMIN", name="Administrador")
        city = City(name="Branch City", is_active=True)
        db.add_all([role, city])
        db.flush()
        tenant_a, _, _ = _seed_ml_tenant(db, "AssistantA", role_admin=role)
        tenant_b, _, _ = _seed_ml_tenant(db, "AssistantB", role_admin=role)
        foreign_branch = Branch(tenant_id=tenant_b.id, city_id=city.id, name="Foreign", address="Elsewhere", phone="70000002")
        db.add(foreign_branch)
        db.flush()
        db.info.update({"tenant_context_active": True, "tenant_id": tenant_a.id})
        intent = ReportAssistantIntent(kind="top_products", filters=ReportFilters(branch_id=foreign_branch.id))
        monkeypatch.setattr(ai_service, "interpret_intent", lambda *args, **kwargs: (intent, "local", False))
        with pytest.raises(HTTPException) as exc_info:
            reports_router.service.assistant_report(db, ReportAssistantRequest(prompt="Productos"), tenant_id=tenant_a.id)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["code"] in {"BRANCH_NOT_FOUND", "REPORT_DATA_NOT_FOUND"}


def test_cu15_1_assistant_rejects_inactive_same_tenant_branch(monkeypatch: pytest.MonkeyPatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        role = Role(code="ADMIN", name="Administrador")
        city = City(name="Inactive Branch City", is_active=True)
        db.add_all([role, city])
        db.flush()
        tenant, _, _ = _seed_ml_tenant(db, "InactiveBranch", role_admin=role)
        inactive_branch = Branch(
            tenant_id=tenant.id,
            city_id=city.id,
            name="Inactive Local",
            address="Elsewhere",
            phone="70000003",
            is_active=False,
        )
        db.add(inactive_branch)
        db.flush()
        db.info.update({"tenant_context_active": True, "tenant_id": tenant.id})
        intent = ReportAssistantIntent(kind="sales_by_branch", filters=ReportFilters(branch_id=inactive_branch.id))
        monkeypatch.setattr(ai_service, "interpret_intent", lambda *args, **kwargs: (intent, "local", False))
        with pytest.raises(HTTPException) as exc_info:
            reports_router.service.assistant_report(db, ReportAssistantRequest(prompt="Ventas por sucursal"), tenant_id=tenant.id)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["code"] == "BRANCH_NOT_FOUND"


def test_cu15_1_assistant_uses_bound_tenant_context_for_normal_request(monkeypatch: pytest.MonkeyPatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        role = Role(code="ADMIN", name="Administrador")
        db.add(role)
        db.flush()
        tenant, _, _ = _seed_ml_tenant(db, "BoundAssistant", role_admin=role)
        db.info.update({"tenant_context_active": True, "tenant_id": tenant.id})
        intent = ReportAssistantIntent(kind="inventory", filters=ReportFilters())
        monkeypatch.setattr(ai_service, "interpret_intent", lambda *args, **kwargs: (intent, "local", False))
        monkeypatch.setattr(ai_service, "build_narrative", lambda *args, **kwargs: ("ok", False))
        response = reports_router.service.assistant_report(db, ReportAssistantRequest(prompt="Stock"), tenant_id=tenant.id)
        assert response.provider == "local"
        assert response.narrative == "ok"


def test_t3_1_assistant_intent_classification_and_chart_type(monkeypatch: pytest.MonkeyPatch):
    """T3.1.1: Valida interpretación de intenciones y tipo de gráfico recomendado para los 4 reportes obligatorios."""
    monkeypatch.setattr(ai_service.settings, "gemini_api_key", "")
    monkeypatch.setattr(ai_service.settings, "openai_api_key", "")
    filters = ReportFilters()

    # 1. Ventas por sucursal / comparación
    intent_branch, _, _ = ai_service.interpret_intent("Mostrame las ventas de septiembre agrupadas por sucursal", filters)
    assert intent_branch.kind == "sales_by_branch"
    assert intent_branch.chart_type in ("bar", "line")

    # 2. Top productos
    intent_top, _, _ = ai_service.interpret_intent("¿Cuáles fueron los diez productos más vendidos este mes?", filters)
    assert intent_top.kind == "top_products"
    assert intent_top.chart_type == "bar"

    # 3. Bajo stock
    intent_inv, _, _ = ai_service.interpret_intent("Mostrame los productos con menor existencia y alerta de stock", filters)
    assert intent_inv.kind == "inventory"
    assert intent_inv.chart_type == "table"

    # 4. Ingresos por categoría
    intent_cat, _, _ = ai_service.interpret_intent("¿Qué categorías generaron mayores ingresos durante este período?", filters)
    assert intent_cat.kind == "revenue_by_category"
    assert intent_cat.chart_type in ("pie", "bar")


def test_t3_1_subscription_plan_blocks_generative_reports_for_basic_plan(monkeypatch: pytest.MonkeyPatch):
    """T3.1.3: Plan Básico (sin generative_reports_enabled) bloquea reportes generativos con 403 FEATURE_NOT_IN_PLAN."""
    monkeypatch.setattr(ai_service.settings, "gemini_api_key", "")
    monkeypatch.setattr(ai_service.settings, "openai_api_key", "")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        role_admin = Role(code="ADMIN", name="Administrador")
        session.add(role_admin)
        session.flush()

        t_basic, u_basic, p_basic = _seed_ml_tenant(session, "BasicCo", has_generative=False, role_admin=role_admin)
        t_pro, u_pro, p_pro = _seed_ml_tenant(session, "ProCo", has_generative=True, role_admin=role_admin)
        session.commit()

        email_basic, email_pro = u_basic.email, u_pro.email

    def override_db():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)

    try:
        # Login basic user
        login_basic = client.post("/api/v1/auth/login", json={"email": email_basic, "password": p_basic})
        assert login_basic.status_code == 200
        token_basic = login_basic.json()["access_token"]

        # Login pro user
        login_pro = client.post("/api/v1/auth/login", json={"email": email_pro, "password": p_pro})
        assert login_pro.status_code == 200
        token_pro = login_pro.json()["access_token"]

        # Intento de consulta en Plan Básico -> 403 Forbidden
        res_basic = client.post(
            "/api/v1/reports/assistant",
            json={"prompt": "Ventas por sucursal este mes"},
            headers={"Authorization": f"Bearer {token_basic}"},
        )
        assert res_basic.status_code == 403
        data_basic = res_basic.json()["detail"]
        assert data_basic["code"] == "FEATURE_NOT_IN_PLAN"
        assert "no están incluidos en su plan" in data_basic["message"]

        # Intento de modelos ML en Plan Básico -> 403 Forbidden
        res_ml = client.get(
            "/api/v1/reports/ml/demand-forecast",
            headers={"Authorization": f"Bearer {token_basic}"},
        )
        assert res_ml.status_code == 403

        # Consulta en Plan Profesional -> 200 OK
        res_pro = client.post(
            "/api/v1/reports/assistant",
            json={"prompt": "Ventas por sucursal este mes"},
            headers={"Authorization": f"Bearer {token_pro}"},
        )
        assert res_pro.status_code == 200
        data_pro = res_pro.json()
        assert "intent" in data_pro
        assert "narrative" in data_pro
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_t3_1_multitenant_report_data_isolation(monkeypatch: pytest.MonkeyPatch):
    """T3.1.2: Las consultas de reportes con IA respetan estrictamente el aislamiento por tenant_id."""
    # Keep every assistant request local even when developer credentials are configured.
    monkeypatch.setattr(ai_service.settings, "gemini_api_key", "")
    monkeypatch.setattr(ai_service.settings, "openai_api_key", "")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        role_admin = Role(code="ADMIN", name="Administrador")
        city = City(name="Cochabamba", is_active=True)
        session.add_all([role_admin, city])
        session.flush()

        t1, u1, p1 = _seed_ml_tenant(session, "AtelierAlpha", has_generative=True, role_admin=role_admin)
        t2, u2, p2 = _seed_ml_tenant(session, "BoutiqueBeta", has_generative=True, role_admin=role_admin)

        b1 = Branch(tenant_id=t1.id, city_id=city.id, name="Sucursal Alpha", address="Av. Uno", phone="71111111")
        b2 = Branch(tenant_id=t2.id, city_id=city.id, name="Sucursal Beta", address="Av. Dos", phone="72222222")
        session.add_all([b1, b2])
        session.flush()

        size = Size(name="M", size_type="ALPHA")
        color = Color(name="Azul", hex_code="#0000FF")
        session.add_all([size, color])
        session.flush()

        cat1 = Category(tenant_id=t1.id, name="Vestidos Alpha")
        cat2 = Category(tenant_id=t2.id, name="Calzados Beta")
        session.add_all([cat1, cat2])
        session.flush()

        prod1 = Product(tenant_id=t1.id, category_id=cat1.id, name="Vestido Seda Alpha", code="V-A1", slug="v-a1", price=Decimal("200.0"))
        prod2 = Product(tenant_id=t2.id, category_id=cat2.id, name="Zapatos Cuero Beta", code="Z-B1", slug="z-b1", price=Decimal("300.0"))
        session.add_all([prod1, prod2])
        session.flush()

        var1 = ProductVariant(tenant_id=t1.id, product_id=prod1.id, sku="SKU-VA1", size_id=size.id, color_id=color.id)
        var2 = ProductVariant(tenant_id=t2.id, product_id=prod2.id, sku="SKU-ZB1", size_id=size.id, color_id=color.id)
        session.add_all([var1, var2])
        session.flush()

        sale1 = Sale(tenant_id=t1.id, branch_id=b1.id, order_number="ORD-T1-1", channel="PHYSICAL", status="COMPLETED", subtotal=Decimal("200.0"), total=Decimal("200.0"))
        sale1.items.append(SaleItem(product_variant_id=var1.id, quantity=1, unit_price=Decimal("200.0"), line_total=Decimal("200.0")))

        sale2 = Sale(tenant_id=t2.id, branch_id=b2.id, order_number="ORD-T2-1", channel="PHYSICAL", status="COMPLETED", subtotal=Decimal("600.0"), total=Decimal("600.0"))
        sale2.items.append(SaleItem(product_variant_id=var2.id, quantity=2, unit_price=Decimal("300.0"), line_total=Decimal("600.0")))

        session.add_all([sale1, sale2])
        session.commit()

        email1 = u1.email

    def override_db():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)

    try:
        login_res = client.post("/api/v1/auth/login", json={"email": email1, "password": p1})
        assert login_res.status_code == 200
        token1 = login_res.json()["access_token"]

        headers = {"Authorization": f"Bearer {token1}"}

        # Preserve category coverage and extend isolation checks across every report shape.
        responses = {
            "category": client.post(
                "/api/v1/reports/assistant",
                json={"prompt": "¿Qué categorías generaron mayores ingresos?"},
                headers=headers,
            ),
            "top_products": client.post(
                "/api/v1/reports/assistant",
                json={"prompt": "¿Cuáles fueron los productos más vendidos?"},
                headers=headers,
            ),
            "sales_by_branch": client.post(
                "/api/v1/reports/assistant",
                json={"prompt": "Mostrame las ventas por sucursal"},
                headers=headers,
            ),
            "dashboard": client.post(
                "/api/v1/reports/assistant",
                json={"prompt": "Mostrame el resumen ejecutivo"},
                headers=headers,
            ),
        }
        assert all(response.status_code == 200 for response in responses.values())

        category_body = responses["category"].json()
        assert category_body["intent"]["kind"] == "revenue_by_category"
        categories_returned = [item["category_name"] for item in category_body["data"]]
        assert "Vestidos Alpha" in categories_returned
        assert "Calzados Beta" not in categories_returned  # No data leak!
        assert len(category_body["data"]) == 1
        assert Decimal(str(category_body["data"][0]["total_revenue"])) == Decimal("200.00")

        top_products_body = responses["top_products"].json()
        assert top_products_body["intent"]["kind"] == "top_products"
        products_returned = [item["product_name"] for item in top_products_body["data"]]
        assert "Vestido Seda Alpha" in products_returned
        assert "Zapatos Cuero Beta" not in products_returned
        assert len(top_products_body["data"]) == 1
        assert top_products_body["data"][0]["units_sold"] == 1
        assert Decimal(str(top_products_body["data"][0]["revenue"])) == Decimal("200.00")

        branch_body = responses["sales_by_branch"].json()
        assert branch_body["intent"]["kind"] == "sales_by_branch"
        branches_returned = [item["branch_name"] for item in branch_body["data"]]
        assert "Sucursal Alpha" in branches_returned
        assert "Sucursal Beta" not in branches_returned
        assert len(branch_body["data"]) == 1
        assert branch_body["data"][0]["sales_count"] == 1
        assert Decimal(str(branch_body["data"][0]["total"])) == Decimal("200.00")

        dashboard_body = responses["dashboard"].json()
        assert dashboard_body["intent"]["kind"] == "dashboard"
        dashboard_products = [item["product_name"] for item in dashboard_body["data"]["top_products"]]
        dashboard_branches = [item["branch_name"] for item in dashboard_body["data"]["sales_by_branch"]]
        assert "Vestido Seda Alpha" in dashboard_products
        assert "Zapatos Cuero Beta" not in dashboard_products
        assert "Sucursal Alpha" in dashboard_branches
        assert "Sucursal Beta" not in dashboard_branches
        assert dashboard_body["data"]["revenue"]["sales_count"] == 1
        assert Decimal(str(dashboard_body["data"]["revenue"]["total"])) == Decimal("200.00")
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_cu18_1_synthetic_generators_are_tenant_seeded_and_day_normalized():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        role_admin = Role(code="ADMIN", name="Administrador")
        session.add(role_admin)
        session.flush()
        tenant, _, _ = _seed_ml_tenant(session, "DeterministicCo", role_admin=role_admin)
        session.commit()

        first_sales = ml_service.SyntheticDataService.generate_sales_series(session, tenant.id, days=3)
        second_sales = ml_service.SyntheticDataService.generate_sales_series(session, tenant.id, days=3)
        first_rfm = ml_service.SyntheticDataService.generate_customer_rfm_profiles(session, tenant.id, num_customers=8)
        second_rfm = ml_service.SyntheticDataService.generate_customer_rfm_profiles(session, tenant.id, num_customers=8)

        assert first_sales == second_sales
        assert first_rfm == second_rfm
        assert all(record["date"].hour == 0 for record in first_sales)
        assert all(record["date"].tzinfo == timezone.utc for record in first_sales)


def test_cu18_1_sparse_ml_paths_report_real_and_synthetic_sample_counts():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        role_admin = Role(code="ADMIN", name="Administrador")
        session.add(role_admin)
        session.flush()
        tenant, _, _ = _seed_ml_tenant(session, "SparseMetricsCo", role_admin=role_admin)
        session.commit()

        forecast = ml_service.DemandForecastService.forecast_demand(session, tenant.id, weeks_ahead=1)
        segmentation = ml_service.CustomerSegmentationService.segment_customers(session, tenant.id)

        assert forecast.metrics.samples_count == 70
        assert forecast.metrics.real_samples_count == 0
        assert forecast.metrics.synthetic_samples_count == 70
        assert segmentation.metrics.samples_count == 60
        assert segmentation.metrics.real_samples_count == 0
        assert segmentation.metrics.synthetic_samples_count == 60


def test_cu18_1_forecast_counts_real_rows_and_non_overwritten_synthetic_days(monkeypatch: pytest.MonkeyPatch):
    class FakeResult:
        def all(self):
            return [("2024-01-02", 1, 9, Decimal("90")), ("2024-01-20", 1, 7, Decimal("70"))]

    class FakeDb:
        def execute(self, _query):
            return FakeResult()

    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    synthetic = [
        {"date": base + timedelta(days=index), "branch_id": 1, "units_sold": 10, "revenue": Decimal("100")}
        for index in range(20)
    ]
    monkeypatch.setattr(ml_service.SyntheticDataService, "generate_sales_series", lambda *args, **kwargs: synthetic)

    response = ml_service.DemandForecastService.forecast_demand(FakeDb(), tenant_id=7, weeks_ahead=1)

    assert response.metrics.real_samples_count == 2
    assert response.metrics.synthetic_samples_count == 18
    assert response.metrics.samples_count == 20


def test_t3_2_synthetic_data_and_supervised_demand_forecast():
    """T3.2.1 & T3.2.2: Generación sintética y modelo supervisado de proyección de demanda con MAE/RMSE/R2."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        role_admin = Role(code="ADMIN", name="Administrador")
        city = City(name="Santa Cruz", is_active=True)
        session.add_all([role_admin, city])
        session.flush()

        tenant, user, _ = _seed_ml_tenant(session, "DemandCo", has_generative=True, role_admin=role_admin)
        branch = Branch(tenant_id=tenant.id, city_id=city.id, name="Sede Principal", address="Av. Bush", phone="1234567")
        session.add(branch)
        session.commit()

        # Generador de datos sintéticos
        series = ml_service.SyntheticDataService.generate_sales_series(session, tenant.id, days=60)
        assert len(series) >= 60
        assert all("units_sold" in r and "revenue" in r for r in series)

        # Proyección supervisada
        forecast = ml_service.DemandForecastService.forecast_demand(
            session,
            tenant_id=tenant.id,
            branch_id=branch.id,
            weeks_ahead=4,
        )

        assert forecast.target == "ventas_semanales"
        assert len(forecast.forecast) == 4
        assert forecast.metrics.mae is not None and forecast.metrics.mae >= 0.0
        assert forecast.metrics.rmse is not None and forecast.metrics.rmse >= 0.0
        assert forecast.metrics.r2_score is not None
        assert "Proyección supervisada" in forecast.narrative


def test_t3_2_unsupervised_customer_segmentation_kmeans_rfm():
    """T3.2.3: Modelo no supervisado K-Means RFM agrupa clientes en clusters con métrica Silhouette Score."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        role_admin = Role(code="ADMIN", name="Administrador")
        session.add(role_admin)
        session.flush()

        tenant, user, _ = _seed_ml_tenant(session, "SegmentCo", has_generative=True, role_admin=role_admin)
        session.commit()

        clustering = ml_service.CustomerSegmentationService.segment_customers(
            session,
            tenant_id=tenant.id,
            n_clusters=4,
        )

        assert clustering.clusters_count == 4
        assert len(clustering.segments) == 4
        assert clustering.silhouette_score is not None
        assert clustering.metrics.silhouette_score is not None
        assert clustering.inertia > 0.0

        segment_names = [s.name for s in clustering.segments]
        assert "Clientes VIP / Champions" in segment_names
        assert all(s.suggested_action for s in clustering.segments)
        assert "K-Means RFM" in clustering.narrative


def test_cu19_2_ml_routes_deny_tenantless_users_before_service_invocation(monkeypatch: pytest.MonkeyPatch):
    user = User(tenant_id=None)
    invoked = False

    def fail_if_called(*args, **kwargs):
        nonlocal invoked
        invoked = True
        raise AssertionError("ML service must not run without tenant context")

    monkeypatch.setattr(ml_service.DemandForecastService, "forecast_demand", fail_if_called)
    with pytest.raises(Exception) as exc_info:
        reports_router.demand_forecast(user, db=object())
    assert getattr(exc_info.value, "status_code", None) == 403
    assert "tenant" in str(getattr(exc_info.value, "detail", "")).lower()
    assert invoked is False

    for endpoint in (reports_router.customer_segments, reports_router.train_ml_models):
        with pytest.raises(Exception) as endpoint_exc:
            endpoint(user, db=object())
        assert getattr(endpoint_exc.value, "status_code", None) == 403


def test_cu19_2_forecast_rejects_foreign_or_inactive_branch_without_enumeration(monkeypatch: pytest.MonkeyPatch):
    user = User(tenant_id=10)
    class FakeDb:
        def scalar(self, _query):
            return None

    monkeypatch.setattr(ml_service.DemandForecastService, "forecast_demand", lambda *args, **kwargs: None)
    for branch_id in (20, 21, 999):
        with pytest.raises(Exception) as exc_info:
            reports_router.demand_forecast(user, branch_id=branch_id, weeks_ahead=6, db=FakeDb())
        assert getattr(exc_info.value, "status_code", None) == 404
        assert getattr(exc_info.value, "detail", None) == "Branch not found"


def test_cu19_2_ml_parameter_bounds_are_enforced_at_api_boundary():
    with pytest.raises(Exception) as exc_info:
        reports_router.demand_forecast(User(tenant_id=1), weeks_ahead=0, db=object())
    assert getattr(exc_info.value, "status_code", None) == 422

    with pytest.raises(Exception) as exc_info:
        reports_router.customer_segments(User(tenant_id=1), n_clusters=13, db=object())
    assert getattr(exc_info.value, "status_code", None) == 422


def test_cu19_2_forecast_uses_chronological_split(monkeypatch: pytest.MonkeyPatch):
    class FakeResult:
        def all(self):
            return [(f"2024-01-{day:02d}", 1, day, Decimal(day * 10)) for day in range(1, 21)]

    class FakeDb:
        def execute(self, _query):
            return FakeResult()

        def get(self, *_args):
            return None

    captured: list[tuple[object, object]] = []
    original_fit = ml_service.Ridge.fit

    def capture_fit(model, features, target):
        captured.append((features.copy(), target.copy()))
        return original_fit(model, features, target)

    monkeypatch.setattr(ml_service.Ridge, "fit", capture_fit)
    response = ml_service.DemandForecastService.forecast_demand(FakeDb(), tenant_id=7, weeks_ahead=1)
    assert response.metrics.samples_count == 20
    train_features = captured[0][0]
    assert train_features[:, 0].tolist() == sorted(train_features[:, 0].tolist())
    assert train_features[-1, 0] < response.metrics.samples_count - 1


def test_cu20_3_anomalies_are_deterministic_limited_and_provenanced(monkeypatch: pytest.MonkeyPatch):
    class FakeResult:
        def all(self):
            return []

    class FakeDb:
        def execute(self, _query):
            return FakeResult()

    profiles = [
        {
            "customer_id": index + 1,
            "recency_days": 10 + (index % 5),
            "frequency": 4 + (index % 4),
            "monetary": Decimal(str(100 + index * 10)),
        }
        for index in range(25)
    ]
    profiles.append(
        {
            "customer_id": 999,
            "recency_days": 3650,
            "frequency": 1,
            "monetary": Decimal("999999"),
        }
    )
    monkeypatch.setattr(
        ml_service.SyntheticDataService,
        "generate_customer_rfm_profiles",
        lambda *args, **kwargs: profiles,
    )

    response = ml_service.CustomerSegmentationService.segment_customers(FakeDb(), tenant_id=7)
    repeated_response = ml_service.CustomerSegmentationService.segment_customers(FakeDb(), tenant_id=7)

    assert response.anomalies_count == repeated_response.anomalies_count
    assert [item.model_dump() for item in response.anomalies] == [
        item.model_dump() for item in repeated_response.anomalies
    ]
    assert response.anomalies_count >= 1
    assert len(response.anomalies) <= 10
    assert response.anomalies[0].monetary == Decimal("999999")
    assert response.anomalies[0].data_source == "synthetic"
    assert all(item.data_source in {"real", "synthetic"} for item in response.anomalies)
    assert all("customer_id" not in item.model_dump() for item in response.anomalies)
    assert [item.anomaly_score for item in response.anomalies] == sorted(
        (item.anomaly_score for item in response.anomalies), reverse=True
    )


def test_cu20_3_anomaly_detection_handles_empty_and_degenerate_profiles(monkeypatch: pytest.MonkeyPatch):
    class FakeResult:
        def all(self):
            return []

    class FakeDb:
        def execute(self, _query):
            return FakeResult()

    monkeypatch.setattr(
        ml_service.SyntheticDataService,
        "generate_customer_rfm_profiles",
        lambda *args, **kwargs: [],
    )
    empty_response = ml_service.CustomerSegmentationService.segment_customers(FakeDb(), tenant_id=7)
    assert empty_response.anomalies == []
    assert empty_response.anomalies_count == 0
    assert "insuficientes" in empty_response.narrative.lower()

    degenerate_profiles = [
        {
            "customer_id": index + 1,
            "recency_days": 10,
            "frequency": 2,
            "monetary": Decimal("100"),
        }
        for index in range(4)
    ]
    monkeypatch.setattr(
        ml_service.SyntheticDataService,
        "generate_customer_rfm_profiles",
        lambda *args, **kwargs: degenerate_profiles,
    )
    degenerate_response = ml_service.CustomerSegmentationService.segment_customers(FakeDb(), tenant_id=7)
    assert degenerate_response.anomalies == []
    assert degenerate_response.anomalies_count == 0
    assert "insuficientes" in degenerate_response.narrative.lower()


def test_cu19_2_negative_r2_is_preserved(monkeypatch: pytest.MonkeyPatch):
    class FakeResult:
        def all(self):
            return [(f"2024-01-{day:02d}", 1, day, Decimal(day * 10)) for day in range(1, 21)]

    class FakeDb:
        def execute(self, _query):
            return FakeResult()

        def get(self, *_args):
            return None

    monkeypatch.setattr(ml_service, "r2_score", lambda *_args, **_kwargs: -0.5)
    response = ml_service.DemandForecastService.forecast_demand(FakeDb(), tenant_id=7, weeks_ahead=1)
    assert response.metrics.r2_score == -0.5
    assert "R²=-0.50" in response.narrative


@pytest.mark.parametrize("unavailable_r2", [None, float("nan")])
def test_cu19_2_unavailable_or_nonfinite_r2_is_nullable(monkeypatch: pytest.MonkeyPatch, unavailable_r2: float | None):
    class FakeResult:
        def all(self):
            return [(f"2024-01-{day:02d}", 1, day, Decimal(day * 10)) for day in range(1, 21)]

    class FakeDb:
        def execute(self, _query):
            return FakeResult()

        def get(self, *_args):
            return None

    monkeypatch.setattr(ml_service, "r2_score", lambda *_args, **_kwargs: unavailable_r2)
    response = ml_service.DemandForecastService.forecast_demand(FakeDb(), tenant_id=7, weeks_ahead=1)

    assert response.metrics.r2_score is None
    assert "MAE=" in response.narrative
    assert "RMSE=" in response.narrative
    assert "R² no disponible" in response.narrative
    assert "insuficiencia de datos" not in response.narrative


def test_dynamic_report_xlsx_neutralizes_formula_like_strings_without_stringifying_numbers():
    workbook_bytes = export_service.export_dynamic_report(
        title=" =Título",
        headers=[" +Encabezado", "Valor"],
        rows=[[" -texto", " @dato"], [-7, 12]],
        narrative=" =Narrativa",
        format_name="xlsx",
    ).content

    workbook = load_workbook(io.BytesIO(workbook_bytes), data_only=False)
    sheet = workbook.active
    assert sheet["A1"].value == "' =Título"
    assert sheet["A3"].value == "Diagnóstico Ejecutivo: ' =Narrativa"
    assert sheet["A5"].value == "' +Encabezado"
    assert sheet["A6"].value == "' -texto"
    assert sheet["B6"].value == "' @dato"
    assert sheet["A7"].value == -7
    assert isinstance(sheet["A7"].value, int)


def test_dynamic_report_pdf_escapes_dynamic_title(monkeypatch: pytest.MonkeyPatch):
    original_paragraph = export_service.Paragraph
    captured: list[str] = []

    def recording_paragraph(text: str, style: object):
        captured.append(text)
        return original_paragraph(text, style)

    monkeypatch.setattr(export_service, "Paragraph", recording_paragraph)
    export_service.export_dynamic_report(
        title="Título <riesgoso> & especial",
        headers=["Columna"],
        rows=[["Dato"]],
        format_name="pdf",
    )

    assert "<b>Título &lt;riesgoso&gt; &amp; especial</b>" in captured


def test_t3_1_dynamic_report_export_excel_and_pdf():
    """T3.1.4: Exportación dinámica del reporte generado a formato Excel (.xlsx) y PDF (.pdf)."""
    headers = ["Categoría", "Ventas", "Unidades", "Ingresos"]
    rows = [
        ["Vestidos Fiesta", 12, 18, "Bs 3,600.00"],
        ["Pantalones Lino", 8, 10, "Bs 1,200.00"],
    ]
    narrative = "La categoría Vestidos Fiesta lidera con un 75% de participación comercial."

    # Exportación Excel
    export_xlsx = export_service.export_dynamic_report(
        title="Ingresos por Categoría",
        headers=headers,
        rows=rows,
        narrative=narrative,
        format_name="xlsx",
    )
    assert export_xlsx.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert export_xlsx.filename.endswith(".xlsx")
    assert len(export_xlsx.content) > 0
    # Valida formato ZIP válido de Excel
    with zipfile.ZipFile(io.BytesIO(export_xlsx.content)) as z:
        assert "[Content_Types].xml" in z.namelist()

    # Exportación PDF
    export_pdf = export_service.export_dynamic_report(
        title="Ingresos por Categoría",
        headers=headers,
        rows=rows,
        narrative=narrative,
        format_name="pdf",
    )
    assert export_pdf.media_type == "application/pdf"
    assert export_pdf.filename.endswith(".pdf")
    assert export_pdf.content.startswith(b"%PDF-")
