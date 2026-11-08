# CU-13 Garment Exchange — Backend Safety and Delivery Plan

## Objective
Make the existing garment-exchange backend safe for cashier use, then provide an implementation plan for completing CU-13 across web and mobile POS interfaces.

## Problem
The current exchange endpoint changes inventory but does not persist consumed exchange quantities or monetary differences. It can accept repeat exchanges of the same sold units, reads replacement stock without row locking, and does not validate both variants through the active catalog rules. The first hardening pass also misclassified a cash refund as an approved positive payment and treated cash as sufficient even when a non-cash tender was mixed in or still pending. Existing web UI is a separate sale-return flow, not a garment exchange; no mobile exchange UI was found.

## Accepted decisions and constraints
- Exchange value is the net amount actually paid for returned sale units (sale line total, discounts included and prorated by quantity) versus the replacement variant's current catalog price.
- The first backend iteration supports cash collection/refund for price differences only when every recorded payment on the original sale is settled CASH. Mixed or pending/non-cash tender records fail closed for nonzero differences. A digital-origin sale may proceed only when the calculated difference is zero; non-zero differences fail closed until provider refund/charge integration is designed.
- The operation is online-only. Never hand over the replacement garment while the exchange is unconfirmed. Offline exchange is a future scope requiring a separate consistency design.
- Preserve the user's existing broad worktree changes. Edit only the bounded CU-13 surfaces; do not revert, stage, or commit unrelated files.
- Do not apply migrations to the application schema. Add a migration and verify it only with a unique temporary schema if suitable test infrastructure is explicitly available.
- Strict TDD is required. Use the backend pytest runner from `backend/pyproject.toml`; record exact RED and GREEN results.
- Native review remains deferred because the worktree contains extensive unrelated changes; do not start a broad review.

## Scope
### In scope now
- Persist exchange records and consumed quantities so a sale unit cannot be exchanged repeatedly.
- Enforce tenant/branch and sale eligibility, an exact 30-day window, active product/variant validation, and sufficient replacement stock.
- Make inventory mutation, exchange ledger, cash difference record, and audit record one transaction; lock sale and inventory rows to prevent concurrent duplicate exchange/oversell.
- Use request idempotency and reject reuse of a key with a different payload.
- Calculate difference server-side. Record cash tender/change for additional collection and a distinct cash-refund amount plus explicit cashier confirmation; never serialize a refund as incoming payment/change. Reject nonzero differences unless every original payment record is settled CASH.
- Add focused regression coverage and an additive migration. No frontend implementation in this work unit.

### Out of scope now
- Provider charge/refund integrations for QR, card, or Stripe.
- Offline exchange queue or inventory reservation before server confirmation.
- Web/mobile screens. These are included in the final CU-13 delivery plan, not implemented in this backend repair.
- Applying the migration to any application database, committing, or reviewing unrelated candidate changes.

## Stable tasks
- [x] **CU13-1 — Explore and agree on exchange rules.** Confirm the current API/UI gap, backend defects, cash-only price-difference scope, pricing basis, and online-only policy.
- [x] **CU13-2 — Harden and ledger backend exchanges.** Added durable exchange/idempotency state, validated quantities and variants, locked sale/inventory rows, enforced exact eligibility, and atomically recorded movements, cash adjustment, and audit details.
- [x] **CU13-3 — Verify backend behavior.** Strict-TDD regressions, independent checks, parent spot check, scoped diff check, and migration graph inspection completed; PostgreSQL runtime and migration application remain unverified.
- [x] **CU13-4 — Plan the complete CU-13 flow.** Added the sequenced web/mobile POS, API, testing, and rollout roadmap below.

## Acceptance criteria
- A sold unit cannot be returned/exchanged more than once, including retries and concurrent requests.
- Tenant, branch, sale status, exact 30-day boundary, purchase quantity, active source/replacement variants, and replacement stock are checked server-side.
- Replacement stock cannot be oversold by concurrent exchanges; all database changes roll back together on any failure.
- Reusing an idempotency key with the same request returns the original outcome; changing the request under the same key is rejected, including concurrent duplicate requests.
- Server calculates monetary difference from persisted sale line amounts and current replacement catalog price; client-supplied prices are never trusted.
- Cash price differences are auditable and require recorded tender for collection or explicit cashier confirmation for refund. A refund is stored as an outgoing exchange adjustment, not a positive sale payment; nonzero differences on mixed, pending, unsettled, or non-cash-origin sales are rejected.
- Existing tests remain valid or are updated only where the clarified CU-13 contract requires it; no unrelated behavior is changed.
- No app-schema migration, commit, or broad native review occurs.

