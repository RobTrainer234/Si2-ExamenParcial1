"""Renombra las sucursales de los tenants demo con ciudades bolivianas (un departamento por empresa)
y crea sucursales con stock para tenants que no tengan ninguna. Idempotente.

Uso (dentro del contenedor backend):  python scripts/rename_branches_bolivia.py
"""
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.models import Branch, City, Inventory, ProductVariant, Tenant

# tenant_id -> lista de (ciudad, nombre, dirección, teléfono)
PLAN = {
    2: [  # Boutique Aurora — Dpto. La Paz
        ("La Paz", "Aurora La Paz", "Av. 6 de Agosto 2450, Sopocachi", "71001001"),
        ("El Alto", "Aurora El Alto", "Av. Juan Pablo II 1180, Ciudad Satélite", "71001002"),
    ],
    3: [  # Moda Boreal — Dpto. Tarija
        ("Tarija", "Boreal Tarija", "Calle La Madrid 345, Zona Central", "72001001"),
        ("Yacuiba", "Boreal Yacuiba", "Av. San Martín 820", "72001002"),
    ],
    4: [  # Captura CU-01 — Dpto. Potosí
        ("Potosí", "Tienda Potosí", "Calle Bolívar 760, Casco Histórico", "73001001"),
        ("Uyuni", "Tienda Uyuni", "Av. Ferroviaria 215", "73001002"),
    ],
    6: [  # Stripe Smoke Test — Dpto. Oruro
        ("Oruro", "Tienda Oruro", "Calle Adolfo Mier 540, Zona Central", "74001001"),
        ("Challapata", "Tienda Challapata", "Av. Litoral 130", "74001002"),
    ],
}
SOURCE_BRANCH_IDS = (4, 5)  # FashionStore Centro / Norte (tenant 1) como referencia de stock


def get_city(db, name: str) -> City:
    city = db.scalar(select(City).where(City.name == name))
    if city is None:
        city = City(name=name, is_active=True)
        db.add(city)
        db.flush()
    return city


def seed_inventory(db, tenant_id: int, branch: Branch, source_branch_id: int) -> int:
    """Copia cantidades de la sucursal origen emparejando variantes por SKU."""
    sku_to_variant = {v.sku: v.id for v in db.scalars(select(ProductVariant).where(ProductVariant.tenant_id == tenant_id))}
    count = 0
    rows = db.execute(
        select(ProductVariant.sku, Inventory.stock_quantity)
        .join(Inventory, Inventory.product_variant_id == ProductVariant.id)
        .where(Inventory.branch_id == source_branch_id)
    ).all()
    for sku, qty in rows:
        vid = sku_to_variant.get(sku)
        if vid is None:
            continue
        db.add(Inventory(tenant_id=tenant_id, branch_id=branch.id, product_variant_id=vid, stock_quantity=max(qty, 0), reserved_quantity=0))
        count += 1
    return count


def main() -> None:
    db = SessionLocal()
    try:
        for tenant_id, specs in PLAN.items():
            tenant = db.get(Tenant, tenant_id)
            if tenant is None:
                continue
            existing = db.scalars(select(Branch).where(Branch.tenant_id == tenant_id).order_by(Branch.id)).all()
            for i, (city_name, name, address, phone) in enumerate(specs):
                city = get_city(db, city_name)
                if i < len(existing):
                    b = existing[i]
                    old = b.name
                    b.name, b.city_id, b.address, b.phone = name, city.id, address, phone
                    print(f"[renombrada] T{tenant_id} '{old}' -> '{name}' ({city_name})")
                else:
                    b = Branch(tenant_id=tenant_id, city_id=city.id, name=name, address=address, phone=phone, is_active=True)
                    db.add(b)
                    db.flush()
                    inv = seed_inventory(db, tenant_id, b, SOURCE_BRANCH_IDS[i % len(SOURCE_BRANCH_IDS)])
                    print(f"[creada] T{tenant_id} '{name}' ({city_name}) con {inv} registros de inventario")
        db.commit()
        print("Listo.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
