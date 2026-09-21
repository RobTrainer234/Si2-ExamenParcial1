# Comercio del Ciclo 2

Cada cliente tiene un único carrito activo. Agregar una variante existente incrementa su cantidad; el carrito no bloquea stock y el checkout vuelve a validar disponibilidad.

Las ventas presenciales usan el canal `PHYSICAL` y requieren cajero y sucursal. Las compras digitales usan el canal `DIGITAL` y descuentan inventario de la sucursal seleccionada únicamente cuando el pago queda aprobado.

La pantalla web `/pos`, visible para usuarios con `sales.create`, registra una variante, cantidad y sucursal, y confirma el cobro mediante el endpoint de caja.

Una venta inicia como `PENDING`. Al aprobarse el pago, el sistema bloquea cada registro de inventario, valida `stock_quantity - reserved_quantity`, descuenta el stock físico y registra un movimiento `SALE`.

## Pago en caja

El endpoint de caja valida:

- que la venta sea presencial y esté pendiente;
- que el monto recibido cubra el total;
- que tarjeta y QR usen monto exacto;
- que tarjeta y QR incluyan referencia.

Para efectivo, el sistema persiste `received_amount` y `change_amount`, además del importe aplicado a la venta (`amount`). Esto permite auditar cuánto entregó el cliente y cuánto cambio correspondía.

## Pago electrónico sandbox

El pago electrónico académico usa proveedor `SANDBOX`:

1. `POST /api/v1/payments/electronic` crea o reutiliza un pago pendiente usando `idempotency_key`.
2. La clave de idempotencia solo puede reutilizarse para la misma venta y el mismo método.
3. `POST /api/v1/payments/electronic/notification` exige el encabezado `X-Sandbox-Signature`.
4. Una aprobación confirma la venta y descuenta inventario una sola vez.
5. Un pago en estado terminal `APPROVED`, `REJECTED` o `CANCELLED` no puede revertirse a otro resultado incompatible.

El secreto `SANDBOX_PAYMENT_WEBHOOK_SECRET` debe cambiarse fuera del entorno académico local.

## Stripe real

El frontend y móvil conservan superficies preparadas para Stripe mediante `STRIPE_PENDING`, pero Stripe real queda pendiente de credenciales y backend específico de PaymentIntent. La integración productiva deberá recibir un `client_secret` desde el backend y confirmar el pago mediante webhook firmado de Stripe. El modo sandbox actual no debe confundirse con una pasarela real de producción.
