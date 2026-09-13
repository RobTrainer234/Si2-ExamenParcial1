# Inventario del Ciclo 2

El módulo `/api/v1/inventory` mantiene el stock físico y reservado por
`branch_id + product_variant_id`. El stock disponible se calcula como
`stock_quantity - reserved_quantity`. Los administradores pueden gestionarlo
globalmente; los encargados de sucursal solo pueden consultar y ajustar las
sucursales asignadas, mientras que los cajeros tienen acceso de lectura.

Cada ajuste de cantidad genera un movimiento `IN` o `OUT` con stock anterior,
stock nuevo, usuario y motivo. Las reservas generan `RESERVE` y las
cancelaciones o vencimientos generan `RELEASE`. Los movimientos derivados
conservan el tipo e identificador de la entidad que los originó.

Endpoints adicionales:

```text
POST /api/v1/inventory/movements
GET  /api/v1/inventory/movements
```
