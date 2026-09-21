import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import get_db  # noqa: E402
from app.core.models import Base, AIRecommendation, Bitacora, Branch, Category, City, Color, Inventory, InventoryMovement, Permission, Product, ProductSupplier, ProductVariant, Promotion, Reservation, Role, RolePermission, Sale, Season, Size, Supplier, User, VirtualFittingSession  # noqa: E402
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


def test_catalog_navigation_returns_categories_and_seasons() -> None:
    with Session(engine) as db:
        category = Category(name="Navigation Category")
        size = Size(name="Navigation M")
        color = Color(name="Navigation Blue", hex_code="#0000FF")
        season = Season(name="Navigation Season")
        db.add_all([category, size, color, season])
        db.flush()
        product = Product(category_id=category.id, season_id=season.id, code="NAV-001", name="Navigation Product", slug="navigation-product", price=50)
        db.add(product)
        db.flush()
        category_id = category.id
        db.add(ProductVariant(product_id=product.id, size_id=size.id, color_id=color.id, sku="NAV-001-M-BLUE"))
        db.commit()
    response = client.get("/api/v1/catalog/navigation")
    assert response.status_code == 200
    assert response.json()["categories"][0]["id"] == category_id


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
    assert client.post("/api/v1/auth/logout", json={}).status_code == 422


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


def test_locations_require_admin_authorization() -> None:
    client_tokens = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Cliente",
            "last_name": "Prueba",
            "email": "locations-client@example.com",
            "phone": "70000014",
            "password": "Secure123!",
        },
    ).json()
    headers = {"Authorization": f"Bearer {client_tokens['access_token']}"}

    assert client.get("/api/v1/cities", headers=headers).status_code == 403
    assert client.post("/api/v1/cities", headers=headers, json={"name": "La Paz"}).status_code == 403
    assert client.get("/api/v1/branches", headers=headers).status_code == 403