## Implementation roadmap for the complete CU-13

### Phase 0 — Backend foundation (completed in this work)
- Add an exchange ledger and exchange-item history with a tenant-scoped idempotency key and request fingerprint.
- Lock the sale and affected inventory rows; validate tenant/branch access, sale status, active variants, exact 30-day eligibility, available replacement stock, and unexchanged original quantity.
- Compute returned value from the persisted net sale-line total prorated by quantity; compute replacement value using the server's current catalog price.
- Require all recorded original payment rows to be settled CASH before accepting a nonzero price difference. Record collections as incoming cash payments; record refunds separately as outgoing `cash_refunded` exchange adjustments with cashier confirmation.
- Apply the unapplied Alembic migration through the deployment process only after the user authorizes the target environment. No migration was applied during this work.

### Phase 1 — Complete the backend contract before building screens
1. Add a branch- and tenant-scoped sale lookup by order number/receipt; expose the original sale lines and remaining exchangeable quantities without leaking cross-branch sales.
2. Add a read-only exchange quote endpoint. It should return remaining quantity, returned-item paid value, current replacement price, available stock, signed difference, settlement eligibility, and quote expiry/fingerprint. The client never supplies authoritative prices.
3. At confirmation, lock and recalculate all quote inputs. If price, stock, eligibility, or remaining quantity changed, return a conflict requiring a fresh quote; never execute a stale quote.
4. Keep idempotency on finalization; same-key/same-payload replays the exact exchange, while different-payload reuse conflicts. Return a durable exchange number/receipt payload.
5. Decide how returned garments enter inventory. **Recommended:** receive them into a non-saleable inspection/quarantine state, and only make them available after inspection. The current backend increments sellable stock immediately; confirm or change this policy before the full UI rollout.

### Phase 2 — Web cashier experience
- Add a distinct “Cambio de prenda” POS mode; keep the existing sale-return action separate and unchanged.
- Search/select a sale, show its date, branch, items, paid values, and remaining exchangeable quantities; do not rely on hard-coded order examples.
- Select the item/quantity received, replacement product/variant and quantity; present the server quote and clear cash-due/cash-refund amounts.
- For additional cash, capture tendered amount and change; for refund, require explicit cashier confirmation. Block nonzero differences when the original payment record is not fully settled cash.
- Confirm with a generated idempotency key; show the exchange receipt only after server success. If offline, disable finalization and preserve no local commitment/claim.

### Phase 3 — Mobile cashier experience
- Add a staff-facing commerce/POS exchange feature in Flutter (repository, typed models, screen and route); do not reuse the customer purchase-history screen as a cashier workflow.
- Match web's lookup → item selection → quote → cash settlement → confirmed receipt sequence and permission/branch rules.
- Show offline state and prevent exchange commitment until the server confirms. Do not queue exchanges in the existing sales/reservations outbox.

### Phase 4 — Verification and rollout
- Backend tests: sale/tenant/branch isolation, exact 30-day boundary, partial and repeated quantities, active/inactive variants, price/discount calculations, zero/positive/negative differences, cash/mixed/pending tenders, stale quote, idempotency, concurrent duplicate requests, stock races, rollback, and audit/receipt data.
- Web unit/component and browser E2E tests; Flutter repository/widget tests; both clients should exercise success, validation errors, stale quotes, offline blocking and retries.
- Run a PostgreSQL integration race test and migration upgrade/downgrade only against an explicitly configured unique temporary schema; never use the application schema or silently fall back to `DATABASE_URL`.
- Manual evidence: cash-to-equal-price, cash collection with change, cash refund with confirmation, exact/expired 30-day boundary, insufficient stock, repeated-unit rejection, mixed/pending tender rejection, and offline blocking.
- Roll out the database migration before the app version that uses the ledger; monitor exchange audit/inventory movements and keep ordinary returns separate.

### Remaining product checkpoint
Before implementing the screens, confirm returned-item inspection/quarantine behavior. The roadmap recommends quarantine first because a cashier cannot establish that a returned garment is immediately sellable. Non-cash refunds/charges and offline exchanges stay out of v1.

