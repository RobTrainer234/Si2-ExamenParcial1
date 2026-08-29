# Scripts y datos iniciales

Las migraciones se ejecutan con Alembic desde `backend/migrations`.

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
