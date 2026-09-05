# Scripts y datos iniciales

Las migraciones se ejecutan con Alembic desde `backend/migrations`.

## Inspeccionar el modelo completo

El script `backend/scripts/inspeccionar_modelo_bd.py` muestra las clases
SQLAlchemy, tablas, columnas, restricciones, indices, relaciones y el DDL de
PostgreSQL de los tres ciclos.

Ejecutar desde `backend/`:

```bash
python scripts/inspeccionar_modelo_bd.py
python scripts/inspeccionar_modelo_bd.py --salida ../docs/esquema_generado.sql
```

El segundo comando genera un archivo SQL para revisión documental. El archivo
se puede regenerar después de cualquier cambio en `backend/app/core/models.py`.

## Seed de desarrollo

El seed disponible está en `backend/app/core/seed.py`. Crea los cinco roles base
y un administrador con `SEED_ADMIN_EMAIL` y `SEED_ADMIN_PASSWORD`.

Ejecutar con Docker:

```bash
docker compose exec backend python -m app.core.seed
```

El seed exige `APP_ENV=development`, es idempotente y no debe ejecutarse en
produccion. Actualmente no se cargan productos, proveedores ni inventario de
ejemplo automaticamente.
