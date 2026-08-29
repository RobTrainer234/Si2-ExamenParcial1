import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import get_db  # noqa: E402
from app.core.models import Base, Branch, Category, City, Color, Inventory, Product, ProductVariant, Role, Size, Supplier, User  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)


def override_get_db():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function() -> None:
    with Session(engine) as db:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        db.add(Role(code="CLIENT", name="Cliente"))
        db.commit()


def test_register_login_and_me() -> None:
    payload = {
        "first_name": "Ana",
        "last_name": "Lopez",
        "email": "ana@example.com",
        "phone": "+591 70000000",
        "password": "Secure123!",
    }
    register_response = client.post("/api/v1/auth/register", json=payload)

    assert register_response.status_code == 201
    tokens = register_response.json()
    assert tokens["user"]["role"] == "CLIENT"
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "ana@example.com"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_response.status_code == 200


def test_duplicate_email_and_invalid_login() -> None:
    payload = {
        "first_name": "Ana",
        "last_name": "Lopez",
        "email": "duplicate@example.com",
        "phone": "70000000",
        "password": "Secure123!",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409
    assert client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": "Wrong123!"},
    ).status_code == 401


def test_protected_endpoint_requires_token() -> None:
    assert client.get("/api/v1/auth/me").status_code == 401


def test_refresh_rotation_and_logout() -> None:
    payload = {
        "first_name": "Luis",
        "last_name": "Perez",
        "email": "luis@example.com",
        "phone": "70000001",
        "password": "Secure123!",
    }
    tokens = client.post("/api/v1/auth/register", json=payload).json()
    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
    assert client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    ).status_code == 401

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": new_tokens["refresh_token"]},
    )
    assert logout_response.status_code == 204
    assert client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": new_tokens["refresh_token"]},
    ).status_code == 401


def test_admin_can_manage_users_and_client_cannot() -> None:
    with Session(engine) as db:
        admin_role = Role(code="ADMIN", name="Administrador")
        db.add(admin_role)
        db.flush()
        client_role = db.scalar(select(Role).where(Role.code == "CLIENT"))
        db.add(
            User(
                role=admin_role,
                first_name="Admin",
                last_name="User",
                email="admin@example.com",
                phone="70000002",
                password_hash=hash_password("Admin123!"),
            )
        )
        db.add(
            User(
                role=client_role,
                first_name="Ana",
                last_name="Lopez",
                email="ana@example.com",
                phone="70000000",
                password_hash=hash_password("Secure123!"),
            )
        )
        db.commit()

    client_tokens = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": "Secure123!"},
    ).json()
    assert client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {client_tokens['access_token']}"},
    ).status_code == 403

    admin_tokens = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"},
    ).json()
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    users_response = client.get("/api/v1/users?page=1&page_size=10", headers=headers)
    assert users_response.status_code == 200
    assert users_response.json()["total"] == 2

    created = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "first_name": "Manager",
            "last_name": "User",
            "email": "manager@example.com",
            "phone": "70000003",
            "password": "Manager123!",
            "role": "CLIENT",
        },
    )
    assert created.status_code == 201
    manager_id = created.json()["id"]
    assert client.patch(f"/api/v1/users/{manager_id}/deactivate", headers=headers).status_code == 200

    admin_id = next(item["id"] for item in users_response.json()["items"] if item["email"] == "admin@example.com")
    assert client.patch(f"/api/v1/users/{admin_id}/deactivate", headers=headers).status_code == 400
    assert client.patch(
        f"/api/v1/users/{admin_id}",
        headers=headers,
        json={"role": "CLIENT"},
    ).status_code == 400


