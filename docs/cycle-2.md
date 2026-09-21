# Implementación del Ciclo 2

El Ciclo 2 incorpora operaciones comerciales sobre la base del catálogo y la autenticación del Ciclo 1. La implementación mantiene el flujo `Router -> Service -> PostgreSQL` y cierra las brechas detectadas antes de iniciar el Ciclo 3.

## Estado actualizado

| Caso de uso | Estado | Alcance implementado |
| --- | --- | --- |
| CU18 Inventario y movimientos | Completo funcional con verificación automatizada | Stock físico, stock reservado, movimientos manuales y derivados, auditoría, rollback, permisos por sucursal e historial. La concurrencia real PostgreSQL queda recomendada como prueba de despliegue, no como brecha funcional local. |
| CU10 Gestionar reservas | Completo | Reservas múltiples de prendas para una visita programada y prueba en sucursal; disponibilidad, consulta, cancelación, liberación, expiración y rollback ante errores. La reserva no constituye una compra. |
| CU11 Atención de reservas | Completo | Bandeja web por sucursal, preparación de las prendas y transiciones válidas de preparación, lista y atención. |
| CU19 Temporadas y colecciones | Completo | CRUD web, vigencia en catálogo/ventas/reservas, auditoría y protección de estructuras en uso. |
| CU13 Carrito | Completo | Carrito activo en API, web y móvil, con cantidades y validación de disponibilidad. |
| CU14 Compra digital | Completo en modo sandbox académico | Checkout por sucursal en API, web y móvil, venta pendiente y confirmación después de pago aprobado. |
| CU15 Venta presencial | Completo | API y pantalla web de caja por sucursal, con descuento de inventario al confirmar pago. |
| CU16 Pago en caja | Completo | API y pantalla web para efectivo, tarjeta o QR; valida monto/referencia y persiste monto recibido/cambio para efectivo. |
| CU17 Pago electrónico | Completo para sandbox académico | Pago sandbox con idempotencia vinculada a la venta, notificación autenticada por firma sandbox y estados terminales protegidos. Stripe real queda fuera del cierre y pendiente de credenciales/API reales. |

## Reglas transversales

- El stock disponible es `stock_quantity - reserved_quantity`.
- Las operaciones que reservan, liberan o consumen stock se ejecutan dentro de una transacción.
- No se permite que una salida deje stock disponible negativo.
- Los encargados y cajeros solo pueden operar sobre sucursales asignadas.
- Las reservas terminales son `ATTENDED`, `CANCELLED` y `EXPIRED`.
- Los pagos repetidos no pueden confirmar ni descontar inventario dos veces.
- La clave de idempotencia de pago electrónico se valida contra la misma venta y el mismo método.
- La notificación sandbox exige el encabezado `X-Sandbox-Signature` configurado en el backend.
- Los cambios relevantes se registran en `bitacora` o en movimientos de inventario/pagos trazables.

## Endpoints principales

```text
GET   /api/v1/inventory
POST  /api/v1/inventory
PATCH /api/v1/inventory/{inventory_id}
GET   /api/v1/inventory/movements
POST  /api/v1/inventory/movements

POST  /api/v1/reservations
GET   /api/v1/reservations/mine
GET   /api/v1/reservations/branch
GET   /api/v1/reservations/branches
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

Las temporadas y colecciones se administran mediante `/api/v1/seasons` y `/api/v1/collections`.

## Evidencia de cierre

- Backend: `23 passed` con `cd backend && python -m pytest -q`.
- Angular: `11 passed` con `cd web && npm test -- --watch=false`.
- Flutter: `7 passed` con `cd mobile && flutter test`.

La suite backend cubre autenticación, administración, catálogo, proveedores, inventario, temporadas/colecciones, reservas, carrito, venta presencial, compra digital, pago en caja, pago electrónico sandbox, idempotencia, notificación autenticada y protección contra reversión de estados terminales.

## Notas de despliegue

- `SANDBOX_PAYMENT_WEBHOOK_SECRET` debe cambiarse fuera del entorno académico local.
- La integración Stripe real requiere endpoint propio de PaymentIntent y webhook firmado real; no se marca como requisito de cierre del Ciclo 2 porque el documento académico permite ambiente de prueba.
- Para producción se recomienda ejecutar pruebas E2E con navegador y pruebas de concurrencia contra PostgreSQL real antes de exponer ventas reales.
