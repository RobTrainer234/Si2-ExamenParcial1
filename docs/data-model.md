# Modelo de datos del Ciclo 1

La migración `20260829_0001_initial_schema` crea las siguientes entidades:

- `roles` y `users` para identidad y autorización.
- `cities` y `branches` para la estructura física.
- `categories`, `sizes` y `colors` como maestros administrables.
- `suppliers`, `products` y `product_suppliers` para el catálogo comercial.
- `product_variants` para combinaciones únicas de producto, talla y color.
- `product_images` para URLs de imágenes extensibles a almacenamiento externo.
- `inventory` para stock mínimo por sucursal y variante.

Restricciones importantes:

- `users.email`, `products.code`, `products.slug` y `product_variants.sku` son únicos.
- Una variante no puede repetir producto, talla y color.
- Un registro de inventario no puede repetir sucursal y variante.
- `inventory.stock_quantity` no puede ser negativo.
- Las relaciones maestras usan `RESTRICT`; los hijos de productos usan `CASCADE`.

Aplicar el esquema con:

```bash
cd backend
alembic upgrade head
```
