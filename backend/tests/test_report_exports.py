import os
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret"

from fastapi.testclient import TestClient  # noqa: E402
from openpyxl import load_workbook  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import get_db  # noqa: E402
from app.core.models import Base, Branch, Category, City, Color, Inventory, Product, ProductVariant, Reservation, Role, Sale, SaleItem, Season, Size, User  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402

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
        db.add(admin_role)
        db.flush()
        db.add(
            User(
                role=admin_role,
                first_name="Reports",
                last_name="Admin",
                email="reports-admin@example.com",
                phone="70000099",
                password_hash=hash_password("Admin123!"),
            )
        )
        db.commit()


def teardown_function() -> None:
    if _previous_get_db_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = _previous_get_db_override


def _headers() -> dict[str, str]:
    tokens = client.post("/api/v1/auth/login", json={"email": "reports-admin@example.com", "password": "Admin123!"}).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _seed_report_data() -> None:
    with Session(engine) as db:
        category = Category(name="Reports Category")
        size = Size(name="Reports M")
        color = Color(name="Reports Blue", hex_code="#0000FF")
        season = Season(name="Reports Season")
        city = City(name="Santa Cruz")
        db.add_all([category, size, color, season, city])
        db.flush()
        branch = Branch(city_id=city.id, name="Sucursal Centro", address="Av. Moda 123", phone="70000000")
        product = Product(category_id=category.id, season_id=season.id, code="REP-001", name="Report Shirt", slug="report-shirt", price=Decimal("120.00"))
        db.add_all([branch, product])
        db.flush()
        variant = ProductVariant(product_id=product.id, size_id=size.id, color_id=color.id, sku="REP-001-M-BLUE")
        db.add(variant)
        db.flush()
        db.add(Inventory(branch_id=branch.id, product_variant_id=variant.id, stock_quantity=8, reserved_quantity=1))
        sale = Sale(
            order_number="RPT-0001",
            branch_id=branch.id,
            channel="PHYSICAL",
            status="CONFIRMED",
            subtotal=Decimal("240.00"),
            discount=Decimal("0.00"),
            total=Decimal("240.00"),
            created_at=datetime(2024, 5, 20, 12, 0, tzinfo=UTC),
        )
        db.add(sale)
        db.flush()
        db.add(SaleItem(sale_id=sale.id, product_variant_id=variant.id, quantity=2, unit_price=Decimal("120.00"), discount=Decimal("0.00"), line_total=Decimal("240.00")))
        admin = db.query(User).filter(User.email == "reports-admin@example.com").one()
        db.add(Reservation(customer_id=admin.id, branch_id=branch.id, status="PENDING", created_at=datetime(2024, 5, 20, 11, 0, tzinfo=UTC)))
        db.commit()


def test_report_snapshot_export_xlsx_uses_existing_report_sections() -> None:
    _seed_report_data()

    response = client.get("/api/v1/reports/export/xlsx", headers=_headers())

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert 'attachment; filename="fashionstore-report-all-to-all-all-branches.xlsx"' == response.headers["content-disposition"]
    workbook = load_workbook(BytesIO(response.content), data_only=True)
    assert workbook.sheetnames == ["Summary", "Top Products", "Branches", "Channels", "Reservations", "Low Stock"]
    assert workbook["Summary"]["B2"].value == 1
    assert workbook["Top Products"]["B2"].value == "Report Shirt"
    assert workbook["Branches"]["B2"].value == "Sucursal Centro"
    assert workbook["Channels"]["A2"].value == "PHYSICAL"
    assert workbook["Reservations"]["A2"].value == "PENDING"
    assert workbook["Low Stock"]["F2"].value == "REP-001-M-BLUE"


def test_report_export_pdf_and_pptx_return_downloadable_bytes() -> None:
    _seed_report_data()
    headers = _headers()

    pdf = client.get("/api/v1/reports/export/pdf?date_from=2024-05-01T00:00:00Z&date_to=2024-05-31T23:59:59Z", headers=headers)
    pptx = client.get("/api/v1/reports/export/pptx", headers=headers)

    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF-1.4")
    assert "filename=\"fashionstore-report-2024-05-01-to-2024-05-31-all-branches.pdf\"" in pdf.headers["content-disposition"]
    assert pptx.status_code == 200
    assert pptx.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    with ZipFile(BytesIO(pptx.content)) as package:
        assert "ppt/presentation.xml" in package.namelist()
        assert "ppt/slides/slide1.xml" in package.namelist()


def test_report_export_rejects_invalid_date_range_and_missing_data() -> None:
    headers = _headers()

    invalid_range = client.get("/api/v1/reports/export/xlsx?date_from=2024-06-01T00:00:00Z&date_to=2024-05-01T00:00:00Z", headers=headers)
    missing_data = client.get("/api/v1/reports/export/xlsx", headers=headers)

    assert invalid_range.status_code == 422
    assert invalid_range.json()["detail"]["code"] == "INVALID_DATE_RANGE"
    assert missing_data.status_code == 404
    assert missing_data.json()["detail"]["code"] == "REPORT_DATA_NOT_FOUND"


def test_report_export_requires_authentication() -> None:
    response = client.get("/api/v1/reports/export/xlsx")

    assert response.status_code == 401