def test_admin_can_update_and_filter_locations() -> None:
    with Session(engine) as db:
        admin_role = Role(code="ADMIN", name="Administrador")
        db.add(admin_role)
        db.flush()
        db.add(
            User(
                role=admin_role,
                first_name="Admin",
                last_name="Location Update",
                email="locations-update-admin@example.com",
                phone="70000015",
                password_hash=hash_password("Admin123!"),
            )
        )
        db.commit()

    tokens = client.post(
        "/api/v1/auth/login",
        json={"email": "locations-update-admin@example.com", "password": "Admin123!"},
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    city = client.post("/api/v1/cities", headers=headers, json={"name": "La Paz"}).json()
    branch = client.post(
        "/api/v1/branches",
        headers=headers,
        json={
            "city_id": city["id"],
            "name": "Sucursal Sur",
            "address": "Calle 10",
            "phone": "70000016",
        },
    ).json()

    updated_city = client.patch(
        f"/api/v1/cities/{city['id']}",
        headers=headers,
        json={"name": "La Paz Centro"},
    )
    assert updated_city.status_code == 200
    assert updated_city.json()["name"] == "La Paz Centro"

    updated_branch = client.patch(
        f"/api/v1/branches/{branch['id']}",
        headers=headers,
        json={"address": "Av. Arce 200", "phone": "+591 70000017"},
    )
    assert updated_branch.status_code == 200
    assert updated_branch.json()["address"] == "Av. Arce 200"
    assert updated_branch.json()["phone"] == "+591 70000017"

    branch_page = client.get(
        f"/api/v1/branches?city_id={city['id']}&q=Sur&page_size=10",
        headers=headers,
    )
    assert branch_page.status_code == 200
    assert branch_page.json()["total"] == 1
    assert branch_page.json()["items"][0]["id"] == branch["id"]

    assert client.get(f"/api/v1/cities/{city['id']}", headers=headers).json()["name"] == "La Paz Centro"
    assert client.get(f"/api/v1/branches/{branch['id']}", headers=headers).json()["city_name"] == "La Paz Centro"


def test_location_validations_and_not_found_errors() -> None:
    with Session(engine) as db:
        admin_role = Role(code="ADMIN", name="Administrador")
        db.add(admin_role)
        db.flush()
        db.add(
            User(
                role=admin_role,
                first_name="Admin",
                last_name="Location Validation",
                email="locations-validation-admin@example.com",
                phone="70000018",
                password_hash=hash_password("Admin123!"),
            )
        )
        db.commit()

    tokens = client.post(
        "/api/v1/auth/login",
        json={"email": "locations-validation-admin@example.com", "password": "Admin123!"},
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    inactive_city = client.post("/api/v1/cities", headers=headers, json={"name": "Tarija"}).json()
    assert client.patch(f"/api/v1/cities/{inactive_city['id']}/deactivate", headers=headers).status_code == 200
    assert client.post(
        "/api/v1/branches",
        headers=headers,
        json={"city_id": inactive_city["id"], "name": "Sucursal Centro", "address": "Centro", "phone": "70000019"},
    ).status_code == 400

    city = client.post("/api/v1/cities", headers=headers, json={"name": "Sucre"}).json()
    assert client.post("/api/v1/cities", headers=headers, json={"name": "Sucre"}).status_code == 409
    assert client.patch(f"/api/v1/cities/{city['id']}", headers=headers, json={"name": "Sucre"}).status_code == 200
    assert client.get("/api/v1/cities/9999", headers=headers).status_code == 404
    assert client.get("/api/v1/branches/9999", headers=headers).status_code == 404
    assert client.post(
        "/api/v1/branches",
        headers=headers,
        json={"city_id": city["id"], "name": "Sucursal", "address": "Calle 1", "phone": "abc"},
    ).status_code == 422


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
            "description": "Camisa de algodÃ³n",
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


def test_admin_can_upload_manage_and_delete_product_image() -> None:
    with Session(engine) as db:
        admin_role = Role(code="ADMIN", name="Administrador")
        category = Category(name="Fotos")
        product = Product(category=category, code="IMG-001", name="Producto FotogrÃ¡fico", slug="producto-fotografico", price=100)
        db.add_all([admin_role, product])
        db.flush()
        db.add(User(role=admin_role, first_name="Admin", last_name="Images", email="images-admin@example.com", phone="70000030", password_hash=hash_password("Admin123!")))
        db.commit()
        product_id = product.id

    tokens = client.post("/api/v1/auth/login", json={"email": "images-admin@example.com", "password": "Admin123!"}).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    png_header = b"\x89PNG\r\n\x1a\nminimal-test-image"
    uploaded = client.post(
        f"/api/v1/products/{product_id}/images/upload",
        headers=headers,
        files={"file": ("producto.png", png_header, "image/png")},
        data={"is_primary": "false", "sort_order": "0"},
    )
    assert uploaded.status_code == 201
    image = uploaded.json()["images"][0]
    assert image["image_url"].startswith("/media/products/")
    assert client.get(image["image_url"]).status_code == 200
    promoted = client.patch(f"/api/v1/products/{product_id}/images/{image['id']}", headers=headers, json={"is_primary": True})
    assert promoted.status_code == 200
    assert promoted.json()["images"][0]["is_primary"] is True
    deleted = client.delete(f"/api/v1/products/{product_id}/images/{image['id']}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["images"] == []


def test_admin_can_manage_seasons_collections_and_assign_them_to_products() -> None:
    with Session(engine) as db:
        admin_role = Role(code="ADMIN", name="Administrador")
        category = Category(name="Chaquetas")
        size = Size(name="M")
        color = Color(name="Verde", hex_code="#00FF00")
        db.add_all([admin_role, category, size, color])
        db.flush()
        db.add(
            User(
                role=admin_role,
                first_name="Admin",
                last_name="Seasons",
                email="seasons-admin@example.com",
                phone="70000020",
                password_hash=hash_password("Admin123!"),
            )
        )
        db.commit()
        category_id, size_id, color_id = category.id, size.id, color.id

    tokens = client.post(
        "/api/v1/auth/login",
        json={"email": "seasons-admin@example.com", "password": "Admin123!"},
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    season = client.post(
        "/api/v1/seasons",
        headers=headers,
        json={"name": "OtoÃ±o 2026", "starts_on": "2026-03-01", "ends_on": "2026-05-31"},
    )
    assert season.status_code == 201
    season_id = season.json()["id"]
    assert client.post("/api/v1/seasons", headers=headers, json={"name": "OtoÃ±o 2026"}).status_code == 409

    collection = client.post(
        "/api/v1/collections",
        headers=headers,
        json={"season_id": season_id, "name": "Abrigos", "description": "ColecciÃ³n de abrigo"},
    )
    assert collection.status_code == 201
    collection_id = collection.json()["id"]
    assert collection.json()["season_name"] == "OtoÃ±o 2026"
    assert client.post("/api/v1/collections", headers=headers, json={"season_id": season_id, "name": "Abrigos"}).status_code == 409

    product = client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "category_id": category_id,
            "season_id": season_id,
            "collection_id": collection_id,
            "code": "CHA-001",
            "name": "Chaqueta Verde",
            "slug": "chaqueta-verde",
            "price": "450.00",
            "variants": [{"size_id": size_id, "color_id": color_id, "sku": "CHA-001-M-VERDE"}],
        },
    )
    assert product.status_code == 201
    assert product.json()["season_id"] == season_id
    assert product.json()["collection_id"] == collection_id

    other_season = client.post("/api/v1/seasons", headers=headers, json={"name": "Invierno 2026"}).json()
    assert client.patch(
        f"/api/v1/products/{product.json()['id']}",
        headers=headers,
        json={"season_id": other_season["id"], "collection_id": collection_id},
    ).status_code == 400
    assert client.patch(f"/api/v1/seasons/{season_id}/deactivate", headers=headers, json={}).status_code == 409
    assert client.patch(f"/api/v1/collections/{collection_id}/deactivate", headers=headers, json={}).status_code == 409
    assert client.post(
        "/api/v1/products",
        headers=headers,
        json={"category_id": category_id, "season_id": other_season["id"], "collection_id": collection_id, "code": "CHA-002", "name": "Chaqueta Invierno", "slug": "chaqueta-invierno", "price": "500.00"},
    ).status_code == 400


def test_season_validity_filters_catalog_and_records_update_audit() -> None:
    with Session(engine) as db:
        admin_role = Role(code="ADMIN", name="Administrador")
        category = Category(name="Abrigos")
        size = Size(name="S")
        color = Color(name="Negro", hex_code="#000000")
        db.add_all([admin_role, category, size, color])
        db.flush()
        db.add(User(role=admin_role, first_name="Admin", last_name="Validity", email="validity-admin@example.com", phone="70000021", password_hash=hash_password("Admin123!")))
        db.commit()
        category_id, size_id, color_id = category.id, size.id, color.id

    tokens = client.post("/api/v1/auth/login", json={"email": "validity-admin@example.com", "password": "Admin123!"}).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.post("/api/v1/seasons", headers=headers, json={"name": "   "}).status_code == 422
    past = client.post("/api/v1/seasons", headers=headers, json={"name": "Invierno 2020", "starts_on": "2020-01-01", "ends_on": "2020-12-31"})
    assert past.status_code == 201
    past_id = past.json()["id"]
    collection = client.post("/api/v1/collections", headers=headers, json={"season_id": past_id, "name": "Piezas clÃ¡sicas"}).json()
    product = client.post("/api/v1/products", headers=headers, json={"category_id": category_id, "season_id": past_id, "collection_id": collection["id"], "code": "ABR-PAST", "name": "Abrigo histÃ³rico", "slug": "abrigo-historico", "price": "300.00", "variants": [{"size_id": size_id, "color_id": color_id, "sku": "ABR-PAST-S-NEGRO"}]})
    assert product.status_code == 201
    assert client.get("/api/v1/catalog", params={"q": "ABR-PAST"}).json()["total"] == 0

    future = client.post("/api/v1/seasons", headers=headers, json={"name": "Primavera 2099", "starts_on": "2099-01-01", "ends_on": "2099-12-31"})
    assert future.status_code == 201
    future_id = future.json()["id"]
    updated = client.patch(f"/api/v1/seasons/{future_id}", headers=headers, json={"name": "PRIMAVERA 2099"})
    assert updated.status_code == 200
    with Session(engine) as db:
        audit = db.scalar(select(Bitacora).where(Bitacora.entity_type == "season", Bitacora.entity_id == future_id, Bitacora.action == "UPDATE").order_by(Bitacora.id.desc()))
        assert audit is not None
        assert audit.old_values["name"] == "Primavera 2099"
        assert audit.new_values["name"] == "PRIMAVERA 2099"
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
        product = Product(category_id=category.id, code="PAN-001", name="PantalÃ³n Casual", slug="pantalon-casual", price=150)
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
    with Session(engine) as db:
        movement = db.scalar(select(InventoryMovement).where(InventoryMovement.inventory_id == inventory_id))
        audit = db.scalar(select(Bitacora).where(Bitacora.entity_type == "inventory", Bitacora.entity_id == inventory_id).order_by(Bitacora.id.desc()))
        assert movement is not None
        assert movement.movement_type == "OUT"
        assert movement.stock_before == 4
        assert movement.stock_after == 0
    assert audit is not None
    assert audit.action == "UPDATE"
    audit_page = client.get("/api/v1/audit?entity_type=inventory", headers=headers)
    assert audit_page.status_code == 200
    assert audit_page.json()["total"] >= 1


def test_branch_manager_can_manage_only_assigned_inventory_movements() -> None:
    with Session(engine) as db:
        manager_role = Role(code="BRANCH_MANAGER", name="Encargado de inventario")
        inventory_read = Permission(code="inventory.read", name="Consultar inventario")
        inventory_adjust = Permission(code="inventory.adjust", name="Ajustar inventario")
        admin_role = Role(code="ADMIN", name="Administrador")
        category = Category(name="Movement Category")
        size = Size(name="Movement M")
        color = Color(name="Movement Blue", hex_code="#0000BB")
        city = City(name="Movement City")
        db.add_all([manager_role, inventory_read, inventory_adjust, admin_role, category, size, color, city])
        db.flush()
        db.add_all([
            RolePermission(role_id=manager_role.id, permission_id=inventory_read.id),
            RolePermission(role_id=manager_role.id, permission_id=inventory_adjust.id),
        ])
        branch_one = Branch(city_id=city.id, name="Movement Branch One", address="Movement 1", phone="70000060")
        branch_two = Branch(city_id=city.id, name="Movement Branch Two", address="Movement 2", phone="70000061")
        product = Product(category_id=category.id, code="MOV-001", name="Producto Movimiento", slug="producto-movimiento", price=80)
        manager = User(role=manager_role, first_name="Movement", last_name="Manager", email="movement-manager@example.com", phone="70000062", password_hash=hash_password("Manager123!"))
        admin = User(role=admin_role, first_name="Movement", last_name="Admin", email="movement-admin@example.com", phone="70000063", password_hash=hash_password("Admin123!"))
        manager.branches.append(branch_one)
        db.add_all([branch_one, branch_two, product, manager, admin])
        db.flush()
        variant = ProductVariant(product_id=product.id, size_id=size.id, color_id=color.id, sku="MOV-001-M-BLUE")
        db.add(variant)
        db.flush()
        inventory_one = Inventory(branch_id=branch_one.id, product_variant_id=variant.id, stock_quantity=5)
        inventory_two = Inventory(branch_id=branch_two.id, product_variant_id=variant.id, stock_quantity=5)
        db.add_all([inventory_one, inventory_two])
        db.commit()
        inventory_one_id, inventory_two_id = inventory_one.id, inventory_two.id

    admin_tokens = client.post("/api/v1/auth/login", json={"email": "movement-admin@example.com", "password": "Admin123!"}).json()
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    created = client.post("/api/v1/inventory/movements", headers=admin_headers, json={"inventory_id": inventory_two_id, "movement_type": "IN", "quantity": 2, "reason": "RecepciÃ³n externa"})
    assert created.status_code == 201

    manager_tokens = client.post("/api/v1/auth/login", json={"email": "movement-manager@example.com", "password": "Manager123!"}).json()
    manager_headers = {"Authorization": f"Bearer {manager_tokens['access_token']}"}
    own = client.post("/api/v1/inventory/movements", headers=manager_headers, json={"inventory_id": inventory_one_id, "movement_type": "OUT", "quantity": 2, "reason": "Venta de mostrador"})
    assert own.status_code == 201
    assert own.json()["stock_before"] == 5
    assert own.json()["stock_after"] == 3
    assert own.json()["branch_name"] == "Movement Branch One"
    assert client.post("/api/v1/inventory/movements", headers=manager_headers, json={"inventory_id": inventory_one_id, "movement_type": "OUT", "quantity": 10, "reason": "Salida imposible"}).status_code == 409
    assert client.post("/api/v1/inventory/movements", headers=manager_headers, json={"inventory_id": inventory_one_id, "movement_type": "INVALID", "quantity": 1, "reason": "Tipo invÃ¡lido"}).status_code == 422
    assert client.get("/api/v1/inventory/movements", headers=manager_headers).json()["total"] == 1
    assert client.get(f"/api/v1/inventory/movements?inventory_id={inventory_two_id}", headers=manager_headers).status_code == 403

    with Session(engine) as db:
        movement = db.scalar(select(InventoryMovement).where(InventoryMovement.inventory_id == inventory_one_id))
        audit = db.scalar(select(Bitacora).where(Bitacora.entity_type == "inventory_movement", Bitacora.entity_id == movement.id))
        assert movement is not None
        assert movement.created_by is not None
        assert audit is not None


def test_supplier_portal_only_returns_associated_products() -> None:
    with Session(engine) as db:
        supplier_role = Role(code="SUPPLIER", name="Proveedor")
        portal_permission = Permission(code="suppliers.portal", name="Portal de proveedor")
        supplier = Supplier(trade_name="Proveedor Portal")
        category = Category(name="Portal Category")
        db.add_all([supplier_role, portal_permission, supplier, category])
        db.flush()
        db.add(RolePermission(role_id=supplier_role.id, permission_id=portal_permission.id))
        product = Product(category_id=category.id, code="POR-001", name="Producto Portal", slug="producto-portal", price=50)
        other = Product(category_id=category.id, code="POR-002", name="Producto Ajeno", slug="producto-ajeno", price=60)
        db.add_all([product, other])
        db.flush()
        db.add(ProductSupplier(product_id=product.id, supplier_id=supplier.id))
        db.add(User(role=supplier_role, supplier=supplier, first_name="Portal", last_name="User", email="portal-test@example.com", phone="70000020", password_hash=hash_password("Portal123!")))
        db.commit()

    tokens = client.post("/api/v1/auth/login", json={"email": "portal-test@example.com", "password": "Portal123!"}).json()
    response = client.get("/api/v1/suppliers/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    assert [item["code"] for item in response.json()["products"]] == ["POR-001"]


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


def test_supply_offer_is_variant_scoped_and_supplier_can_update_own_offer() -> None:
    with Session(engine) as db:
        admin_role = Role(code="ADMIN", name="Administrador")
        supplier_role = Role(code="SUPPLIER", name="Proveedor")
        portal_permission = Permission(code="suppliers.portal", name="Portal de proveedor")
        supplier = Supplier(trade_name="Proveedor Supply")
        category = Category(name="Supply Category")
        size = Size(name="M")
        color = Color(name="Azul", hex_code="#0000FF")
        season = Season(name="Supply Season")
        db.add_all([admin_role, supplier_role, portal_permission, supplier, category, size, color, season])
        db.flush()
        db.add(RolePermission(role_id=supplier_role.id, permission_id=portal_permission.id))
        product = Product(category_id=category.id, season_id=season.id, code="SUP-001", name="Supply Product", slug="supply-product", price=100)
        db.add(product)
        db.flush()
        variant = ProductVariant(product_id=product.id, size_id=size.id, color_id=color.id, sku="SUP-001-M-AZUL")
        db.add(variant)
        db.flush()
        db.add(ProductSupplier(product_id=product.id, supplier_id=supplier.id))
        db.add(User(role=admin_role, first_name="Supply", last_name="Admin", email="supply-admin@example.com", phone="70000030", password_hash=hash_password("Admin123!")))
        db.add(User(role=supplier_role, supplier=supplier, first_name="Supply", last_name="Provider", email="supply-provider@example.com", phone="70000031", password_hash=hash_password("Portal123!")))
        db.commit()
        supplier_id, variant_id, season_id = supplier.id, variant.id, season.id

    admin_tokens = client.post("/api/v1/auth/login", json={"email": "supply-admin@example.com", "password": "Admin123!"}).json()
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    created = client.post(f"/api/v1/suppliers/{supplier_id}/offers", headers=admin_headers, json={"product_variant_id": variant_id, "season_id": season_id, "status": "AVAILABLE", "available_quantity": 12})
    assert created.status_code == 201
    offer_id = created.json()["id"]

    supplier_tokens = client.post("/api/v1/auth/login", json={"email": "supply-provider@example.com", "password": "Portal123!"}).json()
    supplier_headers = {"Authorization": f"Bearer {supplier_tokens['access_token']}"}
    offers = client.get("/api/v1/suppliers/me/offers", headers=supplier_headers)
    assert offers.status_code == 200
    assert offers.json()[0]["available_quantity"] == 12
    updated = client.patch(f"/api/v1/suppliers/me/offers/{offer_id}", headers=supplier_headers, json={"available_quantity": 20, "status": "LIMITED"})
    assert updated.status_code == 200
    assert updated.json()["available_quantity"] == 20
    assert client.post(f"/api/v1/suppliers/{supplier_id}/offers", headers=admin_headers, json={"product_variant_id": variant_id, "season_id": season_id, "available_quantity": 4}).status_code == 409


def test_customer_reservation_reserves_and_releases_inventory() -> None:
    with Session(engine) as db:
        client_role = db.scalar(select(Role).where(Role.code == "CLIENT"))
        manager_role = Role(code="BRANCH_MANAGER", name="Encargado de sucursal")
        reservation_read = Permission(code="reservations.read", name="Consultar reservas propias")
        reservation_create = Permission(code="reservations.create", name="Crear reservas propias")
        reservation_cancel = Permission(code="reservations.cancel", name="Cancelar reservas propias")
        reservation_manage = Permission(code="reservations.manage", name="Gestionar reservas de sucursal")
        db.add_all([manager_role, reservation_read, reservation_create, reservation_cancel, reservation_manage])
        db.flush()
        db.add_all([
            RolePermission(role_id=client_role.id, permission_id=reservation_read.id),
            RolePermission(role_id=client_role.id, permission_id=reservation_create.id),
            RolePermission(role_id=client_role.id, permission_id=reservation_cancel.id),
            RolePermission(role_id=manager_role.id, permission_id=reservation_manage.id),
            RolePermission(role_id=manager_role.id, permission_id=reservation_read.id),
        ])
        category = Category(name="Reservas Category")
        size = Size(name="Reserva M")
        color = Color(name="Reserva Azul", hex_code="#0000AA")
        city = City(name="Reserva City")
        db.add_all([category, size, color, city])
        db.flush()
        branch = Branch(city_id=city.id, name="Reserva Branch", address="Reserva 1", phone="70000040")
        product = Product(category_id=category.id, code="RES-001", name="Producto Reservable", slug="producto-reservable", price=125)
        db.add_all([branch, product])
        db.flush()
        variant = ProductVariant(product_id=product.id, size_id=size.id, color_id=color.id, sku="RES-001-M-AZUL")
        db.add(variant)
        db.flush()
        inventory = Inventory(branch_id=branch.id, product_variant_id=variant.id, stock_quantity=3)
        customer = User(role=client_role, first_name="Reserva", last_name="Cliente", email="reservation-client@example.com", phone="70000041", password_hash=hash_password("Client123!"))
        manager = User(role=manager_role, first_name="Reserva", last_name="Manager", email="reservation-manager@example.com", phone="70000042", password_hash=hash_password("Manager123!"))
        manager.branches.append(branch)
        db.add_all([inventory, customer, manager])
        db.commit()
        branch_id, variant_id, inventory_id = branch.id, variant.id, inventory.id

    customer_tokens = client.post("/api/v1/auth/login", json={"email": "reservation-client@example.com", "password": "Client123!"}).json()
    customer_headers = {"Authorization": f"Bearer {customer_tokens['access_token']}"}
    scheduled_for = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    failed = client.post("/api/v1/reservations", headers=customer_headers, json={"branch_id": branch_id, "scheduled_for": scheduled_for, "items": [{"product_variant_id": variant_id, "quantity": 1}, {"product_variant_id": 999999, "quantity": 1}]})
    assert failed.status_code == 400
    with Session(engine) as db:
        assert db.scalar(select(Reservation)) is None
        assert db.get(Inventory, inventory_id).reserved_quantity == 0
    created = client.post("/api/v1/reservations", headers=customer_headers, json={"branch_id": branch_id, "scheduled_for": scheduled_for, "items": [{"product_variant_id": variant_id, "quantity": 2}]})
    assert created.status_code == 201
    reservation_id = created.json()["id"]
    assert created.json()["status"] == "PENDING"
    assert client.get("/api/v1/reservations/mine", headers=customer_headers).json()["total"] == 1
    assert client.get(f"/api/v1/reservations/{reservation_id}", headers=customer_headers).status_code == 200

    with Session(engine) as db:
        saved_inventory = db.get(Inventory, inventory_id)
        assert saved_inventory.reserved_quantity == 2
        assert db.scalar(select(InventoryMovement).where(InventoryMovement.reference_id == reservation_id, InventoryMovement.movement_type == "RESERVE")) is not None
        reserve_movement = db.scalar(select(InventoryMovement).where(InventoryMovement.reference_id == reservation_id, InventoryMovement.movement_type == "RESERVE"))
        assert db.scalar(select(Bitacora).where(Bitacora.entity_type == "inventory_movement", Bitacora.entity_id == reserve_movement.id)) is not None

    manager_tokens = client.post("/api/v1/auth/login", json={"email": "reservation-manager@example.com", "password": "Manager123!"}).json()
    manager_headers = {"Authorization": f"Bearer {manager_tokens['access_token']}"}
    assert client.get("/api/v1/reservations/branches", headers=manager_headers).json()["total"] == 1
    assert client.patch(f"/api/v1/reservations/{reservation_id}/status", headers=manager_headers, json={"status": "PREPARING"}).status_code == 200
    assert client.patch(f"/api/v1/reservations/{reservation_id}/status", headers=manager_headers, json={"status": "READY"}).status_code == 200
    assert client.patch(f"/api/v1/reservations/{reservation_id}/cancel", headers=customer_headers).status_code == 200

    with Session(engine) as db:
        saved_inventory = db.get(Inventory, inventory_id)
        assert saved_inventory.reserved_quantity == 0
        release_movement = db.scalar(select(InventoryMovement).where(InventoryMovement.reference_id == reservation_id, InventoryMovement.movement_type == "RELEASE"))
        assert release_movement is not None
        assert db.scalar(select(Bitacora).where(Bitacora.entity_type == "inventory_movement", Bitacora.entity_id == release_movement.id)) is not None

    attended = client.post("/api/v1/reservations", headers=customer_headers, json={"branch_id": branch_id, "items": [{"product_variant_id": variant_id, "quantity": 1}]})
    assert attended.status_code == 201
    attended_id = attended.json()["id"]
    assert client.patch(f"/api/v1/reservations/{attended_id}/status", headers=manager_headers, json={"status": "PREPARING"}).status_code == 200
    assert client.patch(f"/api/v1/reservations/{attended_id}/status", headers=manager_headers, json={"status": "READY"}).status_code == 200
    assert client.patch(f"/api/v1/reservations/{attended_id}/status", headers=manager_headers, json={"status": "ATTENDED"}).status_code == 200
    assert client.patch(f"/api/v1/reservations/{attended_id}/status", headers=manager_headers, json={"status": "PREPARING"}).status_code == 409
    with Session(engine) as db:
        assert db.get(Inventory, inventory_id).reserved_quantity == 0

    expired = client.post("/api/v1/reservations", headers=customer_headers, json={"branch_id": branch_id, "items": [{"product_variant_id": variant_id, "quantity": 1}]})
    assert expired.status_code == 201
    expired_id = expired.json()["id"]
    with Session(engine) as db:
        db.get(Reservation, expired_id).expires_at = datetime.now(UTC) - timedelta(minutes=1)
        db.commit()
    mine = client.get("/api/v1/reservations/mine", headers=customer_headers)
    assert mine.status_code == 200
    assert next(item for item in mine.json()["items"] if item["id"] == expired_id)["status"] == "EXPIRED"
    with Session(engine) as db:
        assert db.get(Inventory, inventory_id).reserved_quantity == 0
        assert db.scalar(select(InventoryMovement).where(InventoryMovement.reference_id == expired_id, InventoryMovement.movement_type == "RELEASE")) is not None


def test_cart_physical_and_digital_sales_update_inventory() -> None:
    with Session(engine) as db:
        client_role = db.scalar(select(Role).where(Role.code == "CLIENT"))
        cashier_role = Role(code="CASHIER", name="Cajero")
        cart_permission = Permission(code="cart.manage", name="Gestionar carrito")
        electronic_permission = Permission(code="payments.electronic", name="Pagos electronicos")
        sales_read = Permission(code="sales.read", name="Consultar ventas")
        sales_create = Permission(code="sales.create", name="Crear ventas")
        cash_permission = Permission(code="payments.cash", name="Pagos en caja")
        db.add_all([cashier_role, cart_permission, electronic_permission, sales_read, sales_create, cash_permission])
        db.flush()
        db.add_all([
            RolePermission(role_id=client_role.id, permission_id=cart_permission.id),
            RolePermission(role_id=client_role.id, permission_id=electronic_permission.id),
            RolePermission(role_id=client_role.id, permission_id=sales_read.id),
            RolePermission(role_id=cashier_role.id, permission_id=sales_read.id),
            RolePermission(role_id=cashier_role.id, permission_id=sales_create.id),
            RolePermission(role_id=cashier_role.id, permission_id=cash_permission.id),
        ])
        category = Category(name="Commerce Category")
        size = Size(name="Commerce M")
        color = Color(name="Commerce Black", hex_code="#111111")
        city = City(name="Commerce City")
        db.add_all([category, size, color, city])
        db.flush()
        branch = Branch(city_id=city.id, name="Commerce Branch", address="Commerce 1", phone="70000050")
        product = Product(category_id=category.id, code="COM-001", name="Producto Comercial", slug="producto-comercial", price=100)
        db.add_all([branch, product])
        db.flush()
        variant = ProductVariant(product_id=product.id, size_id=size.id, color_id=color.id, sku="COM-001-M-BLACK")
        db.add(variant)
        db.flush()
        db.add(Inventory(branch_id=branch.id, product_variant_id=variant.id, stock_quantity=5))
        customer = User(role=client_role, first_name="Commerce", last_name="Client", email="commerce-client@example.com", phone="70000051", password_hash=hash_password("Client123!"))
        cashier = User(role=cashier_role, first_name="Commerce", last_name="Cashier", email="commerce-cashier@example.com", phone="70000052", password_hash=hash_password("Cashier123!"))
        cashier.branches.append(branch)
        db.add_all([customer, cashier])
        db.commit()
        branch_id, variant_id = branch.id, variant.id

    customer_tokens = client.post("/api/v1/auth/login", json={"email": "commerce-client@example.com", "password": "Client123!"}).json()
    customer_headers = {"Authorization": f"Bearer {customer_tokens['access_token']}"}
    cart_response = client.post("/api/v1/cart/items", headers=customer_headers, json={"product_variant_id": variant_id, "quantity": 2})
    assert cart_response.status_code == 200
    assert cart_response.json()["subtotal"] == "200.00"

    cashier_tokens = client.post("/api/v1/auth/login", json={"email": "commerce-cashier@example.com", "password": "Cashier123!"}).json()
    cashier_headers = {"Authorization": f"Bearer {cashier_tokens['access_token']}"}
    physical = client.post("/api/v1/sales/physical", headers=cashier_headers, json={"branch_id": branch_id, "items": [{"product_variant_id": variant_id, "quantity": 1}]})
    assert physical.status_code == 201
    physical_id = physical.json()["id"]
    paid = client.post(f"/api/v1/sales/{physical_id}/cash-payment", headers=cashier_headers, json={"method": "CASH", "amount": "120"})
    assert paid.status_code == 200
    assert paid.json()["status"] == "CONFIRMED"
    assert paid.json()["payments"][0]["amount"] == "100.00"
    assert paid.json()["payments"][0]["received_amount"] == "120.00"
    assert paid.json()["payments"][0]["change_amount"] == "20.00"

    digital = client.post("/api/v1/purchases/digital", headers=customer_headers, json={"branch_id": branch_id})
    assert digital.status_code == 201
    sale_id = digital.json()["id"]
    payment = client.post("/api/v1/payments/electronic", headers=customer_headers, json={"sale_id": sale_id, "idempotency_key": "commerce-payment-001", "method": "CARD"})
    assert payment.status_code == 201
    assert client.post("/api/v1/payments/electronic", headers=customer_headers, json={"sale_id": sale_id, "idempotency_key": "commerce-payment-001", "method": "CARD"}).json()["id"] == payment.json()["id"]

    second_digital = client.post("/api/v1/purchases/digital", headers=customer_headers, json={"branch_id": branch_id})
    assert second_digital.status_code == 201
    idempotency_conflict = client.post("/api/v1/payments/electronic", headers=customer_headers, json={"sale_id": second_digital.json()["id"], "idempotency_key": "commerce-payment-001", "method": "CARD"})
    assert idempotency_conflict.status_code == 409
    rejected_payment = client.post("/api/v1/payments/electronic", headers=customer_headers, json={"sale_id": second_digital.json()["id"], "idempotency_key": "commerce-payment-002", "method": "CARD"})
    assert rejected_payment.status_code == 201
    rejected = client.post("/api/v1/payments/electronic/notification", headers={"X-Sandbox-Signature": "sandbox-webhook-secret"}, json={"transaction_reference": rejected_payment.json()["transaction_reference"], "status": "REJECTED", "amount": "200"})
    assert rejected.status_code == 200
    terminal_reversal = client.post("/api/v1/payments/electronic/notification", headers={"X-Sandbox-Signature": "sandbox-webhook-secret"}, json={"transaction_reference": rejected_payment.json()["transaction_reference"], "status": "APPROVED", "amount": "200"})
    assert terminal_reversal.status_code == 409

    unauthenticated = client.post("/api/v1/payments/electronic/notification", json={"transaction_reference": payment.json()["transaction_reference"], "status": "APPROVED", "amount": "200"})
    assert unauthenticated.status_code == 401
    approved = client.post("/api/v1/payments/electronic/notification", headers={"X-Sandbox-Signature": "sandbox-webhook-secret"}, json={"transaction_reference": payment.json()["transaction_reference"], "status": "APPROVED", "amount": "200"})
    assert approved.status_code == 200
    with Session(engine) as db:
        inventory = db.scalar(select(Inventory).where(Inventory.branch_id == branch_id, Inventory.product_variant_id == variant_id))
        assert inventory.stock_quantity == 2
        assert db.scalar(select(Sale).where(Sale.id == sale_id)).status == "CONFIRMED"
        sale_movements = db.scalars(select(InventoryMovement).where(InventoryMovement.inventory_id == inventory.id, InventoryMovement.movement_type == "SALE")).all()
        assert len(sale_movements) == 2
        assert all(db.scalar(select(Bitacora).where(Bitacora.entity_type == "inventory_movement", Bitacora.entity_id == movement.id)) is not None for movement in sale_movements)


def test_cycle3_history_promotions_reports_recommendations_and_virtual_fitting() -> None:
    with Session(engine) as db:
        client_role = db.scalar(select(Role).where(Role.code == "CLIENT"))
        admin_role = Role(code="ADMIN", name="Administrador")
        cashier_role = Role(code="CASHIER", name="Cajero Ciclo 3")
        permissions = {
            code: Permission(code=code, name=name)
            for code, name in {
                "cart.manage": "Gestionar carrito",
                "sales.read": "Consultar ventas",
                "sales.create": "Crear ventas",
                "payments.cash": "Pagos en caja",
                "payments.electronic": "Pagos electrÃ³nicos",
                "promotions.manage": "Gestionar promociones",
                "reports.read": "Consultar reportes",
                "recommendations.read": "Consultar recomendaciones",
                "virtual_fitting.use": "Usar vestidor virtual",
            }.items()
        }
        db.add_all([admin_role, cashier_role, *permissions.values()])
        db.flush()
        for code in ("cart.manage", "sales.read", "payments.electronic", "recommendations.read", "virtual_fitting.use"):
            db.add(RolePermission(role_id=client_role.id, permission_id=permissions[code].id))
        for code in ("sales.read", "sales.create", "payments.cash"):
            db.add(RolePermission(role_id=cashier_role.id, permission_id=permissions[code].id))
        category = Category(name="Cycle 3 Category")
        other_category = Category(name="Cycle 3 Other Category")
        size = Size(name="Cycle 3 M")
        color = Color(name="Cycle 3 Blue", hex_code="#0011FF")
        city = City(name="Cycle 3 City")
        db.add_all([category, other_category, size, color, city])
        db.flush()
        branch = Branch(city_id=city.id, name="Cycle 3 Branch", address="Cycle 3", phone="70000300")
        product = Product(category_id=category.id, code="C3-001", name="Camisa Ciclo 3", slug="camisa-ciclo-3", price=Decimal("100.00"))
        recommended_product = Product(category_id=category.id, code="C3-002", name="Chaqueta Recomendada", slug="chaqueta-recomendada", price=Decimal("180.00"))
        unavailable_product = Product(category_id=other_category.id, code="C3-003", name="Sin Stock", slug="sin-stock", price=Decimal("90.00"))
        db.add_all([branch, product, recommended_product, unavailable_product])
        db.flush()
        variant = ProductVariant(product_id=product.id, size_id=size.id, color_id=color.id, sku="C3-001-M-BLUE")
        recommended_variant = ProductVariant(product_id=recommended_product.id, size_id=size.id, color_id=color.id, sku="C3-002-M-BLUE")
        unavailable_variant = ProductVariant(product_id=unavailable_product.id, size_id=size.id, color_id=color.id, sku="C3-003-M-BLUE")
        db.add_all([variant, recommended_variant, unavailable_variant])
        db.flush()
        db.add_all([
            Inventory(branch_id=branch.id, product_variant_id=variant.id, stock_quantity=8),
            Inventory(branch_id=branch.id, product_variant_id=recommended_variant.id, stock_quantity=7),
            Inventory(branch_id=branch.id, product_variant_id=unavailable_variant.id, stock_quantity=0),
        ])
        customer = User(role=client_role, first_name="Cycle", last_name="Client", email="cycle3-client@example.com", phone="70000301", password_hash=hash_password("Client123!"))
        other_customer = User(role=client_role, first_name="Other", last_name="Client", email="cycle3-other@example.com", phone="70000302", password_hash=hash_password("Client123!"))
        cashier = User(role=cashier_role, first_name="Cycle", last_name="Cashier", email="cycle3-cashier@example.com", phone="70000303", password_hash=hash_password("Cashier123!"))
        admin = User(role=admin_role, first_name="Cycle", last_name="Admin", email="cycle3-admin@example.com", phone="70000304", password_hash=hash_password("Admin123!"))
        cashier.branches.append(branch)
        db.add_all([customer, other_customer, cashier, admin])
        db.commit()
        branch_id, product_id, recommended_product_id, unavailable_product_id, variant_id, recommended_variant_id = branch.id, product.id, recommended_product.id, unavailable_product.id, variant.id, recommended_variant.id

    admin_headers = {"Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'email': 'cycle3-admin@example.com', 'password': 'Admin123!'}).json()['access_token']}"}
    customer_headers = {"Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'email': 'cycle3-client@example.com', 'password': 'Client123!'}).json()['access_token']}"}
    other_headers = {"Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'email': 'cycle3-other@example.com', 'password': 'Client123!'}).json()['access_token']}"}
    cashier_headers = {"Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'email': 'cycle3-cashier@example.com', 'password': 'Cashier123!'}).json()['access_token']}"}

    promotion = client.post("/api/v1/promotions", headers=admin_headers, json={"name": "Promo Ciclo 3", "discount_type": "PERCENT", "discount_value": "10", "starts_at": (datetime.now(UTC) - timedelta(days=1)).isoformat(), "ends_at": (datetime.now(UTC) + timedelta(days=2)).isoformat()})
    assert promotion.status_code == 201
    promotion_id = promotion.json()["id"]
    assert client.post(f"/api/v1/promotions/{promotion_id}/products", headers=admin_headers, json={"product_ids": [product_id]}).status_code == 200
    assert client.get("/api/v1/promotions", headers=customer_headers).status_code == 403

    cart = client.post("/api/v1/cart/items", headers=customer_headers, json={"product_variant_id": variant_id, "quantity": 2})
    assert cart.status_code == 200
    assert cart.json()["subtotal"] == "200.00"
    assert cart.json()["discount"] == "20.00"
    assert cart.json()["total"] == "180.00"
    digital = client.post("/api/v1/purchases/digital", headers=customer_headers, json={"branch_id": branch_id})
    assert digital.status_code == 201
    assert digital.json()["discount"] == "20.00"
    assert digital.json()["total"] == "180.00"
    sale_id = digital.json()["id"]
    payment = client.post("/api/v1/payments/electronic", headers=customer_headers, json={"sale_id": sale_id, "idempotency_key": "cycle3-payment-001", "method": "CARD"})
    assert payment.status_code == 201
    assert client.post("/api/v1/payments/electronic/notification", headers={"X-Sandbox-Signature": "sandbox-webhook-secret"}, json={"transaction_reference": payment.json()["transaction_reference"], "status": "APPROVED", "amount": "180.00"}).status_code == 200

    history = client.get("/api/v1/purchases/mine", headers=customer_headers)
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["id"] == sale_id
    assert client.get(f"/api/v1/purchases/mine/{sale_id}", headers=other_headers).status_code == 404

    physical = client.post("/api/v1/sales/physical", headers=cashier_headers, json={"branch_id": branch_id, "items": [{"product_variant_id": recommended_variant_id, "quantity": 2}]})
    assert physical.status_code == 201
    assert client.post(f"/api/v1/sales/{physical.json()['id']}/cash-payment", headers=cashier_headers, json={"method": "CASH", "amount": "360"}).status_code == 200
    dashboard = client.get("/api/v1/reports/dashboard", headers=admin_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["revenue"]["sales_count"] == 2
    assert any(item["product_id"] == recommended_product_id for item in dashboard.json()["top_products"])
    assert client.get("/api/v1/reports/dashboard", headers=customer_headers).status_code == 403

    recommendations = client.get("/api/v1/recommendations/mine", headers=customer_headers)
    assert recommendations.status_code == 200
    recommended_ids = [item["product_id"] for item in recommendations.json()["items"]]
    assert recommended_product_id in recommended_ids
    assert unavailable_product_id not in recommended_ids
    assert all(item["reason"] for item in recommendations.json()["items"])

    session = client.post("/api/v1/virtual-fitting/sessions", headers=customer_headers, json={"product_id": recommended_product_id, "device_info": "test-device"})
    assert session.status_code == 201
    assert session.json()["status"] == "STARTED"
    assert client.patch(f"/api/v1/virtual-fitting/sessions/{session.json()['id']}/finish", headers=other_headers).status_code == 403
    finished = client.patch(f"/api/v1/virtual-fitting/sessions/{session.json()['id']}/finish", headers=customer_headers)
    assert finished.status_code == 200
    assert finished.json()["status"] == "FINISHED"
    assert client.get("/api/v1/virtual-fitting/sessions/mine", headers=customer_headers).json()["items"][0]["id"] == session.json()["id"]
    with Session(engine) as db:
        assert db.scalar(select(Promotion).where(Promotion.id == promotion_id)) is not None
        assert db.scalar(select(AIRecommendation).where(AIRecommendation.customer_id.is_not(None))) is not None
        assert db.scalar(select(VirtualFittingSession).where(VirtualFittingSession.id == session.json()["id"])).status == "FINISHED"
