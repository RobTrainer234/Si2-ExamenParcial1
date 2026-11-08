# CU-14 — Natural-Language Reports and Voice Input

## Goal
Complete the official CU-14 request flow across Web and Flutter: authorized users can submit written analytics questions or speak a query, receive a truthful transcription, and submit the resulting text to the reports assistant. Keep tenant/report authorization and subscription controls intact. Do not expand into CU-15 query-engine redesign or CU-16 chart redesign.

## Authority
- Official definition: `docs/casos-de-uso-oficiales-parcial-2.md` (Etapa 3; Web and Mobile; written and voice input).
- `docs/parcial-2-etapa-3.md` is a roadmap, not the authority for official CU numbering. Its former ICONIX crosswalk included stale CU-30/31/32 labels; the official matrix prevails.
- User selected authenticated backend transcription for Flutter instead of on-device recognition. Audio may reach the application backend and Google Gemini when configured. The UI discloses this and requires explicit upload after recording.
- No real credentials, `.env` reads, live provider/API calls, or real tenant audio were used.

## TDD and runners
- TDD mode: **strict**, source: user's explicit choice. Observed failing tests precede production changes; do not invent RED evidence.
- Runner conventions from `docs/testing.md`: `cd backend && pytest -q`, `cd mobile && flutter test`, `cd web && npm test`, `cd web && npm run build`.

## Decisions
- Flutter uses the existing authenticated backend transcription route, not local recognition.
- Recording stop only prepares a reviewable payload. Upload requires a separate explicit action after a Spanish disclosure; transcript is placed in the prompt for review and does not auto-run the assistant.
- Maximum capture: 30 seconds; maximum decoded request audio: 2 MiB.
- Flutter recorder sends `audio/mp4`; backend also accepts the existing `audio/webm` contract.
- Audio timeouts exceed the maximum recording: backend provider 35 seconds; Flutter HTTP 45 seconds. Other route timeouts remain unchanged.
- Require `generative_reports_enabled` before provider use. Missing/failed/empty transcription returns a clear error, never an unrelated canned prompt.

## Tasks
- [x] **CU14-1 — Finalize voice path and test plan.** User selected backend transcription and strict TDD; current API, entitlement, fallback, permission, and privacy gaps were mapped.
- [x] **CU14-2 — Implement Flutter voice recording and explicit upload.** Added `record 6.2.1`, Android/iOS microphone declarations, recording/review/transcribe/discard states, Spanish disclosure, 30-second and 2 MiB limits, and parsing of backend `text`.
- [x] **CU14-3 — Make backend transcription truthful and bounded.** Strict Base64, MIME and decoded-size validation; feature gate; generic `503 TRANSCRIPTION_UNAVAILABLE`; nullable confidence; no fabricated fallback transcript.
- [x] **CU14-4a — Align audio request timeouts.** Backend provider timeout 35 seconds and Flutter route timeout 45 seconds, preserving 8-second backend/general, 10-second Flutter/general, and 90-second VTON policies.
- [x] **CU14-4 — Complete cross-platform tests and builds.** Added Web SpeechRecognition tests; no production Web change was required. Independent checks passed across backend, Flutter and Web.
- [x] **CU14-5 — Update official CU-14 traceability.** Added the official matrix crosswalk warning and CU-14 status/evidence in `docs/parcial-2-etapa-3.md`; full Stage 3 ICONIX reconciliation remains open and is not claimed complete.

## Implemented behavior
- **Web:** `SpeechRecognition`/`webkitSpeechRecognition` uses `es-BO`, inserts recognized speech into the report prompt, then submits to the assistant. Errors and unsupported browsers are handled. Its voice path is covered by `cycle3-admin.component.spec.ts`.
- **Flutter:** microphone capture, explicit stop/review/send/discard flow, Spanish disclosure that audio goes to the backend and may be processed by Gemini, transcript review before running the assistant, cleanup and visible error/loading states.
- **Backend:** `reports.read` authorization; `generative_reports_enabled` gate before provider call; strict supported-MIME/Base64 checks; 2 MiB decoded limit; generic provider failure response; no fixed false transcript.

## TDD evidence
- Flutter RED: `cd mobile && flutter test test/voice_recording_service_test.dart test/reports_repository_test.dart test/reports_screen_test.dart` failed before production changes due to missing recording service, stale response parsing, and simulated voice UI.
- Backend RED: `cd backend && pytest -q tests/test_report_transcription.py` initially observed 13 failures and 1 pass; timeout test later observed 8 seconds instead of the intended audio-specific 35 seconds.
- Timeout tests observed Flutter's 45-second transcription policy and preservation of general/VTON timeouts. The Web voice test work initially exposed only test-double typing/constructor issues, not a production behavior failure.

## Final independent verification
- `cd backend && pytest -q tests/test_report_transcription.py tests/test_report_assistant.py` — **21 passed** (independent run).
- `cd backend && ruff check app/modules/reports/router.py app/modules/reports/schemas.py app/modules/reports/ai_service.py tests/test_report_transcription.py` — **All checks passed**.
- `cd mobile && flutter test` — **78 tests passed**.
- `cd mobile && flutter analyze` — **No issues found**.
- `cd mobile && flutter build apk --debug` — **Passed**; existing plugin/Kotlin compatibility warning only.
- `cd web && npm test` — **28 files / 150 tests passed**; jsdom emitted AggregateError XHR noise without failing the suite.
- `cd web && npm run build` — **Passed**.

## Remaining runtime limitations
- Real microphone hardware, browser speech-provider behavior, backend deployment, and live Gemini transcription were not exercised; all tests used fakes/mocks.
- The current GenerateContent REST discovery documents the API key as a query parameter. Header support for this exact endpoint was not established, so the existing transport was not changed. Do not expose the key or inspect `.env`.
- Web SpeechRecognition submits immediately after a transcript; Flutter instead presents a review step before running the assistant.
