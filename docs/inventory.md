# Inventario mínimo del Ciclo 1

El módulo `/api/v1/inventory` mantiene el stock actual por
`branch_id + product_variant_id`. Los administradores pueden gestionarlo
globalmente; los encargados de sucursal solo pueden consultar y ajustar las
sucursales asignadas, mientras que los cajeros tienen acceso de lectura.

Cada ajuste de cantidad genera un movimiento `IN` o `OUT` con stock anterior,
stock nuevo, usuario y motivo. También se registra en la bitácora transversal.
No incluye reservas, ventas, devoluciones ni transferencias entre sucursales.
