import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import get_db  # noqa: E402
from app.core.models import Base, Bitacora, Branch, Category, City, Color, Inventory, InventoryMovement, Permission, Product, ProductSupplier, ProductVariant, Role, RolePermission, Season, Size, Supplier, User  # noqa: E402
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


def test_admin_can_upload_manage_and_delete_product_image() -> None:
    with Session(engine) as db:
        admin_role = Role(code="ADMIN", name="Administrador")
        category = Category(name="Fotos")
        product = Product(category=category, code="IMG-001", name="Producto Fotográfico", slug="producto-fotografico", price=100)
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
        json={"name": "Otoño 2026", "starts_on": "2026-03-01", "ends_on": "2026-05-31"},
    )
    assert season.status_code == 201
    season_id = season.json()["id"]
    assert client.post("/api/v1/seasons", headers=headers, json={"name": "Otoño 2026"}).status_code == 409

    collection = client.post(
        "/api/v1/collections",
        headers=headers,
        json={"season_id": season_id, "name": "Abrigos", "description": "Colección de abrigo"},
    )
    assert collection.status_code == 201
    collection_id = collection.json()["id"]
    assert collection.json()["season_name"] == "Otoño 2026"
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
    assert client.post(
        "/api/v1/products",
        headers=headers,
        json={"category_id": category_id, "season_id": other_season["id"], "collection_id": collection_id, "code": "CHA-002", "name": "Chaqueta Invierno", "slug": "chaqueta-invierno", "price": "500.00"},
    ).status_code == 400


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
