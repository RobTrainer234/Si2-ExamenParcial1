from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.models import Role, User
from app.core.security import hash_password

ROLES = {
    "ADMIN": "Administrador",
    "CLIENT": "Cliente",
    "BRANCH_MANAGER": "Encargado de sucursal",
    "CASHIER": "Cajero",
    "SUPPLIER": "Proveedor",
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
