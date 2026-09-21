# Cycle 1 and 2 Closure Tasks

Goal: close the identified gaps so Cycle 1 and Cycle 2 can be defended as complete before starting Cycle 3.

## Tasks

- [x] Map exact technical and documentation gaps for payment, inventory validation, and traceability.
- [x] Fix cash payment persistence and electronic payment idempotency/provider notification validation.
- [x] Add regression tests for the corrected payment contracts and inventory/payment safety rules.
- [x] Update Cycle 1 and Cycle 2 documentation, including traceability and current verification evidence.
- [x] Run backend, web, and mobile verification commands and record outcomes.

## Acceptance criteria

- [x] CU16 records received amount/change or equivalent auditable metadata.
- [x] CU17 notification path is authenticated for sandbox/provider simulation and idempotency is bound to the correct sale.
- [x] Tests cover the fixed payment behaviors.
- [x] Documentation no longer claims stale counts or partial status incorrectly.
- [x] Verification commands pass or any remaining blocker is explicitly documented.

## Implementation notes

- Added `received_amount` and `change_amount` to `pagos` with Alembic migration `n5j8k2l4m6p8_agregar_montos_pago_caja.py`.
- Added sandbox notification authentication through `X-Sandbox-Signature` backed by `sandbox_payment_webhook_secret`.
- Bound electronic payment idempotency to the same sale and method.
- Protected rejected/cancelled electronic payments from later approval.
- Updated Angular and Flutter demo clients to send the sandbox signature.
- Updated Cycle 1/Cycle 2 docs and API description.

## Verification

- Backend: `cd backend && python -m pytest -q` -> `23 passed`.
- Web: `cd web && npm test -- --watch=false` -> `11 passed` in 6 files.
- Mobile: `cd mobile && flutter test` -> `7 passed`.
