from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.models import Permission, Role, User
from app.core.security import hash_password

ROLES = {
    "ADMIN": "Administrador",
    "CLIENT": "Cliente",
    "BRANCH_MANAGER": "Encargado de sucursal",
    "CASHIER": "Cajero",
    "SUPPLIER": "Proveedor",
}

PERMISSIONS = {
    "catalog.read": "Consultar catálogo",
    "catalog.availability": "Consultar disponibilidad",
    "users.manage": "Gestionar usuarios y roles",
    "locations.manage": "Gestionar ciudades y sucursales",
    "masters.manage": "Gestionar catálogos maestros",
    "suppliers.manage": "Gestionar proveedores",
    "suppliers.portal": "Consultar portal de proveedor",
    "seasons.manage": "Gestionar temporadas y colecciones",
    "products.manage": "Gestionar productos",
    "products.publish": "Publicar productos",
    "inventory.read": "Consultar inventario",
    "inventory.adjust": "Ajustar inventario",
}

ROLE_PERMISSIONS = {
    "ADMIN": set(PERMISSIONS),
    "CLIENT": {"catalog.read", "catalog.availability"},
    "BRANCH_MANAGER": {"catalog.read", "catalog.availability", "inventory.read", "inventory.adjust"},
    "CASHIER": {"catalog.read", "catalog.availability", "inventory.read"},
    "SUPPLIER": {"catalog.read", "suppliers.portal"},
}


def seed_development_data() -> None:
    if settings.app_env != "development":
        raise RuntimeError("El seed de desarrollo solo puede ejecutarse con APP_ENV=development")
    if not settings.seed_admin_password:
        raise RuntimeError("SEED_ADMIN_PASSWORD es obligatorio para ejecutar el seed")

    with SessionLocal.begin() as db:
        roles: dict[str, Role] = {}
        for code, name in ROLES.items():
            role = db.scalar(select(Role).where(Role.code == code))
            if role is None:
                role = Role(code=code, name=name)
                db.add(role)
                db.flush()
            roles[code] = role

        permissions: dict[str, Permission] = {}
        for code, name in PERMISSIONS.items():
            permission = db.scalar(select(Permission).where(Permission.code == code))
            if permission is None:
                permission = Permission(code=code, name=name)
                db.add(permission)
                db.flush()
            permissions[code] = permission
        for role_code, permission_codes in ROLE_PERMISSIONS.items():
            roles[role_code].permissions = [permissions[code] for code in permission_codes]

        admin = db.scalar(select(User).where(User.email == settings.seed_admin_email.lower()))
        if admin is None:
            db.add(
                User(
                    role=roles["ADMIN"],
                    first_name="Administrador",
                    last_name="FashionStore",
                    email=settings.seed_admin_email.lower(),
                    phone="000000000",
                    password_hash=hash_password(settings.seed_admin_password),
                )
            )


if __name__ == "__main__":
    seed_development_data()
    print("Development seed completed")
