import base64
import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["OPENAI_API_KEY"] = ""

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import get_db  # noqa: E402
from app.core.models import Base, Permission, Role, RolePermission, Tenant, User  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.reports import ai_service  # noqa: E402
from app.modules.reports import router as reports_router  # noqa: E402

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)


def override_get_db():
    with Session(engine) as session:
        yield session


client = TestClient(app)
_previous_get_db_override = None


@pytest.fixture(autouse=True)
def allow_report_feature_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(reports_router, "check_tenant_feature", lambda *_: True)


def setup_function() -> None:
    global _previous_get_db_override
    _previous_get_db_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    with Session(engine) as db:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        tenant = Tenant(name="Transcription Tenant")
        role = Role(code="REPORTS", name="Reportes")
        permission = Permission(code="reports.read", name="Consultar reportes")
        db.add_all([tenant, role, permission])
        db.flush()
        db.add(RolePermission(role_id=role.id, permission_id=permission.id))
        db.add(User(tenant=tenant, role=role, first_name="Reader", last_name="Reports", email="reader@example.com", phone="70000092", password_hash=hash_password("Reader123!")))
        db.commit()


def teardown_function() -> None:
    ai_service.settings.gemini_api_key = None
    if _previous_get_db_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = _previous_get_db_override


def _headers() -> dict[str, str]:
    tokens = client.post("/api/v1/auth/login", json={"email": "reader@example.com", "password": "Reader123!"}).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _audio_payload(size: int = 3) -> str:
    return base64.b64encode(b"x" * size).decode("ascii")


def test_transcription_returns_text_for_supported_flutter_mp4(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    def provider(audio_base64: str, mime_type: str) -> str:
        calls.append((audio_base64, mime_type))
        return "ventas por sucursal"

    monkeypatch.setattr(ai_service, "transcribe_audio_prompt", provider)

    response = client.post(
        "/api/v1/reports/transcribe-audio",
        headers=_headers(),
        json={"audio_base64": _audio_payload(), "mime_type": "audio/mp4"},
    )

    assert response.status_code == 200
    assert response.json() == {"text": "ventas por sucursal", "confidence": None}
    assert calls == [(_audio_payload(), "audio/mp4")]


def test_transcription_requires_reports_read_permission() -> None:
    response = client.post("/api/v1/reports/transcribe-audio", json={"audio_base64": _audio_payload()})

    assert response.status_code == 401


def test_transcription_denies_feature_before_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(reports_router, "check_tenant_feature", lambda *_: False)
    monkeypatch.setattr(ai_service, "transcribe_audio_prompt", lambda *_: pytest.fail("provider must not be called"))

    response = client.post(
        "/api/v1/reports/transcribe-audio",
        headers=_headers(),
        json={"audio_base64": _audio_payload()},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "FEATURE_NOT_IN_PLAN"


@pytest.mark.parametrize("provider_result", [None, "", "   "])
def test_transcription_returns_generic_unavailable_for_missing_or_empty_provider_output(
    monkeypatch: pytest.MonkeyPatch, provider_result: str | None
) -> None:
    monkeypatch.setattr(ai_service, "transcribe_audio_prompt", lambda *_: provider_result)

    response = client.post(
        "/api/v1/reports/transcribe-audio",
        headers=_headers(),
        json={"audio_base64": _audio_payload()},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "TRANSCRIPTION_UNAVAILABLE"
    assert "Ventas de septiembre" not in response.text


def test_transcription_returns_generic_unavailable_without_provider_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ai_service.settings, "gemini_api_key", None)

    response = client.post(
        "/api/v1/reports/transcribe-audio",
        headers=_headers(),
        json={"audio_base64": _audio_payload()},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "TRANSCRIPTION_UNAVAILABLE"


def test_transcription_returns_generic_unavailable_when_provider_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def failed_provider(*_: str) -> str:
        raise RuntimeError("secret provider failure")

    monkeypatch.setattr(ai_service, "transcribe_audio_prompt", failed_provider)

    response = client.post(
        "/api/v1/reports/transcribe-audio",
        headers=_headers(),
        json={"audio_base64": _audio_payload()},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "code": "TRANSCRIPTION_UNAVAILABLE",
        "message": "La transcripción no está disponible en este momento.",
    }
    assert "secret provider failure" not in response.text


@pytest.mark.parametrize("mime_type", ["audio/wav", "text/plain", "audio/MP4"])
def test_transcription_rejects_unsupported_mime(mime_type: str) -> None:
    response = client.post(
        "/api/v1/reports/transcribe-audio",
        headers=_headers(),
        json={"audio_base64": _audio_payload(), "mime_type": mime_type},
    )

    assert response.status_code == 422


@pytest.mark.parametrize("audio_base64", ["not-base64!", "YWJj=", "YW Jj"])
def test_transcription_rejects_non_strict_base64(audio_base64: str) -> None:
    response = client.post(
        "/api/v1/reports/transcribe-audio",
        headers=_headers(),
        json={"audio_base64": audio_base64},
    )

    assert response.status_code == 422


def test_transcription_rejects_decoded_audio_over_two_mib() -> None:
    response = client.post(
        "/api/v1/reports/transcribe-audio",
        headers=_headers(),
        json={"audio_base64": _audio_payload(2 * 1024 * 1024 + 1)},
    )

    assert response.status_code == 422


def test_gemini_audio_transcription_uses_audio_specific_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    class FakeClient:
        def __init__(self, *, timeout: float) -> None:
            observed["timeout"] = timeout

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def post(self, *_: object, **__: object) -> httpx.Response:
            return httpx.Response(
                200,
                json={"candidates": [{"content": {"parts": [{"text": "ventas"}]}}]},
            )

    monkeypatch.setattr(ai_service.settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(ai_service.httpx, "Client", FakeClient)

    assert ai_service.transcribe_audio_prompt("YQ==", "audio/mp4") == "ventas"
    assert observed["timeout"] == 35.0
    assert ai_service._TIMEOUT_SECONDS == 8.0
