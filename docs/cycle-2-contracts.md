# Contratos del Ciclo 2

Este documento define la línea base funcional para implementar y validar los
casos de uso del Ciclo 2. Un CU solo se considera completo cuando cumple sus
reglas de negocio, autorización, interfaz prevista y pruebas de aceptación.

## Roles y permisos

| Rol | Alcance del Ciclo 2 |
| --- | --- |
| ADMIN | Puede administrar todos los recursos y operar cualquier sucursal. |
| CLIENT | Puede consultar catálogo y disponibilidad, crear y gestionar sus reservas, gestionar su carrito, consultar sus ventas y pagar electrónicamente. |
| BRANCH_MANAGER | Puede consultar y ajustar inventario, consultar y atender reservas, y consultar ventas de sus sucursales. |
| CASHIER | Puede consultar inventario, registrar ventas presenciales, consultar ventas y procesar pagos en caja de sus sucursales. |
| SUPPLIER | No participa en los CU del Ciclo 2. |

Las operaciones de sucursal deben validar que la sucursal esté asignada al
usuario. El cliente solo puede acceder a sus propias reservas, carrito y
ventas. Los administradores no están limitados por sucursal.

## Reglas transversales

- El stock disponible es `stock_quantity - reserved_quantity`.
- Ninguna reserva, venta o movimiento puede dejar stock disponible negativo.
- Las operaciones que cambian stock deben ser atómicas y seguras ante concurrencia.
- Cada reserva, liberación, venta, pago y ajuste debe conservar trazabilidad.
- Las transiciones de reserva solo pueden seguir el flujo definido.
- Los pagos repetidos no pueden confirmar ni descontar inventario dos veces.
- Las notificaciones de pago deben validarse como mensajes legítimos del proveedor; en el sandbox académico se exige `X-Sandbox-Signature` y en producción debe reemplazarse por webhook firmado real.

## Criterios de aceptación por CU

| CU | Criterio de aceptación |
| --- | --- |
| CU18 Inventario y movimientos | Un usuario autorizado consulta y modifica únicamente inventario de sus sucursales; los movimientos `IN`, `OUT`, reservas y liberaciones actualizan stock, son atómicos y quedan auditados. |
| CU10 Gestionar reservas | Un cliente reserva una o más variantes disponibles en una sucursal para visitarla en una fecha programada y probarse las prendas en el local; consulta sus reservas y puede cancelarlas. La reserva no constituye una compra, los errores no dejan reservas parciales y las reservas vencidas liberan stock. |
| CU11 Atención de reservas | Un encargado consulta la bandeja de su sucursal, prepara las prendas para la visita y avanza reservas solo por transiciones válidas hasta `ATTENDED`; cancelación, expiración y atención dejan el inventario consistente. |
| CU19 Temporadas y colecciones | Un administrador crea, actualiza, activa y desactiva temporadas y colecciones; las fechas de vigencia se aplican al catálogo y no se pueden desactivar estructuras usadas por productos activos. |
| CU13 Carrito | Un cliente añade, modifica, elimina y vacía artículos; el total y la disponibilidad son correctos y el carrito no conserva artículos después de completar una compra. |
| CU14 Compra digital | Un cliente selecciona una sucursal, crea una compra desde su carrito, paga electrónicamente y solo después de una aprobación válida se confirma la venta y se descuenta inventario una vez. |
| CU15 Venta presencial | Un cajero autorizado registra y confirma una venta en su sucursal, con variantes y cantidades válidas, sin permitir stock insuficiente ni confirmaciones duplicadas. |
| CU16 Pago en caja | Un usuario autorizado procesa efectivo, tarjeta o QR; se validan monto y referencia, se registra el monto recibido y el cambio cuando corresponda, y la venta se confirma una sola vez. |
| CU17 Pago electrónico | Un cliente inicia un pago y el proveedor sandbox notifica su resultado mediante `X-Sandbox-Signature`; la idempotencia se asocia a la venta correcta y al método correcto, y los estados terminales no pueden revertirse. |

## Superficies previstas

| CU | Backend | Web | Móvil |
| --- | --- | --- | --- |
| CU18 | Sí | Inventario y movimientos | No previsto actualmente |
| CU10 | Sí | Crear, consultar y cancelar | Crear, consultar y cancelar |
| CU11 | Sí | Bandeja de sucursal | No previsto actualmente |
| CU19 | Sí | Administración | No previsto actualmente |
| CU13 | Sí | Sí | Sí |
| CU14 | Sí | Sí | Sí |
| CU15 | Sí | POS | No previsto actualmente |
| CU16 | Sí | POS | No previsto actualmente |
| CU17 | Sí | Checkout | Checkout |

## Definition of Done

Un CU se marca como `Completo` únicamente cuando:

- El contrato de autorización se cumple para cada rol.
- El flujo exitoso y los errores principales están implementados.
- La persistencia funciona desde una base limpia y una base existente.
- La interfaz de cada superficie prevista permite completar el flujo.
- Existen pruebas de integración del backend y pruebas de interfaz cuando aplica.
- Se verifican transacciones, concurrencia, idempotencia y auditoría.
- La documentación y el estado del CU reflejan la evidencia real.
