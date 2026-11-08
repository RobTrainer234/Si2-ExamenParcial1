from datetime import UTC, datetime, timedelta
import json
from decimal import Decimal

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.models import Base, EmailOutbox, EmailVerificationChallenge, SubscriptionPlan
from app.core import brevo_email
from app.core import email_outbox_worker
from app.modules.subscriptions.schemas import EmailVerificationVerifyRequest, PaidCheckoutRequest
from app.modules.subscriptions.service import create_email_verification, verify_email_code


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_email_verification_request_requires_six_numeric_digits():
    request = EmailVerificationVerifyRequest(email="ada@example.com", code="123456")
    assert request.code == "123456"

    for code in ("12345", "1234567", "12345a", "abcdef"):
        with pytest.raises(ValidationError):
            EmailVerificationVerifyRequest(email="ada@example.com", code=code)


def test_start_verification_stores_only_keyed_code_hash_and_sends_brevo(monkeypatch, db):
    monkeypatch.setattr(brevo_email.settings, "brevo_api_key", "brevo-test")
    monkeypatch.setattr(brevo_email.settings, "brevo_sender_email", "verified@example.com")
    captured = {}

    def handler(request):
        captured["request"] = request
        return httpx.Response(201, json={"messageId": "<id>"}, request=request)

    monkeypatch.setattr(brevo_email.httpx, "post", lambda *args, **kwargs: httpx.Client(transport=httpx.MockTransport(handler)).post(*args, **kwargs))
    result = create_email_verification(db, "Ada@Example.com")
    challenge = db.query(EmailVerificationChallenge).one()
    assert result.email_sent is True
    assert len(challenge.code_hash) == 64
    assert "code" not in result.model_dump()
    assert "123456" not in challenge.code_hash
    assert captured["request"].headers["api-key"] == "brevo-test"
    payload = json.loads(captured["request"].content)
    assert payload["sender"] == {"email": "verified@example.com"}
    assert payload["to"] == [{"email": "ada@example.com"}]
    assert payload["subject"] == "Verificá tu correo electrónico"
    assert "Tu código de verificación es" in payload["htmlContent"]
    assert "Vence en 10 minutos" in payload["htmlContent"]
    assert "Your verification code" not in payload["htmlContent"]


def test_verify_code_returns_one_time_checkout_capability_and_never_persists_plaintext(db, monkeypatch):
    monkeypatch.setattr(brevo_email.settings, "brevo_api_key", "brevo-test")
    monkeypatch.setattr(brevo_email.settings, "brevo_sender_email", "verified@example.com")
    monkeypatch.setattr(brevo_email, "send_transactional_email", lambda **_: None)
    monkeypatch.setattr(brevo_email, "generate_verification_code", lambda: "123456")
    create_email_verification(db, "ada@example.com")
    challenge = db.query(EmailVerificationChallenge).one()
    code = "123456"
    result = verify_email_code(db, "ADA@example.com", code)
    assert result.checkout_capability
    assert db.query(EmailVerificationChallenge).one().verified_at is not None
    assert db.query(EmailVerificationChallenge).one().code_hash != code
    with pytest.raises(Exception):
        verify_email_code(db, "ada@example.com", code)


def test_invalid_code_attempt_is_persisted_after_request_rollback(db, monkeypatch):
    monkeypatch.setattr(brevo_email, "send_transactional_email", lambda **_: None)
    monkeypatch.setattr(brevo_email, "generate_verification_code", lambda: "123456")
    create_email_verification(db, "ada@example.com")
    db.commit()

    with pytest.raises(Exception):
        verify_email_code(db, "ada@example.com", "000000")

    db.rollback()
    db.close()
    with Session(db.bind) as reopened_db:
        challenge = reopened_db.query(EmailVerificationChallenge).one()
        assert challenge.attempts == 1

    for _ in range(4):
        with Session(db.bind) as attempt_db:
            with pytest.raises(Exception):
                verify_email_code(attempt_db, "ada@example.com", "000000")
            attempt_db.rollback()

    with Session(db.bind) as limited_db:
        with pytest.raises(Exception):
            verify_email_code(limited_db, "ada@example.com", "000000")
        limited_db.rollback()
        assert limited_db.query(EmailVerificationChallenge).one().attempts == 5


def test_expired_and_attempt_limited_codes_fail_closed(db, monkeypatch):
    challenge = EmailVerificationChallenge(
        email="ada@example.com", code_hash="x" * 64,
        expires_at=datetime.now(UTC) - timedelta(minutes=1), attempts=5,
        send_count=1, window_started_at=datetime.now(UTC), last_sent_at=datetime.now(UTC),
    )
    db.add(challenge)
    db.commit()
    with pytest.raises(Exception):
        verify_email_code(db, "ada@example.com", "000000")


def test_paid_request_requires_capability():
    with pytest.raises(Exception):
        PaidCheckoutRequest(
            company_name="Acme", first_name="Ada", last_name="Lovelace", email="ada@example.com",
            phone="70000000", password="StrongPass1!", plan_code="BASIC", billing_interval="monthly",
        )


def test_outbox_worker_marks_success_and_retries_safely(db, monkeypatch):
    monkeypatch.setattr(email_outbox_worker.settings, "brevo_api_key", "brevo-test")
    monkeypatch.setattr(email_outbox_worker.settings, "brevo_sender_email", "verified@example.com")
    db.add(EmailOutbox(kind="PAID_SIGNUP_CONFIRMATION", dedupe_key="pending:worker", recipient_email="ada@example.com", subject="Welcome", html_body="<p>Welcome</p>"))
    db.commit()
    monkeypatch.setattr(email_outbox_worker, "send_transactional_email", lambda **_: None)
    assert email_outbox_worker.process_email_outbox(db) == 1
    assert db.query(EmailOutbox).one().status == "SENT"

    retry = EmailOutbox(kind="PAID_SIGNUP_CONFIRMATION", dedupe_key="pending:retry", recipient_email="ada@example.com", subject="Welcome", html_body="<p>Welcome</p>")
    db.add(retry)
    db.commit()
    def fail(**_):
        raise RuntimeError("provider secret must not leak")
    monkeypatch.setattr(email_outbox_worker, "send_transactional_email", fail)
    email_outbox_worker.process_email_outbox(db)
    assert retry.status == "RETRY"
    assert retry.last_error == "RuntimeError"


def test_outbox_is_deduplicated_by_activation(db):
    record = EmailOutbox(kind="PAID_SIGNUP_CONFIRMATION", dedupe_key="pending:1", recipient_email="ada@example.com", subject="Welcome", html_body="<p>Welcome</p>")
    db.add(record)
    db.commit()
    db.add(EmailOutbox(kind="PAID_SIGNUP_CONFIRMATION", dedupe_key="pending:1", recipient_email="ada@example.com", subject="Welcome", html_body="<p>Welcome</p>"))
    with pytest.raises(Exception):
        db.commit()
