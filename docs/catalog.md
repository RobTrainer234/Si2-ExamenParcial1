# Catálogo público del Ciclo 1

El catálogo no requiere autenticación y filtra en PostgreSQL antes de

```text
GET /api/v1/catalog
GET /api/v1/catalog/{product_id}
GET /api/v1/catalog/{product_id}/availability?size_id={id}&color_id={id}
```

Filtros disponibles en el listado:

- `q`
- `category_id`
- `size_id`
- `color_id`
- `branch_id` para sucursal con stock positivo
- `page` y `page_size`

La disponibilidad solo expone sucursales y ciudades activas. No devuelve
proveedores ni información interna del inventario.
