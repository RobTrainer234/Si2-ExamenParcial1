# Modelo de datos completo de FashionStore

El modelo de datos cubre los 23 casos de uso de los tres ciclos. La base se
implementa con PostgreSQL, SQLAlchemy y migraciones Alembic. Las tablas, indices
y relaciones fisicas usan nombres en español. Los atributos internos de Python
y los nombres JSON de la API conservan sus nombres actuales para no romper los
clientes Angular y Flutter.

## Ciclo 1: base del sistema

- `roles` y `usuarios`: identidad, autenticación y autorización.
- `ciudades` y `sucursales`: ciudades y sucursales.
- `categorias`, `tallas` y `colores`: datos maestros del catálogo.
- `proveedores`, `productos` y `producto_proveedores`: productos y proveedores.
- `temporadas` y `colecciones`: organización comercial por temporada y colección.
- `variantes_producto` e `imagenes_producto`: combinaciones de talla/color y recursos
  visuales.
- `inventario`: existencia actual por sucursal y variante.

## Ciclo 2: operación comercial

- `reservas` y `detalles_reserva`: reservas de una o varias variantes.
- `carritos` y `detalles_carrito`: carrito activo del cliente.
- `ventas` y `detalles_venta`: ventas digitales o presenciales.
- `pagos`: pagos en caja o mediante proveedor electrónico.
- `movimientos_inventario`: ingresos, salidas, reservas, ventas, devoluciones y
  ajustes con stock anterior y posterior.

## Ciclo 3: innovación y analítica

- `promociones` y `productos_promocion`: promociones aplicables a productos.
- `sesiones_vestidor_virtual`: sesiones del vestidor virtual.
- `recomendaciones_ia`: recomendaciones generadas por un servicio de IA y su
  contexto de generación.
- El historial de compras se obtiene de `ventas` y `detalles_venta`, evitando duplicar
  información en una tabla separada.

## Bitácora transversal

La clase `Bitacora`, almacenada en `bitacora`, registra cambios y eventos
relevantes de toda la plataforma:

- Usuario que originó el evento, conservado como `NULL` si fue eliminado.
- Acción realizada, por ejemplo `CREATE`, `UPDATE`, `ACTIVATE`, `LOGIN` o
  `DELETE`.
- Tipo e identificador de la entidad afectada.
- Descripción legible del evento.
- Valores anteriores y nuevos en formato JSON cuando corresponda.
- Dirección IP, agente del cliente y fecha/hora.

La relación con la entidad afectada es polimórfica mediante `entity_type` y
`entity_id`. Esto permite registrar en una sola bitácora cambios sobre usuarios,
sucursales, productos, inventario, reservas, ventas, pagos y configuraciones sin
crear una tabla de auditoría por cada módulo.

## Reglas de integridad

- Correos, códigos, slugs y SKU son únicos.
- Una variante no puede repetir producto, talla y color.
- Un inventario no puede repetir sucursal y variante.
- Las cantidades de carrito, reserva, venta y movimiento deben ser positivas.
- El stock anterior y posterior nunca puede ser negativo.
- Los importes de pagos, descuentos y totales no pueden ser negativos.
- Una promoción debe tener fechas válidas y un descuento positivo.
- Las relaciones maestras usan `RESTRICT` para evitar eliminar datos referenciados.
- Los detalles de carrito, reserva, venta y promoción se eliminan con su cabecera
  cuando corresponde.
- La bitácora conserva el evento aunque el usuario original sea eliminado.

## Migraciones

La migración inicial crea las entidades del Ciclo 1. La migración
`5c6e7f44ee6b_agregar_operaciones_ciclos_2_y_3_y_` incorpora las entidades de los
Ciclos 2 y 3, las relaciones de temporada/colección y la `Bitacora`. Las
revisiones posteriores traducen las tablas, indices y columnas de auditoría al
español sin perder los datos existentes.

Aplicar el esquema completo:

```bash
cd backend
alembic upgrade head
```

En Docker, el servicio `migrate` ejecuta este comando automáticamente antes de
iniciar el backend.
