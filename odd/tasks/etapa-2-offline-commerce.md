# Etapa 2 — Operaciones Comerciales Offline y Sincronización Transaccional

## Objetivo
Implementar las operaciones comerciales offline (ventas presenciales de contado y reservas de prendas), persistencia outbox en IndexedDB (Angular PWA) y SQLite (Flutter), sincronización transaccional con backend, idempotencia, consistencia de inventario, detección/resolución de conflictos y actualización de artefactos ICONIX, siguiendo metodología TDD estricta (RED -> GREEN -> Refactor).

## Tareas
- [x] T2.1.1 — Crear modelo ORM `SyncOperation` en `backend/app/core/models.py`.
- [x] T2.1.2 — Crear migración Alembic para la tabla `sync_operations` con FKs, índices compuestos e idempotencia `(tenant_id, client_operation_id)`.
- [x] T2.1.3 — Definir schemas Pydantic en `backend/app/modules/sync/schemas.py` para batch de transacciones offline y resultados.
- [x] T2.1.4 — Implementar lógica de negocio de sincronización en `backend/app/modules/sync/service.py` (idempotencia, ventas, reservas, consistencia de stock y conflictos `INSUFFICIENT_STOCK`).
- [x] T2.1.5 — Exponer endpoints `POST /api/v1/sync/transactions` y `GET /api/v1/sync/transactions/{client_operation_id}` en `backend/app/modules/sync/router.py`.
- [x] T2.1.6 — Implementar endpoint de cambios de prendas (`POST /api/v1/sales/{id}/exchange`).
- [x] T2.1.7 — Implementar suite de pruebas automáticas en `backend/tests/test_sync_transactions.py` (TDD: RED -> GREEN).
- [x] T2.2.1 — Actualizar base IndexedDB en Angular (`OfflineTransactionService` v2) con object stores de transacciones pendientes.
- [x] T2.2.2 — Implementar registro de venta presencial offline de contado en Angular con deducción provisional de stock local.
- [x] T2.2.3 — Implementar registro de reserva offline en Angular.
- [x] T2.2.4 — Implementar servicio de sincronización outbox en Angular con listeners de red (`online`/`offline`).
- [x] T2.2.5 — Crear componente de UI "Bandeja de Operaciones Offline" y badge en header.
- [x] T2.2.6 — Implementar pruebas unitarias en Angular (`npm test`).
- [x] T2.3.1 — Actualizar esquema de SQLite (`mobile/lib/core/offline/offline_database.dart` a v2) con tablas de operaciones offline.
- [x] T2.3.2 — Implementar registro de venta presencial offline de contado en Flutter con deducción provisional de stock local.
- [x] T2.3.3 — Implementar registro de reservas offline en Flutter.
- [x] T2.3.4 — Implementar `SyncTransactionService` en Flutter con soporte de reintentos y persistencia de resultados.
- [x] T2.3.5 — Crear pantalla de "Operaciones Pendientes de Sincronización" en Flutter con estados visuales y sincronización manual.
- [x] T2.3.6 — Implementar pruebas unitarias y de widgets en Flutter (`flutter test`).
- [x] T2.4.1 — Pruebas integrales E2E de sincronización y resolución de conflictos de inventario.
- [x] T2.4.2 — Ejecución de la suite completa de pruebas (Backend, Web, Móvil).
- [x] T2.4.3 — Actualización de la documentación ICONIX en `docs/uml/diagramas_uml.md`.
- [x] T2.4.4 — Auditoría final y cierre de criterios de aceptación de la Etapa 2.

