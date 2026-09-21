# CU09 branch availability validation

## Clarified functional purpose

CU09 lets the client identify which active branches have the selected garment variant available and continue to the reservation flow. The reservation is for a scheduled visit to try the garments on in the branch; it is not a purchase. Reservation lifecycle and branch attention are covered by CU10 and CU11.

- [x] Open a catalog product detail as a client.
- [x] Select an available color and size variant.
- [x] Query availability by branch.
- [x] Verify branch, city, address, stock/status, and reservation action render.
- [x] Add automated E2E coverage and update cycle traceability.
- [x] Fix reservation creation failure caused by PostgreSQL `FOR UPDATE` over nullable eager joins.

Evidence: client browser flow returned active branches with stock and reservation actions. The reproduced reservation POST initially returned 500 due to `NotSupportedError`; after the narrow-row locking fix it returned 201 Created and status PENDING. Backend tests: 26 passed. Playwright: 3 passed, 2 skipped because administrative credentials were not configured. Angular: 40 passed.