## Verification
- Strict TDD, source: user instruction; runner: `cd backend && pytest tests/test_sync_transactions.py -q`.
- RED/GREEN evidence: initial schema/idempotency regression RED (`1 failed`) then GREEN (`1 passed, 5 deselected`); idempotency race regression RED (`1 failed`) then GREEN (`1 passed, 6 deselected`); cash accounting regressions RED (failed with `AttributeError` for the missing settlement helpers) then GREEN (`2 passed, 7 deselected`); pending non-cash regression RED (failed because old predicate accepted CASH + pending CARD) then GREEN (`1 passed, 8 deselected`).
- Final backend run by writer: `9 passed in 14.41s`; independent verification: `9 passed in 14.59s`; parent spot check: `9 passed in 10.88s`.
- Scoped `git diff --check` passed with no whitespace errors (CRLF normalization warnings only).
- `cd backend && alembic heads` reports one head, `x6t8v0z2b4d6`, parent `w5s7u9x1z3b5`. This validates the revision graph only; no migration was applied or executed.
- PostgreSQL concurrency and isolated-schema migration round-trip remain unverified; SQLite does not establish PostgreSQL row-lock behavior. Never fall back to `DATABASE_URL`.

## Progress
CU13-1 through CU13-4 are complete for this request. Backend exchange hardening and the requested full implementation roadmap are recorded here. The final 9-test focused suite passed in the writer run, independent verification, and parent spot check; the scoped diff check and Alembic single-head graph check passed. No application migration was run, no commit was made, and broad unrelated worktree changes were preserved. PostgreSQL concurrency/migration execution and native review remain pending; native review stays deferred until the user isolates a candidate and authorizes fresh scope.

## Updated implementation plan after user decision (2026-11-02)

### Accepted returned-garment policy
The user selected **quarantine pending inspection** for garments received during CU-13 exchanges. A returned exchange item must not increase sellable stock until an authorized inspection explicitly releases it. Rejected items remain non-saleable and must never increase sellable stock. The ordinary sale-return endpoint remains a distinct existing flow and is not changed by this CU-13 work unless separately authorized.

### Newly tracked tasks
- [x] **CU13-5 — Close endpoint and tenant-isolation gaps.** Added explicit tenant scoping to both locked exchange inventory queries and endpoint-level cash collection/refund/payment assertions, including foreign-tenant inventory rejection.
- [x] **CU13-6 — Implement exchange quarantine and inspection API.** Added a separate tenant/branch-scoped quarantine ledger and unapplied migration; exchange returns do not restock or emit `RETURN`, queue/inspection APIs are permission- and branch-scoped, RELEASE restocks once with an `IN` movement, REJECT remains non-saleable, and decisions are audited. Exchange responses/replays include quarantine identity/status.
- [x] **CU13-7 — Add sale lookup and exchange quote contract.** Added branch/tenant-scoped lookup, server-priced quote, and signed expiry/input binding; finalization recomputes under locks and rejects stale/expired quote before mutation.
- [x] **CU13-8 — Build web cashier exchange experience.** Added distinct `EXCHANGE` POS mode in `pos.component.ts` keeping `RETURN` separate and unchanged, with online-only lookup/quote/finalize guards, inline quantity/cash validations, optional reason, ambiguous-failure frozen retry preserving `idempotency_key`, and full confirmed receipt showing quarantine ID/status.
- [x] **CU13-8b — Build web quarantine inspection UI.** Added manager-only (`ADMIN` / `BRANCH_MANAGER` with `inventory.adjust`) quarantine queue and explicit `RELEASE` / `REJECT` actions with required inspection reason (`>= 2` chars) in `operations.component.ts` and `admin.service.ts`.
- [x] **CU13-9 — Build online-only Flutter cashier exchange flow.** Added staff-only AppBar entry point (`ADMIN` or `sales.create`), typed models, `ExchangeRepository`, `exchangeRepositoryProvider`, and `GarmentExchangeScreen` with online-only lookup/quote/cash-settlement/receipt flow, ambiguous-network idempotent retry, 409 stale-quote recovery, and zero offline outbox writes.
- [x] **CU13-10 — Verify CU-13 changes.** Verified focused Backend (`17 passed`, single Alembic head `y7u9w1x3z5b7`), full Web (`28/28` spec files, `145/145` tests), and full Flutter (`0` issues on `flutter analyze`, `72/72` tests across the mobile suite including `10/10` CU-13 exchange tests). No migrations applied to `DATABASE_URL`; unrelated dirty worktree preserved.