def test_admin_can_manage_cities_and_branches() -> None:
    with Session(engine) as db:
        admin_role = Role(code="ADMIN", name="Administrador")
        db.add(admin_role)
        db.flush()
        db.add(
            User(
                role=admin_role,
                first_name="Admin",
                last_name="Locations",
                email="locations-admin@example.com",
                phone="70000004",
                password_hash=hash_password("Admin123!"),
            )
        )
        db.commit()

    tokens = client.post(
        "/api/v1/auth/login",
        json={"email": "locations-admin@example.com", "password": "Admin123!"},
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    city_response = client.post("/api/v1/cities", headers=headers, json={"name": "Santa Cruz"})
    assert city_response.status_code == 201
    city_id = city_response.json()["id"]
    assert client.post("/api/v1/cities", headers=headers, json={"name": "Santa Cruz"}).status_code == 409

    branch_response = client.post(
        "/api/v1/branches",
        headers=headers,
        json={
            "city_id": city_id,
            "name": "Sucursal Centro",
            "address": "Av. Principal 100",
            "phone": "70000005",
            "latitude": -17.7833,
            "longitude": -63.1821,
        },
    )
    assert branch_response.status_code == 201
    assert branch_response.json()["city_name"] == "Santa Cruz"
    branch_id = branch_response.json()["id"]
    assert client.patch(f"/api/v1/branches/{branch_id}/deactivate", headers=headers).status_code == 200
    assert client.patch(f"/api/v1/cities/{city_id}/deactivate", headers=headers).status_code == 200
    assert client.get("/api/v1/cities?q=Santa", headers=headers).json()["total"] == 1


def test_admin_can_manage_catalog_masters() -> None:
    with Session(engine) as db:
        admin_role = Role(code="ADMIN", name="Administrador")
        db.add(admin_role)
        db.flush()
        db.add(
            User(
                role=admin_role,
                first_name="Admin",
                last_name="Masters",
                email="masters-admin@example.com",
                phone="70000006",
                password_hash=hash_password("Admin123!"),
            )
        )
        db.commit()

    tokens = client.post(
        "/api/v1/auth/login",
        json={"email": "masters-admin@example.com", "password": "Admin123!"},
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    category = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": "Camisas", "description": "Prendas superiores"},
    )
    assert category.status_code == 201
    assert client.post("/api/v1/categories", headers=headers, json={"name": "Camisas"}).status_code == 409
    assert client.patch(
        f"/api/v1/categories/{category.json()['id']}/deactivate",
        headers=headers,
    ).status_code == 200

    size = client.post("/api/v1/sizes", headers=headers, json={"name": "M"})
    color = client.post(
        "/api/v1/colors",
        headers=headers,
        json={"name": "Azul", "hex_code": "#0000FF"},
    )
    assert size.status_code == 201
    assert color.status_code == 201
    assert client.post("/api/v1/colors", headers=headers, json={"name": "Rojo", "hex_code": "blue"}).status_code == 422
    assert client.get("/api/v1/sizes?q=M", headers=headers).json()["total"] == 1


def test_admin_can_manage_suppliers() -> None:
    with Session(engine) as db:
        admin_role = Role(code="ADMIN", name="Administrador")
        db.add(admin_role)
        db.flush()
        db.add(
            User(
                role=admin_role,
                first_name="Admin",
                last_name="Suppliers",
                email="suppliers-admin@example.com",
                phone="70000007",
                password_hash=hash_password("Admin123!"),
            )
        )
        db.commit()

    tokens = client.post(
        "/api/v1/auth/login",
        json={"email": "suppliers-admin@example.com", "password": "Admin123!"},
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    supplier = client.post(
        "/api/v1/suppliers",
        headers=headers,
        json={
            "trade_name": "Moda Textil",
            "legal_name": "Moda Textil S.A.",
            "tax_id": "NIT-123",
            "email": "contacto@modatextil.com",
            "phone": "70000008",
            "address": "Calle Comercio 10",
        },
    )
    assert supplier.status_code == 201
    supplier_id = supplier.json()["id"]
    assert client.post(
        "/api/v1/suppliers",
        headers=headers,
        json={"trade_name": "Otro", "tax_id": "NIT-123"},
    ).status_code == 409
    updated = client.patch(
        f"/api/v1/suppliers/{supplier_id}",
        headers=headers,
        json={"trade_name": "Moda Textil Internacional"},
    )
    assert updated.status_code == 200
    assert updated.json()["trade_name"] == "Moda Textil Internacional"
    assert client.patch(f"/api/v1/suppliers/{supplier_id}/deactivate", headers=headers).status_code == 200
    assert client.get("/api/v1/suppliers?q=Internacional", headers=headers).json()["total"] == 1


def test_admin_can_manage_products_and_variants() -> None:
    with Session(engine) as db:
        admin_role = Role(code="ADMIN", name="Administrador")
        category = Category(name="Camisas")
        size = Size(name="M")
        color = Color(name="Azul", hex_code="#0000FF")
        supplier = Supplier(trade_name="Textiles Demo", tax_id="NIT-PRODUCT-1")
        db.add_all([admin_role, category, size, color, supplier])
        db.flush()
        db.add(
            User(
                role=admin_role,
                first_name="Admin",
                last_name="Products",
                email="products-admin@example.com",
                phone="70000009",
                password_hash=hash_password("Admin123!"),
            )
        )
        db.commit()
        category_id, size_id, color_id, supplier_id = category.id, size.id, color.id, supplier.id

    tokens = client.post(
        "/api/v1/auth/login",
        json={"email": "products-admin@example.com", "password": "Admin123!"},
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    product = client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "category_id": category_id,
            "code": "CAM-001",
            "name": "Camisa Casual",
            "slug": "camisa-casual",
            "description": "Camisa de algodón",
            "price": "199.90",
            "supplier_ids": [supplier_id],
            "variants": [{"size_id": size_id, "color_id": color_id, "sku": "CAM-001-M-AZUL"}],
            "images": [{"image_url": "https://example.com/camisa.jpg", "is_primary": True, "sort_order": 0}],
        },
    )
    assert product.status_code == 201
    product_data = product.json()
    assert product_data["supplier_ids"] == [supplier_id]
    assert product_data["variants"][0]["sku"] == "CAM-001-M-AZUL"
    product_id = product_data["id"]
    assert client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "category_id": category_id,
            "code": "CAM-002",
            "name": "Camisa Formal",
            "slug": "camisa-formal",
            "price": "249.90",
            "variants": [{"size_id": size_id, "color_id": color_id, "sku": "CAM-001-M-AZUL"}],
        },
    ).status_code == 409
    assert client.get(f"/api/v1/products/{product_id}", headers=headers).status_code == 200
    assert client.patch(f"/api/v1/products/{product_id}/deactivate", headers=headers).json()["is_active"] is False


