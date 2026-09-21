# Customer reservations UX

- [x] Preserve reservation loading, detail, cancellation, routes, and service behavior.
- [x] Replace the broken compressed reservation list with readable customer-facing cards.
- [x] Show status, branch, visit date, expiration, and reserved item summary clearly.
- [x] Make selected reservation detail and cancellation action understandable.
- [x] Keep responsive desktop/mobile layout and accessible links/buttons.
- [x] Run web tests and build.
- [x] Ensure delayed reservation detail success/failure updates trigger component change detection.
- [x] Browser smoke verification.

Validation:
- `cd web && npm test`: 13 files passed, 45 tests passed.
- `cd web && npm run build`: completed successfully.
- Client browser smoke confirmed 7 reservation cards, detail rendering for `/my-reservations/10`, cancellation action for PENDING status, and no horizontal overflow at desktop or mobile widths.
