# Delivery checkout

## Goal
Add optional home delivery to web and mobile online checkout without breaking branch pickup, inventory, Stripe test, QR, or sandbox payments.

## Decisions
- Existing `branch_id` remains the inventory source/pickup branch selector.
- Add `fulfillment_type`: `PICKUP` (default) or `DELIVERY`.
- Delivery requires a sale-owned shipping snapshot.
- Delivery has no fee in the MVP; totals and payment amounts remain unchanged.
- Shipping details: recipient name, CI, phone, department/city, zone, street, house number, and reference.

## Tasks
- [ ] Add backend model, migration, request/response schema, validation and serialization.
- [ ] Add web and mobile forms with conditional validation and payloads.
- [ ] Run backend/web/mobile regression checks.

## Acceptance criteria
- Existing pickup clients sending only `branch_id` continue to work.
- Delivery cannot start payment until required shipping fields are valid.
- Pickup does not show or require shipping fields.
- Stripe, QR and sandbox payment flows use the same sale total and preserve shipping details.
- Shipping details are stored on the sale and returned only through the sale owner/purchase flow.
