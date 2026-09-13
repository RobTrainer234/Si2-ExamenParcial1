# Comercio del Ciclo 2

Cada cliente tiene un unico carrito activo. Agregar una variante existente
incrementa su cantidad; el carrito no bloquea stock y el checkout vuelve a
validar disponibilidad.

Las ventas presenciales usan el canal `PHYSICAL` y requieren cajero y sucursal.
Las compras digitales usan el canal `DIGITAL` y descuentan inventario de la
sucursal seleccionada durante el checkout.

La pantalla web `/pos`, visible para usuarios con `sales.create`, registra una
variante, cantidad y sucursal, y confirma el cobro mediante el endpoint de caja.

Una venta inicia como `PENDING`. Al aprobarse el pago, el sistema bloquea cada
registro de inventario, valida `stock_quantity - reserved_quantity`, descuenta
el stock fisico y registra un movimiento `SALE`.

Los pagos electronicos usan el proveedor `SANDBOX`. La referencia externa y
`idempotency_key` evitan pagos duplicados. Una notificacion repetida para un
pago aprobado no vuelve a descontar inventario.