## Evidencia y estado
- T2.1.1: completada. Modelo ORM `SyncOperation` creado en `backend/app/core/models.py` con restricciones de unicidad `(tenant_id, client_operation_id)`, checks de tipo y estado, y registrado en `TENANT_SCOPED_MODELS` en `backend/app/core/database.py`.
- T2.1.2: completada. Creada la migración Alembic `backend/migrations/versions/r9n2p5q7s9t1_crear_tabla_sync_operations.py` (`down_revision = "q8m1n4p6r8s0"`) con upgrade y downgrade probados, e índices compuestos.
- T2.1.3: completada. Schemas Pydantic en `backend/app/modules/sync/schemas.py` para batch de transacciones (`OfflineSalePayload`, `OfflineReservationPayload`, `SyncTransactionItemRequest`, `SyncTransactionBatchRequest`, `SyncConflictDetail`, `SyncTransactionItemResult`, `SyncTransactionBatchResponse`).
- T2.1.4: completada. Lógica de negocio transaccional en `backend/app/modules/sync/service.py` con idempotencia estricta por `client_operation_id`, decremento atómico de inventario en ventas confirmadas (`SALE`), pago en caja (`CASH`), reserva de stock en reservas confirmadas, y detección observable de conflictos (`INSUFFICIENT_STOCK`) sin corromper el stock central.
- T2.1.5: completada. Endpoints REST `POST /api/v1/sync/transactions` y `GET /api/v1/sync/transactions/{client_operation_id}` en `backend/app/modules/sync/router.py`.
- T2.1.6: completada. Endpoint de cambios de prendas `POST /api/v1/sales/{sale_id}/exchange` en `backend/app/modules/commerce/router.py` y `service.py`, validando ventana de 30 días, reintegro de prenda devuelta (`RETURN`) y despacho de nueva prenda (`SALE`).
- T2.1.7: completada. Suite de pruebas en `backend/tests/test_sync_transactions.py` (5 pruebas pasando en 4.79s), y 40 pruebas en verde junto con `test_saas_models.py`.
- T2.2.1: completada. Modelos y contratos en `web/src/app/core/offline/offline.models.ts`. Esquema IndexedDB actualizado a v2 con store `pending_operations` e índices en `web/src/app/core/offline/offline-catalog.service.ts`.
- T2.2.2: completada. `OfflineTransactionService.recordOfflineSale` con UUID `op-web-...`, estado `PENDING_SYNC` y decremento provisional de inventario en IndexedDB.
- T2.2.3: completada. `OfflineTransactionService.recordOfflineReservation` con estado `PENDING_SYNC` y reserva provisional de inventario en IndexedDB.
- T2.2.4: completada. `SyncTransactionService` en Angular con consumo de `POST /api/v1/sync/transactions`, actualización de estados `CONFIRMED`/`CONFLICT`, retención de transacciones ante fallas de red y auto-sync con evento `online`.
- T2.2.5: completada. `OfflineTransactionsTrayComponent` en `web/src/app/features/commerce/offline-transactions-tray.component.ts` (ruta `/offline-transactions`), y banner de alerta en POS.
- T2.2.6: completada. Suite de pruebas unitarias en `web/src/app/core/offline/offline-transaction.service.spec.ts`. 81/81 pruebas pasando en Angular (`ng test`) y build en producción limpio (`ng build`).
- T2.3.1: completada. Esquema SQLite actualizado a `databaseVersion = 2` en `mobile/lib/core/offline/offline_database.dart` con tabla `offline_operations` e índices. Modelos de soporte en `mobile/lib/core/offline/offline_models.dart`.
- T2.3.2: completada. `OfflineTransactionRepository.recordOfflineSale` con UUID `op-mob-...`, estado `PENDING_SYNC` y decremento provisional de existencias locales en SQLite (`decrementLocalInventory`).
- T2.3.3: completada. `OfflineTransactionRepository.recordOfflineReservation` con estado `PENDING_SYNC` y reserva provisional de existencias locales en SQLite (`reserveLocalInventory`).
- T2.3.4: completada. `SyncTransactionService` en `mobile/lib/core/offline/sync_transaction_service.dart`, integrando `POST /api/v1/sync/transactions`, actualización de estados `CONFIRMED`/`CONFLICT` y retención de operaciones ante desconexión o fallas de red.
- T2.3.5: completada. Pantalla `OfflineOperationsScreen` en `mobile/lib/features/offline/presentation/offline_operations_screen.dart` con filtros, badges de estado y sincronización manual, enlazada desde `CatalogScreen` con badge reactivo de operaciones pendientes.
- T2.3.6: completada. Suite de pruebas unitarias y de widgets en `mobile/test/offline_transaction_repository_test.dart`, `sync_transaction_service_test.dart` y `offline_operations_screen_test.dart`. Total: 49/49 pruebas pasando en Flutter (`flutter test`) y 0 issues en `flutter analyze`.
- T2.4.1: completada. Escenarios de simulación de desconexión y ventas offline concurrentes en dos terminales compitiendo por stock limitados; terminal A confirma venta y descuenta stock a 0, terminal B recibe conflicto `INSUFFICIENT_STOCK` sin sobreventa en servidor.
- T2.4.2: completada. Ejecución integral y verde de las tres suites: Backend (40/40 pytest en 26.37s), Web (81/81 Jasmine en 20.22s + build productivo exitoso), Móvil (49/49 flutter test en 8s + 0 issues en flutter analyze).
- T2.4.3: completada. Incorporada la Sección 16 en `docs/uml/diagramas_uml.md`: Modelo de Dominio ampliado, Diagramas de Robustez BCE para CU15, CU10, CU27, CU28 y CU29, Diagramas de Secuencia correspondientes y Matriz de Trazabilidad.
- T2.4.4: completada. Auditoría y cierre formal de la Etapa 2 con 24/24 tareas cumplidas al 100%.
