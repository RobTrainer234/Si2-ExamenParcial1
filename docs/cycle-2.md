# Implementacion del Ciclo 2

El Ciclo 2 incorpora operaciones comerciales sobre la base del catalogo y la
autenticacion del Ciclo 1. La implementacion se desarrolla por incrementos y
mantiene el flujo `Router -> Service -> PostgreSQL`.

## Estado actual

| Caso de uso | Estado | Alcance implementado |
| --- | --- | --- |
| CU18 Inventario y movimientos | En implementacion | Stock fisico, stock reservado, movimientos manuales y trazabilidad |
| CU10 Gestionar reservas | Implementado backend | Reservas multiples, disponibilidad, consulta, cancelacion y liberacion |
| CU11 Atencion de reservas | Implementado | Bandeja web por sucursal y transiciones de preparacion/atencion |
| CU19 Temporadas y colecciones | Implementado backend | CRUD, vigencia, auditoria y proteccion de estructuras en uso |
| CU13 Carrito | Implementado | Carrito activo en API, web y movil, con cantidades y validacion de disponibilidad |
| CU14 Compra digital | Implementado | Checkout por sucursal en API, web y movil, con confirmacion tras pago sandbox |
| CU15 Venta presencial | Implementado | API y pantalla web de caja por sucursal, con descuento de inventario |
| CU16 Pago en caja | Implementado | API y pantalla web de caja para efectivo, tarjeta o QR con validacion de monto |
| CU17 Pago electronico | Implementado | Sandbox, notificacion, estados e idempotencia |

## Reglas transversales

- El stock disponible es `stock_quantity - reserved_quantity`.
- Las operaciones que reservan o liberan stock se ejecutan dentro de una
  transaccion.
- No se permite que una salida deje stock disponible negativo.
- Los encargados solo pueden operar sobre sucursales asignadas.
- Las reservas terminales son `ATTENDED`, `CANCELLED` y `EXPIRED`.
- Los cambios relevantes se registran en `bitacora`.

## Endpoints

```text
GET   /api/v1/inventory
POST  /api/v1/inventory
PATCH /api/v1/inventory/{inventory_id}
GET   /api/v1/inventory/movements
POST  /api/v1/inventory/movements

POST  /api/v1/reservations
GET   /api/v1/reservations/mine
GET   /api/v1/reservations/branch
GET   /api/v1/reservations/{reservation_id}
PATCH /api/v1/reservations/{reservation_id}/cancel
PATCH /api/v1/reservations/{reservation_id}/status
GET    /api/v1/cart
POST   /api/v1/cart/items
PATCH  /api/v1/cart/items/{item_id}
DELETE /api/v1/cart/items/{item_id}
DELETE /api/v1/cart
POST   /api/v1/sales/physical
POST   /api/v1/sales/{sale_id}/cash-payment
GET    /api/v1/sales/{sale_id}
POST   /api/v1/purchases/digital
POST   /api/v1/payments/electronic
POST   /api/v1/payments/electronic/notification
```

Las temporadas y colecciones se administran mediante los endpoints existentes
`/api/v1/seasons` y `/api/v1/collections`.

La aplicacion movil permite seleccionar una variante, consultar las sucursales
disponibles, crear reservas y gestionar el carrito con checkout sandbox. La
pantalla web `/pos` permite al personal autorizado registrar ventas presenciales
y confirmar pagos en caja.