## CU13-5 result
- Added `Inventory.tenant_id == current_user.tenant_id` to both returned/replacement inventory lookups while preserving branch/variant filters and row locks.
- Added endpoint assertions for a positive CASH collection (`amount=30.00`, tender `50.00`, change `20.00`) and a negative CASH refund (`cash_refunded=50.00`, no incoming exchange Payment/change, explicit cashier confirmation). Added foreign-tenant inventory rejection.
- Strict-TDD evidence: writer's first RED was `8 passed, 1 failed` due only to a formatting expectation (`'50'` vs `'50.00'`), not a feature failure; after correction and code change, writer GREEN was `9 passed in 5.12s`. Independent verifier reran the same focused suite: `9 passed in 5.76s`.
- No migration, staging, commit, broad test suite, or native review was run. SQLite tests do not validate PostgreSQL row-lock behavior.

## CU13-6 result
- Added `InventoryQuarantine` as a separate ledger linked to exchange items, branch, tenant, inventory, and variant. Exchange finalization no longer increases returned-item sellable stock and creates no `RETURN` movement; it creates a `PENDING` quarantine record instead.
- Added `GET /inventory/quarantine` and `POST /inventory/quarantine/{id}/inspection`. Inspection is restricted to ADMIN/BRANCH_MANAGER with existing `inventory.adjust`, tenant and branch checks, row locks, audit, same-decision replay, and conflict on reversal. RELEASE increases sellable stock once and writes an `IN` movement; REJECT does not restock.
- Added optional `quarantine_id` and `quarantine_status` to the exchange response and persisted result for same-key replay. Fields are nullable for legacy idempotency records.
- Added unapplied migration `backend/migrations/versions/y7u9w1x3z5b7_cu13_exchange_quarantine.py`, parent `x6t8v0z2b4d6`; migration was not executed.
- Core strict-TDD result reported by writer: RED `2 failed, 10 passed`; GREEN `12 passed`. A later independent endpoint-security test hardening used real SQLite ORM fixtures and passed separately; the metadata/coverage follow-up did not capture its own RED. Independent final run: `13 passed in 4.94s`. `cd backend && alembic heads` reports `y7u9w1x3z5b7 (head)`.
- PostgreSQL concurrency and migration execution remain unverified. Independent verification noted legacy result replay without quarantine keys is supported by nullable response fields but that exact replay case is not directly tested.

## CU13-7 result
- Added `GET /sales/lookup/{order_number}` requiring `sales.read`; it filters by current tenant and accessible branches and returns sale items with net paid line totals and remaining exchangeable quantities.
- Added `POST /sales/{sale_id}/exchange/quote` requiring `sales.create`; quote derives returned value, current replacement price, stock/reserved quantities, signed difference, and settlement eligibility from server state.
- Exchange finalization now requires a server-authenticated quote fingerprint and expiry, signs the canonical values with HMAC-SHA256 using `settings.jwt_secret`, recalculates under sale/item/inventory locks, and rejects expired or changed inputs before mutations. Idempotency, cash-only nonzero differences, and quarantine remain intact.
- Strict-TDD evidence: first requested run failed only because the new quote test file did not yet exist (setup failure; not behavior RED). Then expiry-tampering regression observed RED (`200 EXCHANGED`) before the HMAC-expiry fix and GREEN afterward. Tests-only route coverage added after.
- Writer and independent final focused run: `cd backend && pytest tests/test_sync_transactions.py tests/test_cu13_exchange_quote.py -q` — final verifier `12 passed in 8.58s`. SQLite API checks cover tenant and branch lookup isolation, partial remaining quantities, quote arithmetic/stock, stale price/stock, actual expiry, expiry extension tampering, and no-mutation failures. PostgreSQL lock/concurrency behavior remains unverified.

