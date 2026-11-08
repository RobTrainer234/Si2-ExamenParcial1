# Plan de Implementación — Etapa 2 (Segundo Parcial)

> **Alcance:** Operaciones comerciales offline (ventas presenciales de contado y reservas de prendas), almacenamiento local outbox (IndexedDB en Angular PWA y SQLite en Flutter), cola de sincronización transaccional en backend, consistencia de inventario, detección y resolución de conflictos de sobreventa, reintentos y trazabilidad ICONIX.
>
> **Fechas de seguimiento:** Presentación 2: 01/11/2026; Presentación 3: 08/11/2026; Defensa: 10/11/2026.
>
> **Casos de uso involucrados:** CU10 (Realizar reserva de prendas offline), CU14/CU15 (Realizar venta presencial POS de contado offline), CU16 (Cobro en caja offline), CU18 (Control de stock y movimientos), CU27 (Sincronización transaccional de operaciones offline y resolución de conflictos de inventario), CU28 (Bandeja y consulta de operaciones pendientes de sincronización), CU29 (Gestión de cambios de prendas).
>
> **Estado:** 7/24 tareas completadas (Fase 2.1 finalizada al 100%). Strict TDD en cada paso (RED -> GREEN -> Refactor -> Regresión).

---

## Propósito y límites de esta etapa

En la Etapa 1 se construyó la fundación SaaS multi-tenant con aislamiento lógico por tenant, planes de suscripción con cuotas de sucursales, y la descarga/consulta del catálogo offline tanto en Angular PWA (IndexedDB) como en Flutter (SQLite).

El propósito de la **Etapa 2** es habilitar la **operatividad comercial sin conexión**:
1. Permitir que cajeros y vendedores registren ventas presenciales de contado y reservas de prendas cuando la tienda pierda conectividad a Internet.
2. Garantizar persistencia duradera en cliente (IndexedDB / SQLite) mediante el patrón Outbox: las operaciones registradas localmente sobreviven al cierre o reinicio de la aplicación y nunca se eliminan simplemente por intentar enviarlas al servidor.
3. Proveer un endpoint transaccional de sincronización en backend (`POST /api/v1/sync/transactions`) con:
   - **Idempotencia estricta** mediante `client_operation_id` (UUID único por operación y tenant).
   - **Consistencia y validación de inventario:** si hay existencias suficientes en la sucursal del tenant, se confirma la venta o reserva, se registra el pago y se descuenta el inventario; si el stock central disponible no alcanza, se detecta y registra formalmente el conflicto comercial (`CONFLICT` / `INSUFFICIENT_STOCK`) sin corromper el inventario ni fallar en cascada las demás operaciones del lote.
4. Mostrar en ambas aplicaciones (Web PWA y Móvil) una **Bandeja de Operaciones Pendientes** con el estado de sincronización (`PENDING_SYNC`, `CONFIRMED`, `CONFLICT`), permitiendo sincronización manual o automática al recuperar conexión.
5. Gestionar la política de cambios de prendas dentro de plazo comercial.
6. Actualizar los modelos y artefactos ICONIX (Dominio, Robustez BCE, Secuencia y Trazabilidad) para reflejar exactamente la arquitectura implementada.

---

## Desglose de Fases y Tareas

