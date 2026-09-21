# Cycle 3 Contracts

This document defines the functional baseline for Cycle 3. A use case is complete only when backend behavior, authorization, planned UI surface, validation, tests, and documentation are aligned.

## Roles and permissions

| Role | Cycle 3 scope |
| --- | --- |
| ADMIN | Manages promotions and reads all reports. |
| CLIENT | Reads own purchase history, recommendations, and virtual fitting sessions. |
| CASHIER | No new Cycle 3 administration scope. |
| BRANCH_MANAGER | Reads operational reports only if explicitly granted later. |
| SUPPLIER | No direct Cycle 3 scope. |

## Use cases

| CU | Use case | Acceptance criteria |
| --- | --- | --- |
| CU23 | Purchase history | A client can list and inspect only their own confirmed/pending/failed purchases with items and payments. Unauthorized users cannot read another customer's history. |
| CU20 | Promotions | An administrator creates, edits, activates/deactivates promotions, assigns products, and valid promotions affect cart and sale totals without producing negative totals. |
| CU21 | Reports and dashboards | An administrator can read sales, stock, reservations, channels, and revenue summaries with date/branch filters. Calculations match persisted sales/inventory/reservations. |
| CU22 | AI recommendations | A client receives explainable product recommendations based on purchase history, category affinity, active season, popularity, and available stock. Products without availability are excluded. Cold-start clients receive popular available products. |
| CU12 | Virtual fitting | A client can start, finish, and list virtual fitting sessions for active products. Mobile provides a camera/overlay prototype using local pose detection or a documented fallback simulator. |

## Constraints

- The recommendation engine is an academic scoring engine. It is considered AI assistance because it infers ranked products from behavior and catalog signals; it does not train a custom ML model.
- The virtual fitting room uses local mobile pose detection (`camera` + `google_mlkit_pose_detection`) and transparent garment overlays. A simulator fallback is used when no camera is available.
- Stripe production integration is outside Cycle 3. Sandbox payments remain the accepted academic payment path.

## Definition of Done

- Backend tests cover each CU's successful flow and main authorization/error cases.
- Web/mobile compile/test suites pass.
- `docs/cycle-3.md` records implemented endpoints, surfaces, verification evidence, and limitations.