## CU13-8 result
- Completed distinct `EXCHANGE` mode in `web/src/app/features/commerce/pos.component.ts` and expanded exchange/quarantine contracts in `web/src/app/core/models/admin.models.ts`, keeping `RETURN` separate and unchanged.
- Enforced online-only guards across lookup, quote, and finalization (never queuing in `OfflineTransactionService`), added inline validations for quantities, cash tender, and ineligible non-cash differences, preserved frozen `idempotency_key` retries on ambiguous (`status === 0` or `>= 500`) responses, decremented remaining exchangeable quantities on confirmation, rendered the confirmed quarantine receipt, and added `resetExchangeFlow()`.
- Strict-TDD evidence: RED failed compilation in `pos.component.spec.ts` (`TS2339: Property 'exchangeReason' / 'resetExchangeFlow' does not exist on type 'PosComponent'`); GREEN passed `npx ng test --include "**/pos.component.spec.ts" --watch=false` (`1 passed, 9 tests`).

## CU13-8b result
- Added `quarantineList` (`GET /inventory/quarantine`) and `inspectQuarantine` (`POST /inventory/quarantine/{id}/inspection`) in `web/src/app/core/admin/admin.service.ts`.
- Added quarantine queue card in `web/src/app/features/operations/operations.component.ts` with status filtering (`PENDING` default, `RELEASED`, `REJECTED`, all), manager-only action gating (`ADMIN` or `BRANCH_MANAGER` with `inventory.adjust`), inline reason validation (`min_length >= 2`), explicit `RELEASE` / `REJECT` buttons, read-only view for non-managers, and automatic refresh of inventory, movements, and quarantine records.
- Strict-TDD evidence: RED failed compilation (`TS2339` on missing `quarantineList`, `inspectQuarantine`, `canInspectQuarantine`, `quarantineItems`, `submitQuarantineDecision`); GREEN passed `npx ng test --include "**/admin.service.spec.ts" --include "**/operations.component.spec.ts" --watch=false` (`2 passed, 8 tests`).

## CU13-9 result
- Added typed exchange models (`mobile/lib/features/exchange/data/exchange_models.dart`), `ExchangeRepository` (`mobile/lib/features/exchange/data/exchange_repository.dart`), `exchangeRepositoryProvider` (`mobile/lib/core/providers.dart`), online-only `GarmentExchangeScreen` (`mobile/lib/features/exchange/presentation/garment_exchange_screen.dart`), and staff-only AppBar entry point (`canAccessCashierExchange` in `mobile/lib/main.dart`), keeping customer `PurchaseHistoryScreen` untouched.
- Matched Web's lookup → item/variant selection → server quote → cash collection/refund confirmation → confirmed quarantine receipt workflow, freezing controls with preserved `idempotency_key` on ambiguous failures, clearing stale quotes on `409`, blocking actions when `ConnectivityStatus.offline`, and never writing to `OfflineTransactionRepository`.
- Strict-TDD evidence: RED failed compilation (`00:00 +0 -2: Some tests failed` for missing exchange models/repository/screen/provider); GREEN passed `flutter test test/exchange_repository_test.dart test/garment_exchange_screen_test.dart` (`10 passed`) and `flutter analyze` (`No issues found!`).

## CU13-10 result
- Backend focused verification: `cd backend && pytest tests/test_sync_transactions.py tests/test_cu13_exchange_quote.py tests/test_cu13_exchange_quarantine.py tests/test_cu13_exchange_quarantine_api.py -q` → `17 passed in 6.30s`; `alembic heads` → `y7u9w1x3z5b7 (head)` (revision graph check only; no migration applied to `DATABASE_URL`).
- Web full verification: `cd web && npm test -- --watch=false` → `28 passed (28)` spec files, `145 passed (145)` tests.
- Mobile full verification: `cd mobile && flutter test` → all suites passed (`72 passed`); targeted `flutter analyze` on all CU-13 Dart files → `No issues found!`.
- Scoped `git diff --check` on modified CU-13 files passed with exit code `0`.

## Progress
CU13-1 through CU13-10 are complete across Backend, Web POS + Operations Quarantine UI, and Mobile Flutter POS. All strict-TDD RED/GREEN checks and focused/full suites passed. Unrelated dirty worktree changes were preserved; no staging, commit, or application-database migration was executed. PostgreSQL live row-lock concurrency and deployment migration application (`alembic upgrade head`) remain deployment-time steps once authorized by the user.

## Immediate next step
When ready to deploy or test against a live PostgreSQL instance, authorize running `alembic upgrade head` (`y7u9w1x3z5b7`) on the target database before serving the updated CU-13 endpoints.
