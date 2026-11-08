# Etapa 2 UI Capture Tasks

## Goal
Capture the current Web interface for each official Etapa 2 use case, in official order, using isolated Playwright contexts and mocked/dummy data. The user explicitly prioritized the screenshots and does not require separate independent verification for them. Do not use real credentials, inspect `.env`, contact real transaction APIs, write backend state, or sync real operations.

## Authority and scope
- Official IDs/order: `docs/casos-de-uso-oficiales-parcial-2.md` (CU-08, CU-09, CU-10, CU-11, CU-12, CU-13, CU-22).
- `docs/parcial-2-etapa-2.md` contains historical numbering; do not use those historical IDs for screenshot labels.
- Output: `docs/ui-screens/etapa-2/`, matching the Etapa 1 screenshot folder.
- Capture one CU at a time. This currently covers the Web PWA only; do not assume Flutter screenshots are authorized.

## Tasks
- [x] **CAP-08 — Capture Web CU-08 offline cash sale.** Saved `docs/ui-screens/etapa-2/CU-08_Registrar_Venta_Contado_Offline.png`; isolated mock flow shows queued `PENDING_SYNC` SALE; no sync or backend write.
- [x] **CAP-09 — Capture current Web reservation UI.** Saved `docs/ui-screens/etapa-2/CU-09_Reserva_Prendas_Interfaz_Actual_Online.png`; current interface is online-only, so offline reservation remains a disclosed implementation gap.
- [x] **CAP-10 — Capture Web local pending operations.** Saved `docs/ui-screens/etapa-2/CU-10_Consultar_Operaciones_Locales_Pendientes.png`; shows an isolated pending reservation; no sync.
- [x] **CAP-11 — Capture Web synchronization.** Saved `docs/ui-screens/etapa-2/CU-11_Sincronizar_Operaciones_Offline.png`; mocked synchronization shows a confirmed local reservation; no live backend.
- [x] **CAP-12 — Capture Web synchronization conflict.** Saved `docs/ui-screens/etapa-2/CU-12_Gestionar_Conflictos_Sincronizacion_Estado_Actual.png`; current tray shows `INSUFFICIENT_STOCK`, but no dedicated resolution control exists.
- [x] **CAP-13 — Capture Web garment exchange.** Saved `docs/ui-screens/etapa-2/CU-13_Gestionar_Cambio_Prendas_Interfaz_Actual_Web.png`; mock-only exchange shows `EXCHANGED` and quarantine `PENDING`. No real exchange was performed.
- [x] **CAP-22 — Capture Web offline customer data.** Saved `docs/ui-screens/etapa-2/CU-22_Gestionar_Datos_Minimos_Clientes_Offline.png`; shows the POS customer mode with two synthetic IndexedDB records and a third customer ready in the form. Capture command completed with 1 test passed; no separate independent verification requested. No live backend or credentials used.

## Progress and safety
All 7 official Etapa 2 screenshots (CU-08, CU-09, CU-10, CU-11, CU-12, CU-13, CU-22) are generated and saved in `docs/ui-screens/etapa-2/`. The user explicitly asked to prioritize producing the captures. The CU-13 image is a mock demonstration, not live backend evidence.

The current reservation UI does not implement offline reservation, and the conflict tray has no dedicated conflict-resolution action. Keep those limitations explicit if describing the screenshots. No staging or commits.
