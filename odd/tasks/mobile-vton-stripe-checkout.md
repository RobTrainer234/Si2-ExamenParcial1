# Mobile VTON and Stripe test checkout

## Goal
Complete the mobile virtual fitting and checkout flows based on the latest screenshots.

## Decisions
- Payment mode: Stripe test real, with credentials supplied through build/runtime configuration only.
- Virtual fitting mode: capture-only VTON; remove misleading live AR overlay and generate a result after capturing a photo.
- Preserve existing routes and separate sandbox payment from Stripe.

## Tasks
- [x] Replace the current live rectangular catalog-image overlay with an explicit capture-only flow using the existing VTON endpoint.
- [x] Integrate Stripe test PaymentSheet/client confirmation with the existing backend intent and confirmation routes.
- [x] Run focused mobile/backend tests, analyze, and APK build; document external Stripe setup requirements.
- [x] Remove the misleading local VTON montage and fabricated fit metrics; require real Gemini output for captured try-on.
- [x] Add complete gallery-photo VTON flow with validation, preview, shared submission, and result actions.

## Acceptance criteria
- The camera screen never renders the raw catalog image as a live overlay.
- Capturing a photo sends non-empty image data to the VTON endpoint and displays the returned composite or a clear error.
- Stripe test checkout is enabled only when configured, creates an intent, presents payment UI, confirms with the backend, and leaves sandbox demo separate.
- No API secret is bundled into Flutter or committed to the repository.
