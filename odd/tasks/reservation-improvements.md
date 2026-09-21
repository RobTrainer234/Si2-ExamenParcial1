# CU09 reservation improvements

- [x] Add a confirmation dialog before cancelling a reservation, preserving the current cancel endpoint and state transitions.
- [x] Add a status timeline for PENDING, PREPARING, READY, ATTENDED, CANCELLED, and EXPIRED.
- [x] Add a human-readable reservation code derived from the existing reservation id.
- [x] Include branch city, address, phone, and coordinates in reservation detail/list response and display them clearly.
- [x] Add client-side reservation status filters with counts for all, active, historical, and cancelled.
- [x] Keep responsive layout, Spanish UI, accessibility, and existing reservation behavior.
- [x] Run backend/frontend tests, build, container recreation, and browser smoke verification.

## Implementation notes

- Backend reservation serialization now includes nullable branch city, address, phone, latitude, and longitude from the existing Branch/City relationships without database changes.
- Frontend derives reservation codes as `FS-` plus the zero-padded reservation id.
- Client filtering remains in-memory against the already loaded `/reservations/mine` response; no API contract change.
- Cancellation still uses the existing cancel service call after the user confirms in the in-page dialog.

Evidence: Backend 27 tests passed; Angular 48 tests passed; production build passed. Client browser smoke confirmed filters, code `FS-000010`, branch details, timeline, confirmation dialog, and no horizontal overflow at desktop width.