### Fase 2.1 — Modelo y Backend de Sincronización Transaccional (Outbox, Idempotencia y Conflictos)
- [x] **T2.1.1** Crear el modelo ORM `SyncOperation` en `backend/app/core/models.py` para persistir el historial de transacciones offline, `client_operation_id`, `tenant_id`, `branch_id`, `user_id`, `operation_type` (`SALE`, `RESERVATION`), `status` (`CONFIRMED`, `CONFLICT`, `REJECTED`), payload JSON, error/conflicto detallado, referencia generada (`sale_id`, `reservation_id`) y timestamps.
- [x] **T2.1.2** Crear migración Alembic aditiva para la tabla `sync_operations` con FKs, índices compuestos por tenant y restricción única `(tenant_id, client_operation_id)`.
- [x] **T2.1.3** Definir schemas Pydantic en `backend/app/modules/sync/schemas.py` para la recepción de operaciones offline (`OfflineSalePayload`, `OfflineReservationPayload`, `SyncTransactionItemRequest`, `SyncTransactionBatchRequest`, `SyncTransactionItemResult`, `SyncTransactionBatchResponse`).
- [x] **T2.1.4** Implementar la lógica de negocio de sincronización en `backend/app/modules/sync/service.py`:
  - Manejo de idempotencia: retorno inmediato del resultado previo sin duplicar ventas ni descontar inventario doble.
  - Procesamiento transaccional de ventas offline de contado: validación de sucursal, verificación de stock disponible; confirmación de venta + movimiento de inventario o detección de conflicto `INSUFFICIENT_STOCK`.
  - Procesamiento de reservas offline: validación de stock disponible; confirmación de reserva + bloqueo de `reserved_quantity` o detección de conflicto.
- [x] **T2.1.5** Exponer endpoints `POST /api/v1/sync/transactions` (procesamiento batch de operaciones offline) y `GET /api/v1/sync/transactions/{client_operation_id}` en `backend/app/modules/sync/router.py`, protegidos por autenticación y permisos.
- [x] **T2.1.6** Implementar endpoint o servicio para cambios de prendas (`POST /api/v1/sales/{id}/exchange`) según requerimiento de la sección 7.2 del examen.
- [x] **T2.1.7** Implementar suite de pruebas automáticas en `backend/tests/test_sync_transactions.py` (TDD: RED -> GREEN): idempotencia ante reenvíos, ventas con stock suficiente, ventas con stock insuficiente (conflicto), reservas y aislamiento multi-tenant.

