# Inventario mínimo del Ciclo 1

El módulo `/api/v1/inventory` mantiene únicamente el stock actual por
`branch_id + product_variant_id` y requiere `ADMIN`.

No implementa movimientos, reservas, ventas, devoluciones ni auditoría de
inventario. Solo se permiten referencias a sucursales, productos y variantes
activas, y la base de datos impide cantidades negativas y combinaciones
duplicadas.
