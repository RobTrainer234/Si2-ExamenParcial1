# Migrate Gemini integrations to OpenAI

## Goal
Replace every active Gemini API-key/provider path in FashionStore with OpenAI/GPT while preserving local fallbacks, tenant/security boundaries, and existing response contracts. Scope includes report intent/narrative, report audio transcription, virtual fitting image generation/editing, AI chat, and recommendation-reason enrichment. Keep the actual API key user-managed and backend-only.

## Authorization and model selection
- User explicitly requested the full Gemini-to-GPT migration and asked the orchestrator to select suitable models.
- Text workloads (reports, chat, recommendation enrichment): `gpt-5.4-mini` via the existing OpenAI Responses/Chat Completions contracts; it is current, supports structured outputs, and is suitable for cost/latency-sensitive structured requests.
- Virtual fitting: `gpt-image-2.6-sunburst` for detailed image editing with person and garment image inputs; the existing VTON contract needs an image output, not merely vision/text.
- Audio transcription: `gpt-transcribe` via the OpenAI audio-transcriptions API.
- Official references: https://developers.openai.com/api/docs/models/gpt-5.4-mini ; https://developers.openai.com/api/docs/models/gpt-image-2.6-sunburst ; https://developers.openai.com/api/docs/models/gpt-transcribe . No live provider request was made.

## Current state
- CodeGraph and read-only mapping identified active Gemini usage in `backend/app/modules/reports/ai_service.py`, `backend/app/modules/virtual_fitting/vton_service.py`, `backend/app/modules/ai_chat/service.py`, and `backend/app/modules/recommendations/service.py`.
- OpenAI is already configured and used as a fallback for reports/chat, but Gemini currently has precedence. Recommendations and VTON call Gemini directly. Audio transcription is Gemini-only.
- `backend` uses direct `httpx` calls; no provider SDK dependency is required by the current integration patterns.
- Repository working tree contains extensive pre-existing modifications. Preserve them; do not stage or commit.
- Implementation is blocked before source work: required `gentle-ai-worker/SKILL.md` is absent (`ENOENT`, `paths-invalid`); no configured generic worker or native Agent fallback is exposed. No source files were changed for this task.

## Tasks
- [ ] Replace reports' Gemini intent and narrative paths with OpenAI as the primary provider; preserve strict structured intent validation and local fallback. Keep response provider values accurate and remove active Gemini provider literals.
- [ ] Migrate voice-report transcription from Gemini inline audio to OpenAI `gpt-transcribe`; preserve MIME/base64 validation, request size limits, dedicated timeout/error behavior, and no-fabricated-transcript fallback.
- [ ] Migrate virtual fitting from Gemini `generateContent` to OpenAI image editing using `gpt-image-2.6-sunburst`; preserve user-photo/catalog-garment inputs, output contract, privacy boundaries, safe failure semantics, and existing local placeholder behavior when no capture is submitted.
- [ ] Make OpenAI the sole generative route for AI chat and recommendations; preserve the rule-based/local fallback and tenant-bound data access. Retain historical recommendation provenance values where changing persisted history would require a separate migration; new provider source labels should be accurate.
- [ ] Update config defaults, `.env.example`, Compose variable wiring, active UI/provider labels and operational documentation. Remove active Gemini key/model variables from configuration only after all callers are migrated. Do not remove unrelated historical `.gemini` asset paths or historical records.
- [ ] Update tests for OpenAI request/response contracts, malformed/unavailable provider fallback, transcription, image editing, recommendation enrichment, and chat. Use mocks only; no actual API key or live call in tests.
- [ ] Run focused backend/Web/mobile checks and Ruff. Record exact commands/results and limitations; do not apply database migrations or commit.

## Configuration plan
- `OPENAI_API_KEY` is the only active provider secret. Do not request or store the key in chat, memory, tests, docs, or source.
- Proposed non-secret settings: `OPENAI_MODEL=gpt-5.4-mini`, `OPENAI_IMAGE_MODEL=gpt-image-2.6-sunburst`, `OPENAI_TRANSCRIPTION_MODEL=gpt-transcribe`.
- User reports `OPENAI_API_KEY` is already present in local `.env`; this was not inspected or validated. Do not request, print, or store its value. Preserve the key locally while removing Gemini assignments only through a non-disclosing, value-preserving update. Keep placeholders in `.env.example` only.
- Update `docker-compose.yml` and `docker-compose.prod.yml` to pass the OpenAI variable names to the backend only; never expose the secret to Web/mobile builds.

## TDD and verification
- TDD: enabled by the user's standing project instruction to use TDD for code changes; observe RED before implementation, then GREEN and refactor.
- Backend focused runner: `cd backend && pytest -q tests/test_ai_chat_and_returns.py tests/test_generative_reports_ml.py tests/test_report_assistant.py tests/test_report_transcription.py tests/test_virtual_fitting_vton.py`.
- Recommendations integration runner: `cd backend && pytest -q tests/test_auth.py -k cycle3_history_promotions_reports_recommendations_and_virtual_fitting`.
- Backend lint runner: `cd backend && ruff check app/core/config.py app/modules/ai_chat/service.py app/modules/recommendations/service.py app/modules/reports/ai_service.py app/modules/reports/schemas.py app/modules/virtual_fitting/vton_service.py tests/test_ai_chat_and_returns.py tests/test_generative_reports_ml.py tests/test_report_assistant.py tests/test_report_transcription.py tests/test_virtual_fitting_vton.py`.
- Mobile UI runner if provider labels/contracts change: `cd mobile && flutter test test/virtual_fitting_screen_test.dart test/reports_screen_test.dart`.
- Web tests only if report provider DTO/spec changes: `cd web && npm test`.
- No migrations, deployed-service tests, live provider calls, or API-key validation.

## Constraints
- Preserve unrelated working-tree changes; keep writes single-threaded and within explicitly derived narrow surfaces.
- Never expose or persist real provider secrets; never call OpenAI/Gemini for verification.
- Do not claim the virtual fitting output measures real fit or body dimensions; it remains a generated visual preview.
- Update current operational docs, but preserve historical evidence/records unless a separate explicit data migration is authorized.