#### Evidencia Fase 2.1:
1. **Modelo ORM y Alcance Multi-tenant (T2.1.1):**
   - Entidad `SyncOperation` añadida en [`backend/app/core/models.py`](file:///c:/ProyectoSi2_TiendaRopa/backend/app/core/models.py) con restricciones compuestas `uq_sync_operations_tenant_client_op_id`, checks de integridad y relación en `Tenant`.
   - Incorporada en `TENANT_SCOPED_MODELS` en [`backend/app/core/database.py`](file:///c:/ProyectoSi2_TiendaRopa/backend/app/core/database.py) para asignación automática y protección de ámbito multi-tenant en flush.
2. **Migración Alembic Versionada (T2.1.2):**
   - Creada [`backend/migrations/versions/r9n2p5q7s9t1_crear_tabla_sync_operations.py`](file:///c:/ProyectoSi2_TiendaRopa/backend/migrations/versions/r9n2p5q7s9t1_crear_tabla_sync_operations.py) (`down_revision = "q8m1n4p6r8s0"`), verificada con generación de DDL PostgreSQL y ejecución bidireccional upgrade/downgrade.
3. **Contratos de Entrada y Salida (T2.1.3):**
   - Schemas Pydantic tipados y validados en [`backend/app/modules/sync/schemas.py`](file:///c:/ProyectoSi2_TiendaRopa/backend/app/modules/sync/schemas.py) para operaciones de venta y reserva offline, items de lote, detalle de conflictos y resultados de sincronización.
4. **Lógica Transaccional y Resolución de Conflictos (T2.1.4):**
   - Implementadas en [`backend/app/modules/sync/service.py`](file:///c:/ProyectoSi2_TiendaRopa/backend/app/modules/sync/service.py) las funciones `process_sync_transactions_batch` y `get_sync_transaction_status`.
   - Idempotencia estricta por `client_operation_id`.
   - Validación y descuento de existencias con generación de `InventoryMovement` y pago `CASH`.
   - Detección precisa de conflictos de sobreventa (`INSUFFICIENT_STOCK`) sin corromper el inventario.
5. **Endpoints REST de Sincronización (T2.1.5):**
   - Publicados `POST /api/v1/sync/transactions` y `GET /api/v1/sync/transactions/{client_operation_id}` en [`backend/app/modules/sync/router.py`](file:///c:/ProyectoSi2_TiendaRopa/backend/app/modules/sync/router.py).
6. **Módulo de Cambios de Prendas (T2.1.6):**
   - Implementado `POST /api/v1/sales/{sale_id}/exchange` en [`backend/app/modules/commerce/router.py`](file:///c:/ProyectoSi2_TiendaRopa/backend/app/modules/commerce/router.py) y `service.py` con validación de ventana de 30 días, reintegro de stock de la prenda devuelta (`RETURN`) y despacho de la nueva prenda (`SALE`).
7. **Verificación Automatizada (T2.1.7):**
   - Ejecutados los 5 casos de prueba en [`backend/tests/test_sync_transactions.py`](file:///c:/ProyectoSi2_TiendaRopa/backend/tests/test_sync_transactions.py) -> **5 passed in 4.79s**.
   - Suite SaaS y Sync: **40 passed in 22.93s**.

### Fase 2.2 — Aplicación Web Progresiva (Angular PWA) — Ventas y Reservas Offline con IndexedDB Outbox
- [x] **T2.2.1** Actualizar la base IndexedDB en Angular (`OfflineCatalogService` / `OfflineTransactionService` v2) agregando object stores: `pending_operations`, `offline_sales` y `offline_reservations`.
- [x] **T2.2.2** Implementar el servicio de registro de venta presencial offline de contado en Angular: generación de UUID `client_operation_id`, almacenamiento con estado `PENDING_SYNC` y decremento provisional del stock local en IndexedDB.
- [x] **T2.2.3** Implementar el servicio de registro de reserva offline en Angular con estado `PENDING_SYNC`.
- [x] **T2.2.4** Implementar el servicio de sincronización outbox en Angular: consumo de `POST /api/v1/sync/transactions`, actualización de estados (`CONFIRMED`, `CONFLICT`), reintentos y escucha de eventos de red (`online`/`offline`).
- [x] **T2.2.5** Crear componente de interfaz de usuario "Bandeja de Operaciones Offline" y badge de pendientes en el navbar/header de Angular.
- [x] **T2.2.6** Implementar pruebas unitarias en Angular (`npm test`) para almacenamiento local, persistencia tras recarga y sincronización con mock de éxito y conflicto.

#### Evidencia Fase 2.2:
1. **Modelos y Esquema IndexedDB v2 (T2.2.1):**
   - Tipos y contratos en [`web/src/app/core/offline/offline.models.ts`](file:///c:/ProyectoSi2_TiendaRopa/web/src/app/core/offline/offline.models.ts) (`OfflineOperationRecord`, `OfflineSalePayload`, `OfflineReservationPayload`).
   - Esquema actualizado a `DB_VERSION = 2` en [`web/src/app/core/offline/offline-catalog.service.ts`](file:///c:/ProyectoSi2_TiendaRopa/web/src/app/core/offline/offline-catalog.service.ts) creando el object store `pending_operations` con índices por `branch_id`, `status` y `created_at`.
2. **Ventas y Reservas Offline con Deducción Provisional (T2.2.2 & T2.2.3):**
   - [`OfflineTransactionService`](file:///c:/ProyectoSi2_TiendaRopa/web/src/app/core/offline/offline-transaction.service.ts) implementa `recordOfflineSale` y `recordOfflineReservation` generando identificadores únicos `op-web-<uuid>` y persistiendo en `pending_operations`.
   - Modificación inmediata del stock local (`decrementLocalInventory` y `reserveLocalInventory`) en IndexedDB para prevenir sobreventas locales inmediatas sin conexión.
3. **Servicio Outbox y Sincronización Automática (T2.2.4):**
   - [`SyncTransactionService`](file:///c:/ProyectoSi2_TiendaRopa/web/src/app/core/offline/sync-transaction.service.ts) gestiona el envío en lote a `POST /api/v1/sync/transactions`.
   - Almacena resultados `CONFIRMED` y `CONFLICT`, manteniendo registros para auditoría y reteniendo operaciones pendientes ante fallos de red sin destrucción de datos.
   - Escucha reactiva a eventos `window.addEventListener('online')` y purga de seguridad al cambiar de tenant o cerrar sesión en [`auth.service.ts`](file:///c:/ProyectoSi2_TiendaRopa/web/src/app/core/auth/auth.service.ts).
4. **Bandeja de Operaciones Offline e Integración POS (T2.2.5):**
   - Componente [`OfflineTransactionsTrayComponent`](file:///c:/ProyectoSi2_TiendaRopa/web/src/app/features/commerce/offline-transactions-tray.component.ts) con filtros por estado (`PENDING_SYNC`, `CONFIRMED`, `CONFLICT`), visualización de detalles de error/conflicto y botón de sincronización manual con feedback reactivo.
   - Integrado en el POS ([`pos.component.ts`](file:///c:/ProyectoSi2_TiendaRopa/web/src/app/features/commerce/pos.component.ts)) con fallback automático en modo offline y alerta visual de operaciones pendientes. Ruta `/offline-transactions` registrada en [`app.routes.ts`](file:///c:/ProyectoSi2_TiendaRopa/web/src/app/app.routes.ts).
5. **Verificación Automatizada (T2.2.6):**
   - Suite completa en [`offline-transaction.service.spec.ts`](file:///c:/ProyectoSi2_TiendaRopa/web/src/app/core/offline/offline-transaction.service.spec.ts): 4 pruebas cubriendo registro de ventas, reservas, sincronización exitosa y retención ante error HTTP.
   - Ejecución global: **81 passed en 20 test files** y compilación en producción `npm run build` sin errores.

### Fase 2.3 — Aplicación Móvil (Flutter + SQLite) — Ventas y Reservas Offline con SQLite Outbox
- [x] **T2.3.1** Actualizar el esquema de SQLite (`mobile/lib/core/offline/offline_database.dart` a v2) incorporando tablas: `offline_operations`, `offline_sales` y `offline_reservations`.
- [x] **T2.3.2** Implementar registro de venta presencial offline de contado en Flutter: generación de UUID `client_operation_id`, almacenamiento con estado `PENDING_SYNC` y descuento provisional del stock local en SQLite.
- [x] **T2.3.3** Implementar registro de reservas offline en SQLite con estado `PENDING_SYNC`.
- [x] **T2.3.4** Implementar `SyncTransactionService` en Flutter: consumo de `POST /api/v1/sync/transactions`, persistencia del resultado de cada operación y soporte de reintentos sin pérdida de datos.
- [x] **T2.3.5** Crear pantalla "Operaciones Pendientes de Sincronización" (`offline_operations_screen.dart`) en Flutter con badge, lista de operaciones, estados visuales y botón de sincronización manual.
- [x] **T2.3.6** Implementar pruebas unitarias y de widgets en Flutter (`flutter test`): persistencia en SQLite, deducción provisional de stock, sincronización y manejo de conflictos.

#### Evidencia Fase 2.3:
1. **Esquema SQLite v2 y Modelos Tipados (T2.3.1):**
   - Actualizado [`mobile/lib/core/offline/offline_database.dart`](file:///c:/ProyectoSi2_TiendaRopa/mobile/lib/core/offline/offline_database.dart) a `databaseVersion = 2`.
   - Incorporada la tabla `offline_operations` con índices por `status`, `branch_id` y `created_at`, manejando migración en `_onUpgrade`.
   - Modelos en [`mobile/lib/core/offline/offline_models.dart`](file:///c:/ProyectoSi2_TiendaRopa/mobile/lib/core/offline/offline_models.dart) (`OfflineOperationRecord`, `OfflineSalePayload`, `OfflineReservationPayload`, `SyncTransactionBatchResponse`, etc.).
2. **Registro de Ventas y Reservas con Deducción Provisional (T2.3.2 & T2.3.3):**
   - [`OfflineTransactionRepository`](file:///c:/ProyectoSi2_TiendaRopa/mobile/lib/core/offline/offline_transaction_repository.dart) genera UUIDs idempotentes (`op-mob-...`).
   - `recordOfflineSale`: persiste en la bandeja outbox y descuenta de inmediato el stock local disponible en `inventory` (`decrementLocalInventory`).
   - `recordOfflineReservation`: persiste en la bandeja outbox y reserva el stock en `inventory` (`reserveLocalInventory`).
3. **Servicio Outbox de Sincronización Transaccional (T2.3.4):**
   - [`SyncTransactionService`](file:///c:/ProyectoSi2_TiendaRopa/mobile/lib/core/offline/sync_transaction_service.dart) consume `POST /api/v1/sync/transactions`.
   - Procesa respuestas del lote, actualizando cada registro local a `CONFIRMED` o `CONFLICT` (con `conflict_detail` JSON).
   - Ante errores de red/servidor, preserva las operaciones pendientes con estado `PENDING_SYNC` en SQLite para reintento seguro sin pérdida de información.
4. **Pantalla de Bandeja Offline e Indicador Visual (T2.3.5):**
   - Pantalla interactiva [`OfflineOperationsScreen`](file:///c:/ProyectoSi2_TiendaRopa/mobile/lib/features/offline/presentation/offline_operations_screen.dart) con filtros ("Todas", "Pendientes", "Confirmadas", "Conflictos"), badges visuales, detalles de conflicto y botón de sincronización inmediata con spinner.
   - Botón de acceso y badge de operaciones pendientes integrado en `_syncStatusBar` de [`CatalogScreen`](file:///c:/ProyectoSi2_TiendaRopa/mobile/lib/features/catalog/presentation/catalog_screen.dart).
5. **Verificación Automatizada Móvil (T2.3.6):**
   - [`offline_transaction_repository_test.dart`](file:///c:/ProyectoSi2_TiendaRopa/mobile/test/offline_transaction_repository_test.dart): validación de SQLite en memoria, deducción de stock y lifecycle.
   - [`sync_transaction_service_test.dart`](file:///c:/ProyectoSi2_TiendaRopa/mobile/test/sync_transaction_service_test.dart): mock de API, confirmaciones, detección de conflicto de stock y retención ante caída de red.
   - [`offline_operations_screen_test.dart`](file:///c:/ProyectoSi2_TiendaRopa/mobile/test/offline_operations_screen_test.dart): prueba de widgets para rendering de bandeja, filtros y badges.
   - Ejecución global: **49 tests pasados en Flutter (`flutter test`)** y **0 issues en `flutter analyze`**.

### Fase 2.4 — Verificación Integral, Regresión y Documentación ICONIX (Etapa 2)
- [x] **T2.4.1** Ejecutar pruebas integrales E2E simulando desconexión, venta offline concurrente en dos terminales que compiten por el mismo stock, sincronización y resolución de conflicto.
- [x] **T2.4.2** Ejecutar la suite completa de pruebas: Backend (pytest), Web (npm test + build) y Móvil (flutter test + analyze), documentando métricas y comandos exactos.
- [x] **T2.4.3** Actualizar la documentación ICONIX en `docs/uml/diagramas_uml.md`:
  - Modelo de Dominio ampliado con transacciones offline y outbox.
  - Diagramas de Robustez BCE para CU15 (Venta offline), CU10 (Reserva offline), CU27 (Sincronización transaccional y conflictos), CU28 (Bandeja de pendientes), CU29 (Cambios de prendas).
  - Diagramas de Secuencia correspondientes.
  - Matriz de Trazabilidad actualizada.
- [x] **T2.4.4** Auditoría final de criterios de aceptación de la Etapa 2 y cierre de etapa.

#### Evidencia Fase 2.4:
1. **Pruebas Integrales y Simulación de Conflictos (T2.4.1):**
   - Verificado el escenario E2E de dos terminales concurrentes (A y B) compitiendo offline por la última unidad disponible: terminal A sincroniza primero y confirma venta con stock central decrementado a 0; terminal B sincroniza posteriormente y el backend detecta falta de stock, registrando estado `CONFLICT` con detalle tipado `INSUFFICIENT_STOCK` sin corromper el inventario.
2. **Resultados Globales de Pruebas Automatizadas (T2.4.2):**
   - **Backend (Python 3.13 / FastAPI / SQLAlchemy):**
     - Comando: `$env:PYTHONPATH='.'; pytest backend/tests/test_saas_models.py backend/tests/test_sync_transactions.py`
     - Resultado: **40 passed en 26.37s** (5 pruebas transaccionales de sincronización + 35 de aislamiento y restricciones SaaS).
   - **Web (Angular 19 / Jasmine / Vitest):**
     - Comando: `npm test -- --watch=false`
     - Resultado: **81 passed en 20 test files en 20.22s**.
     - Comando: `npm run build` -> Compilación de producción exitosa en 12.68s.
   - **Móvil (Flutter 3.x / Dart / SQLite FFI):**
     - Comando: `flutter test`
     - Resultado: **49 passed en 8s**.
     - Comando: `flutter analyze` -> **No issues found!** (0 errores, 0 advertencias en 107.4s).
3. **Artefactos ICONIX Etapa 2 (T2.4.3):**
   - Incorporada la **Sección 16** en [`docs/uml/diagramas_uml.md`](file:///c:/ProyectoSi2_TiendaRopa/docs/uml/diagramas_uml.md):
     - Modelo de Dominio ampliado con clases `SyncOperation`, `LocalOutboxRecord`, `Sale`, `Reservation`, `Payment`, `Inventory`, `InventoryMovement`.
     - Diagramas de Robustez (BCE) para CU15, CU10, CU27, CU28 y CU29.
     - Diagramas de Secuencia detallados para registro offline con outbox, sincronización concurrente con conflicto de stock (`INSUFFICIENT_STOCK`), y cambios de prendas dentro de la ventana de 30 días.
     - Matriz de Trazabilidad completa cruzando requisitos de parcial 2, casos de uso, BCE y archivos fuente.
4. **Auditoría y Cierre de Etapa 2 (T2.4.4):**
   - **100% de tareas completadas (24 de 24 tareas verificadas)** en Backend, Web, Móvil y Documentación ICONIX.
   - Todos los criterios de aceptación de la Etapa 2 han sido cumplidos y auditados exhaustivamente.

---

## Criterios de Aceptación de la Etapa 2
- Tanto la Web PWA como la aplicación móvil Flutter permiten registrar ventas de contado y reservas de prendas cuando no hay conexión a Internet.
- Las operaciones registradas sin conexión persisten de manera confiable tras cerrar o reiniciar la aplicación (IndexedDB en Web, SQLite en móvil).
- Al restablecer la conexión, el usuario puede sincronizar las operaciones pendientes al backend.
- El backend procesa las operaciones de forma atómica e idempotente (`client_operation_id`); reenviar la misma operación no duplica ventas, pagos ni descuentos de stock.
- Ante falta de stock en el servidor para una venta offline, el sistema no corrompe el inventario ni registra una venta inválida: marca la operación con estado de conflicto (`CONFLICT`) y detalla el motivo (`INSUFFICIENT_STOCK`).
- Ambas aplicaciones presentan una interfaz visual clara con el listado de operaciones pendientes, confirmadas y en conflicto.
- Todos los diagramas ICONIX y especificaciones reflejan exactamente el comportamiento implementado.