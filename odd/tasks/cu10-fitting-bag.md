# CU10 UX — Bolsa de probador multi-prenda

## Objective

Allow a client to collect multiple garment variants in one fitting bag, choose one branch and visit date, review the selection, and create one reservation for the in-store fitting visit. Keep this flow separate from the purchase cart.

## Scope

- Add/remove multiple selected variants from a client-side fitting bag.
- Preserve quantity per variant and prevent duplicate variant rows.
- Choose one branch and scheduled visit date for the whole reservation.
- Submit all items through the existing `POST /api/v1/reservations` `items[]` contract.
- Keep existing reservation lifecycle, stock locking, cancellation, expiration, and branch attention behavior.
- Add accessible Spanish UI and focused tests.

## Non-goals

- No database migration.
- No new reservation endpoint.
- No reuse of the commerce cart.
- No change to CU11 branch workflow.

## Acceptance criteria

- A client can add at least two different variants to one fitting bag.
- The bag shows selected product, size, color, quantity, and removal controls.
- The client selects one available branch and a future visit date.
- One reservation request contains all selected variants.
- Existing single-item reservation behavior remains available through the new flow.
- Empty bag and failed reservation states are handled without losing the draft selection.

## Implementation evidence

- Added `web/src/app/core/reservations/fitting-bag.service.ts` for persisted client-side draft state, duplicate merging, quantities, and shared-branch intersection.
- Added `web/src/app/features/reservations/fitting-bag.component.ts` with responsive Spanish review and one-submit reservation flow.
- Product detail now adds the selected variant to the fitting bag instead of creating a single-item reservation immediately.
- Added authenticated `/fitting-bag` route and client navigation.
- Angular: `14 files / 50 tests` passed.
- Production build passed.
- Playwright CU10 smoke: `1 passed` after force-recreating Docker containers.
- Follow-up UX correction: adding a garment no longer navigates away from product detail; the client can continue exploring, add more garments, or open the bag explicitly.