def test_admin_can_manage_minimum_inventory() -> None:
    with Session(engine) as db:
        admin_role = Role(code="ADMIN", name="Administrador")
        category = Category(name="Pantalones")
        size = Size(name="L")
        color = Color(name="Negro", hex_code="#000000")
        city = City(name="Cochabamba")
        db.add_all([admin_role, category, size, color, city])
        db.flush()
        branch = Branch(city_id=city.id, name="Sucursal Norte", address="Av. Norte 20", phone="70000010")
        product = Product(category_id=category.id, code="PAN-001", name="Pantalón Casual", slug="pantalon-casual", price=150)
        db.add_all([branch, product])
        db.flush()
        variant = ProductVariant(product_id=product.id, size_id=size.id, color_id=color.id, sku="PAN-001-L-NEGRO")
        db.add(variant)
        db.flush()
        db.add(
            User(
                role=admin_role,
                first_name="Admin",
                last_name="Inventory",
                email="inventory-admin@example.com",
                phone="70000011",
                password_hash=hash_password("Admin123!"),
            )
        )
        db.commit()
        branch_id, variant_id, product_id = branch.id, variant.id, product.id

    tokens = client.post(
        "/api/v1/auth/login",
        json={"email": "inventory-admin@example.com", "password": "Admin123!"},
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    inventory = client.post(
        "/api/v1/inventory",
        headers=headers,
        json={"branch_id": branch_id, "product_variant_id": variant_id, "stock_quantity": 4},
    )
    assert inventory.status_code == 201
    assert inventory.json()["available"] is True
    inventory_id = inventory.json()["id"]
    assert client.patch(
        f"/api/v1/inventory/{inventory_id}",
        headers=headers,
        json={"stock_quantity": 0},
    ).json()["available"] is False
    assert client.post(
        "/api/v1/inventory",
        headers=headers,
        json={"branch_id": branch_id, "product_variant_id": variant_id, "stock_quantity": 2},
    ).status_code == 409
    assert client.patch(
        f"/api/v1/inventory/{inventory_id}",
        headers=headers,
        json={"stock_quantity": -1},
    ).status_code == 422
    assert client.get(f"/api/v1/inventory?product_id={product_id}", headers=headers).json()["total"] == 1


def test_public_catalog_filters_and_availability() -> None:
    with Session(engine) as db:
        category = Category(name="Vestidos")
        size = Size(name="S")
        color = Color(name="Rojo", hex_code="#FF0000")
        city = City(name="Santa Cruz")
        db.add_all([category, size, color, city])
        db.flush()
        active_branch = Branch(city_id=city.id, name="Sucursal Centro", address="Centro 1", phone="70000012")
        inactive_branch = Branch(city_id=city.id, name="Sucursal Norte", address="Norte 1", phone="70000013", is_active=False)
        product = Product(category_id=category.id, code="VES-001", name="Vestido Rojo", slug="vestido-rojo", price=300)
        db.add_all([active_branch, inactive_branch, product])
        db.flush()
        variant = ProductVariant(product_id=product.id, size_id=size.id, color_id=color.id, sku="VES-001-S-ROJO")
        db.add(variant)
        db.flush()
        db.add_all([
            Inventory(branch_id=active_branch.id, product_variant_id=variant.id, stock_quantity=3),
            Inventory(branch_id=inactive_branch.id, product_variant_id=variant.id, stock_quantity=8),
        ])
        db.commit()
        category_id, size_id, color_id, product_id = category.id, size.id, color.id, product.id

    catalog = client.get(
        f"/api/v1/catalog?q=Vestido&category_id={category_id}&size_id={size_id}&color_id={color_id}",
    )
    assert catalog.status_code == 200
    assert catalog.json()["total"] == 1
    assert catalog.json()["items"][0]["name"] == "Vestido Rojo"

    availability = client.get(
        f"/api/v1/catalog/{product_id}/availability?size_id={size_id}&color_id={color_id}",
    )
    assert availability.status_code == 200
    branches = availability.json()
    assert len(branches) == 1
    assert branches[0]["available"] is True
    assert branches[0]["stock"] == 3
