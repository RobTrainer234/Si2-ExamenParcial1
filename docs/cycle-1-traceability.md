# Trazabilidad del Ciclo 1

## Estado actualizado

El Ciclo 1 queda cubierto por implementación backend, web, móvil parcial y pruebas automatizadas. La evidencia actual ya no coincide con los conteos históricos del primer cierre; la verificación más reciente se registra abajo.

| Caso de uso | Estado | Evidencia principal |
| --- | --- | --- |
| CU01 Registrar Cliente | Completo | `POST /api/v1/auth/register`, `backend/app/modules/auth`, pantalla `web/src/app/features/auth/register.component.ts`, prueba `test_register_login_and_me`. |
| CU02 Gestionar Inicio/Cierre de Sesión | Completo | `login`, `me`, `refresh`, `logout`, guards/interceptor Angular, pruebas de rotación y logout. |
| CU03 Gestionar Usuarios y Roles | Completo | `backend/app/modules/users`, `web/src/app/features/admin/admin.component.ts`, validaciones contra auto-desactivación/cambio de rol. |
| CU04 Gestionar Ciudades y Sucursales | Completo | `backend/app/modules/locations`, filtros, activación/desactivación y validaciones de ciudad/sucursal. |
| CU05 Gestionar Productos | Completo | `backend/app/modules/products`, variantes, proveedores, imágenes y publicación de catálogo. |
| CU06 Gestionar Categorías, Tallas y Colores | Completo | `backend/app/modules/catalog_masters`, validación de duplicados y formato hexadecimal. |
| CU07 Gestionar Proveedores | Completo para administración | `backend/app/modules/suppliers`, CRUD administrativo y portal de proveedor base. |
| CU08 Consultar Catálogo y Buscar Prendas | Completo | `backend/app/modules/catalog`, `web/src/app/features/catalog`, `mobile/lib/features/catalog`, filtros públicos. |
| CU09 Consultar Disponibilidad por Sucursal | Completo | Endpoint de disponibilidad por producto/talla/color con filtro de sucursal y ciudad activas. El cliente puede identificar dónde hay stock y pasar al flujo de reserva para probar las prendas en el local; la reserva no es una compra y se gestiona en CU10/CU11. |

## Verificación realizada

- Backend: `23 passed` con `cd backend && python -m pytest -q`.
- Angular: `11 passed` con `cd web && npm test -- --watch=false`.
- Flutter: `7 passed` con `cd mobile && flutter test`.

## Evidencia E2E reciente de CU08

- Catálogo público cargó con 11 productos e imágenes válidas.
- Búsqueda `Bolso` devolvió `Bolso Cuero Sur`.
- Filtro de categoría `Accesorios` devolvió el producto esperado.
- La tarjeta abrió `/catalog/5` y mostró el detalle `Bolso Cuero Sur`.
- Angular: `40 passed`; E2E Playwright: `2 passed`, `2 skipped` por credenciales administrativas no configuradas.

## Evidencia E2E reciente de CU09

- Cliente abrió el detalle del producto desde el catálogo.
- Se validó la selección de color y talla disponible.
- `Ver disponibilidad en tiendas` devolvió 2 sucursales activas.
- Se mostraron sucursal, ciudad, dirección, stock y acción `Reservar`.
- Ejemplo verificado: FashionStore Norte (Cochabamba, 10 disponibles) y FashionStore Centro (Santa Cruz, 6 disponibles).
- E2E Playwright actualizado: `3 passed`, `2 skipped` por credenciales administrativas no configuradas.
- La creación de reserva fue reproducida y corregida: ahora responde `201 Created` y genera una reserva `PENDING`.
- La experiencia de Mis reservas incorpora confirmación de cancelación, línea de estados, código `FS-`, datos de sucursal y filtros por estado.
- Alcance funcional aclarado: la disponibilidad de CU09 permite seleccionar una sucursal y derivar a una reserva de prendas para una visita programada; el objetivo es que el cliente pueda probarlas en el local. La reserva no constituye una compra y su gestión/atención corresponde a CU10/CU11.

## Fuera de alcance del Ciclo 1

No forman parte del Ciclo 1: carrito, reservas, checkout, pagos, ventas, movimientos completos de inventario, IA, realidad aumentada y reportes avanzados. Esos elementos se cierran en Ciclo 2 o quedan para Ciclo 3.

## Riesgos pendientes

- Antes de desplegar, sustituir todos los valores sensibles de `.env.example` y secretos sandbox.
- El seed actual prepara roles, permisos y administrador; los datos de catálogo deben cargarse mediante la API administrativa o scripts controlados.
- Las pruebas E2E visuales no son parte del cierre funcional automatizado del Ciclo 1, pero son recomendables para defensa/demostración.
