from datetime import UTC, datetime, timedelta
from decimal import Decimal
from urllib.parse import parse_qs

import httpx
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.models import Base, EmailOutbox, EmailVerificationChallenge, PendingPaidSignup, ProcessedStripeEvent, Role, Subscription, SubscriptionPlan, Tenant, User
from app.main import app
from app.modules.subscriptions.schemas import PaidCheckoutRequest, PaidCheckoutStatusResponse
from app.modules.subscriptions.service import create_paid_checkout
from app.modules.subscriptions import stripe_service


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        from app.modules.subscriptions.service import _secret_hash
        now = datetime.now(UTC)
        session.add(EmailVerificationChallenge(email="ada@example.com", code_hash="x" * 64, expires_at=now + timedelta(minutes=10), attempts=0, send_count=1, window_started_at=now, last_sent_at=now, verified_at=now, capability_hash=_secret_hash("test-capability"), capability_expires_at=now + timedelta(minutes=20)))
        session.commit()
        yield session


def test_stripe_checkout_posts_form_mapping_and_preserves_idempotency(monkeypatch):
    monkeypatch.setattr(stripe_service.settings, "stripe_secret_key", "sk_test_no_network")
    captured = {}

    def handle_request(request):
        captured["request"] = request
        return httpx.Response(
            200,
            json={"id": "cs_test_123", "url": "https://checkout.stripe.test/cs_test_123"},
            request=request,
        )

    transport = httpx.MockTransport(handle_request)
    client = httpx.Client(transport=transport)
    monkeypatch.setattr(
        stripe_service.httpx,
        "post",
        lambda url, *, headers, data, timeout: client.post(
            url, headers=headers, data=data, timeout=timeout
        ),
    )

    result = stripe_service.create_checkout_session(
        mode="subscription",
        success_url="https://app.test/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://app.test/cancel",
        line_items=[
            {
                "price_data": {
                    "currency": "bob",
                    "unit_amount": 149900,
                    "recurring": {"interval": "year"},
                    "product_data": {"name": "Professional"},
                }
            }
        ],
        metadata={"pending_signup_id": 42},
        idempotency_key="pending-42",
    )
    client.close()

    request = captured["request"]
    assert request.headers["content-type"] == "application/x-www-form-urlencoded"
    assert parse_qs(request.content.decode()) == {
        "mode": ["subscription"],
        "success_url": ["https://app.test/success?session_id={CHECKOUT_SESSION_ID}"],
        "cancel_url": ["https://app.test/cancel"],
        "line_items[0][price_data][currency]": ["bob"],
        "line_items[0][price_data][unit_amount]": ["149900"],
        "line_items[0][price_data][recurring][interval]": ["year"],
        "line_items[0][price_data][product_data][name]": ["Professional"],
        "line_items[0][quantity]": ["1"],
        "metadata[pending_signup_id]": ["42"],
    }
    assert request.headers["Idempotency-Key"] == "pending-42"
    assert result == {"id": "cs_test_123", "url": "https://checkout.stripe.test/cs_test_123"}


def test_paid_checkout_uses_server_plan_amount_and_recurring_interval(monkeypatch, db):
    plan = SubscriptionPlan(
        code="PROFESSIONAL",
        name="Professional",
        price_monthly=Decimal("149.90"),
        price_annual=Decimal("1499.00"),
        currency="BOB",
        max_active_branches=5,
        is_active=True,
    )
    db.add(plan)
    db.commit()

    captured = {}

    def fake_create_session(**kwargs):
        captured.update(kwargs)
        return {"id": "cs_test_123", "url": "https://checkout.stripe.test/cs_test_123"}

    monkeypatch.setattr("app.modules.subscriptions.stripe_service.create_checkout_session", fake_create_session)

    result = create_paid_checkout(
        db,
        PaidCheckoutRequest(
            company_name="Acme",
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            phone="70000000",
            password="StrongPass1!",
            plan_code="PROFESSIONAL",
            billing_interval="annual",
            checkout_capability="test-capability",
        ),
    )

    assert captured["line_items"][0]["price_data"]["unit_amount"] == 149900
    assert captured["line_items"][0]["price_data"]["currency"] == "bob"
    assert captured["line_items"][0]["price_data"]["recurring"]["interval"] == "year"
    assert captured["success_url"].endswith("/subscription/success?session_id={CHECKOUT_SESSION_ID}")
    assert "plan=PROFESSIONAL" in captured["cancel_url"]
    assert "billing=annual" in captured["cancel_url"]
    assert result.session_id == "cs_test_123"
    assert db.query(PendingPaidSignup).count() == 1
    assert db.query(PendingPaidSignup).one().status == "CHECKOUT_CREATED"


def test_paid_checkout_status_is_coarse_and_does_not_query_stripe(db):
    from app.modules.subscriptions.service import get_paid_checkout_status

    pending = _pending_for_webhook(db, session_id="cs_status")
    result = get_paid_checkout_status(db, "cs_status")
    assert result == {"status": "CHECKOUT_CREATED"}

    pending.status = "COMPLETED"
    db.commit()
    assert get_paid_checkout_status(db, "cs_status") == {"status": "COMPLETED"}


def test_paid_checkout_status_http_response_has_security_headers(monkeypatch):
    monkeypatch.setattr(
        "app.modules.subscriptions.router.service.get_paid_checkout_status",
        lambda _db, _session_id: {"status": "CHECKOUT_CREATED"},
    )

    def override_get_db():
        yield None

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).get("/api/v1/subscriptions/paid-checkout/status?session_id=cs_headers")
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_paid_checkout_status_preserves_email_conflict_state(db):
    from app.modules.subscriptions.service import get_paid_checkout_status

    _pending_for_webhook(db, session_id="cs_conflict", status="EMAIL_CONFLICT")

    assert get_paid_checkout_status(db, "cs_conflict") == {"status": "EMAIL_CONFLICT"}
    assert PaidCheckoutStatusResponse(status="EMAIL_CONFLICT").status == "EMAIL_CONFLICT"


def test_paid_checkout_status_unknown_and_invalid_session_ids_are_distinct(db):
    from app.modules.subscriptions.service import get_paid_checkout_status

    with pytest.raises(Exception) as unknown:
        get_paid_checkout_status(db, "cs_unknown")
    assert getattr(unknown.value, "status_code", None) == 404
    assert unknown.value.detail["code"] == "CHECKOUT_SESSION_NOT_FOUND"

    with pytest.raises(Exception) as invalid:
        get_paid_checkout_status(db, "   ")
    assert getattr(invalid.value, "status_code", None) == 400
    assert invalid.value.detail["code"] == "CHECKOUT_SESSION_INVALID"


def test_paid_checkout_rejects_invalid_plan_or_interval(db):
    with pytest.raises(Exception):
        create_paid_checkout(
            db,
            PaidCheckoutRequest(
                company_name="Acme",
                first_name="Ada",
                last_name="Lovelace",
                email="ada@example.com",
                phone="70000000",
                password="StrongPass1!",
                plan_code="UNKNOWN",
                billing_interval="monthly",
            ),
        )

    with pytest.raises(ValueError):
        PaidCheckoutRequest(
            company_name="Acme",
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            phone="70000000",
            password="StrongPass1!",
            plan_code="PROFESSIONAL",
            billing_interval="weekly",
        )


def test_paid_checkout_does_not_create_access_entities(db):
    plan = SubscriptionPlan(
        code="BASIC",
        name="Basic",
        price_monthly=Decimal("49.00"),
        price_annual=Decimal("490.00"),
        currency="BOB",
        max_active_branches=2,
        is_active=True,
    )
    db.add(plan)
    db.commit()

    result = create_paid_checkout(
        db,
        PaidCheckoutRequest(
            company_name="Acme",
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            phone="70000000",
            password="StrongPass1!",
            plan_code="BASIC",
            billing_interval="monthly",
            checkout_capability="test-capability",
        ),
        session_creator=lambda **_: {"id": "cs_test_456", "url": "https://checkout.stripe.test/cs_test_456"},
    )

    assert result.session_url.startswith("https://checkout.stripe.test/")
    assert db.query(PendingPaidSignup).count() == 1
    assert db.execute(text("SELECT COUNT(*) FROM tenants")).scalar_one() == 0
    assert db.execute(text("SELECT COUNT(*) FROM usuarios")).scalar_one() == 0


def _paid_request(**overrides):
    values = {
        "company_name": "Acme",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "phone": "70000000",
        "password": "StrongPass1!",
        "plan_code": "BASIC",
        "billing_interval": "monthly",
        "checkout_capability": "test-capability",
    }
    values.update(overrides)
    return PaidCheckoutRequest(**values)


def test_paid_checkout_rejects_zero_price_before_stripe_request(db):
    db.add(
        SubscriptionPlan(
            code="BASIC",
            name="Basic",
            price_monthly=Decimal("0.00"),
            price_annual=Decimal("490.00"),
            currency="BOB",
            max_active_branches=2,
            is_active=True,
        )
    )
    db.commit()
    called = False

    def fail_if_called(**_kwargs):
        nonlocal called
        called = True
        raise AssertionError("Stripe must not be called for a zero-price interval")

    with pytest.raises(Exception):
        create_paid_checkout(db, _paid_request(), session_creator=fail_if_called)

    assert called is False
    assert db.query(PendingPaidSignup).count() == 0


def test_identical_retry_reuses_pending_attempt_and_stripe_idempotency_key(db):
    db.add(
        SubscriptionPlan(
            code="BASIC",
            name="Basic",
            price_monthly=Decimal("49.00"),
            price_annual=Decimal("490.00"),
            currency="BOB",
            max_active_branches=2,
            is_active=True,
        )
    )
    db.commit()
    calls = []

    def fake_create_session(**kwargs):
        calls.append(kwargs)
        return {"id": "cs_test_retry", "url": "https://checkout.stripe.test/cs_test_retry"}

    request = _paid_request()
    first = create_paid_checkout(db, request, session_creator=fake_create_session)
    second = create_paid_checkout(db, request, session_creator=fake_create_session)

    assert first == second
    assert len(calls) == 1
    assert calls[0]["idempotency_key"]
    assert db.query(PendingPaidSignup).count() == 1


def test_stripe_transport_retry_reuses_persisted_idempotency_key(db):
    db.add(
        SubscriptionPlan(
            code="BASIC",
            name="Basic",
            price_monthly=Decimal("49.00"),
            price_annual=Decimal("490.00"),
            currency="BOB",
            max_active_branches=2,
            is_active=True,
        )
    )
    db.commit()
    idempotency_keys = []

    def fail_after_request(**kwargs):
        idempotency_keys.append(kwargs["idempotency_key"])
        raise RuntimeError("Simulated lost response after Stripe created the session")

    with pytest.raises(RuntimeError):
        create_paid_checkout(db, _paid_request(), session_creator=fail_after_request)

    pending = db.query(PendingPaidSignup).one()
    assert pending.status == "PENDING"
    assert pending.stripe_idempotency_key

    def recover_same_stripe_session(**kwargs):
        idempotency_keys.append(kwargs["idempotency_key"])
        return {"id": "cs_test_recovered", "url": "https://checkout.stripe.test/cs_test_recovered"}

    result = create_paid_checkout(db, _paid_request(), session_creator=recover_same_stripe_session)

    assert idempotency_keys == [pending.stripe_idempotency_key, pending.stripe_idempotency_key]
    assert result.session_id == "cs_test_recovered"
    assert db.query(PendingPaidSignup).one().status == "CHECKOUT_CREATED"


def test_capability_cannot_create_second_signup_after_original_is_terminal(db):
    db.add(
        SubscriptionPlan(
            code="BASIC",
            name="Basic",
            price_monthly=Decimal("49.00"),
            price_annual=Decimal("490.00"),
            currency="BOB",
            max_active_branches=2,
            is_active=True,
        )
    )
    db.commit()

    create_paid_checkout(
        db,
        _paid_request(),
        session_creator=lambda **_: {"id": "cs_test_terminal", "url": "https://checkout.stripe.test/cs_test_terminal"},
    )
    pending = db.query(PendingPaidSignup).one()
    pending.status = "COMPLETED"
    db.commit()

    with pytest.raises(Exception) as error:
        create_paid_checkout(
            db,
            _paid_request(company_name="Second Company"),
            session_creator=lambda **_: pytest.fail("Stripe must not be called"),
        )

    assert getattr(error.value, "status_code", None) == 409
    assert error.value.detail["code"] in {"PAID_SIGNUP_CAPABILITY_REUSED", "PAID_SIGNUP_IN_PROGRESS"}
    assert db.query(PendingPaidSignup).count() == 1


def test_same_email_with_different_details_returns_conflict_without_stripe_request(db):
    db.add(
        SubscriptionPlan(
            code="BASIC",
            name="Basic",
            price_monthly=Decimal("49.00"),
            price_annual=Decimal("490.00"),
            currency="BOB",
            max_active_branches=2,
            is_active=True,
        )
    )
    db.commit()
    calls = []

    def fake_create_session(**kwargs):
        calls.append(kwargs)
        return {"id": "cs_test_conflict", "url": "https://checkout.stripe.test/cs_test_conflict"}

    create_paid_checkout(db, _paid_request(), session_creator=fake_create_session)
    with pytest.raises(Exception) as error:
        create_paid_checkout(db, _paid_request(company_name="Other Company"), session_creator=fake_create_session)

    assert getattr(error.value, "status_code", None) == 409
    assert len(calls) == 1


def test_pending_paid_signup_migration_accepts_initial_null_idempotency_key(monkeypatch):
    from importlib.util import module_from_spec, spec_from_file_location
    from pathlib import Path

    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import inspect

    migration_path = Path(__file__).resolve().parents[1] / "migrations" / "versions" / "t2p4r6v8x0z2_pending_paid_signups.py"
    spec = spec_from_file_location("pending_paid_signups_migration", migration_path)
    assert spec and spec.loader
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE subscription_plans (id INTEGER PRIMARY KEY)"))
        monkeypatch.setattr(migration, "op", Operations(MigrationContext.configure(connection)))
        migration.upgrade()
        columns = {column["name"]: column for column in inspect(connection).get_columns("pending_paid_signups")}
        assert columns["stripe_idempotency_key"]["nullable"] is True
        connection.execute(
            text(
                """
                INSERT INTO pending_paid_signups
                    (company_name, first_name, last_name, email, phone, password_hash,
                     plan_id, billing_interval, amount, currency, stripe_idempotency_key)
                VALUES
                    (:company_name, :first_name, :last_name, :email, :phone, :password_hash,
                     :plan_id, :billing_interval, :amount, :currency, NULL)
                """
            ),
            {
                "company_name": "Acme",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada@example.com",
                "phone": "70000000",
                "password_hash": "hashed",
                "plan_id": 1,
                "billing_interval": "monthly",
                "amount": "49.00",
                "currency": "BOB",
            },
        )
        assert connection.execute(text("SELECT COUNT(*) FROM pending_paid_signups")).scalar_one() == 1


def _pending_for_webhook(db, *, session_id="cs_paid", status="CHECKOUT_CREATED"):
    plan = SubscriptionPlan(
        code="BASIC", name="Basic", price_monthly=Decimal("49.00"), price_annual=Decimal("490.00"),
        currency="BOB", max_active_branches=2, is_active=True,
    )
    role = Role(code="ADMIN", name="Administrator", is_active=True)
    db.add_all([plan, role])
    db.flush()
    pending = PendingPaidSignup(
        company_name="Acme", first_name="Ada", last_name="Lovelace", email="ada@example.com",
        phone="70000000", password_hash="hashed-password", plan_id=plan.id, billing_interval="monthly",
        amount=Decimal("49.00"), currency="bob", status=status, stripe_session_id=session_id,
    )
    db.add(pending)
    db.commit()
    return pending


def _checkout_event(session_id="cs_paid", *, event_id="evt_paid", payment_status="paid", mode="subscription", metadata=None):
    return {
        "id": event_id,
        "type": "checkout.session.completed",
        "data": {"object": {
            "id": session_id, "mode": mode, "payment_status": payment_status,
            "customer": "cus_123", "subscription": "sub_123",
            "metadata": metadata or {"pending_signup_id": "1"},
        }},
    }


def test_webhook_missing_secret_and_signature_fail_closed(monkeypatch, db):
    _pending_for_webhook(db)
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.settings.stripe_webhook_secret", None)
    with pytest.raises(Exception):
        stripe_service.handle_webhook(db, b"{}", None)


def test_invalid_signature_and_malformed_json_are_rejected(monkeypatch, db):
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.settings.stripe_webhook_secret", "whsec_test")
    with pytest.raises(Exception):
        stripe_service.handle_webhook(db, b"{}", "invalid")
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.verify_webhook_signature", lambda *_: True)
    with pytest.raises(Exception):
        stripe_service.handle_webhook(db, b"not-json", "valid-signature")


def test_valid_paid_checkout_webhook_activates_exactly_one_access_graph(monkeypatch, db):
    monkeypatch.setattr(settings, "frontend_url", "https://app.example.com")
    pending = _pending_for_webhook(db)
    pending.first_name = '<img src=x onerror="alert(1)">'
    db.commit()
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.settings.stripe_webhook_secret", "whsec_test")
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.verify_webhook_signature", lambda *_: True)
    event = _checkout_event(metadata={"pending_signup_id": str(pending.id)})
    result = stripe_service.handle_webhook(db, __import__("json").dumps(event).encode(), "valid-signature")
    assert result["received"] is True
    assert db.query(Tenant).count() == 1
    assert db.query(User).count() == 1
    assert db.query(Subscription).count() == 1
    assert db.query(PendingPaidSignup).one().status == "COMPLETED"
    assert db.query(User).one().tenant_id == db.query(Tenant).one().id
    assert db.query(Subscription).one().status == "ACTIVE"
    assert db.query(User).one().refresh_tokens == []
    assert db.query(EmailOutbox).count() == 1
    outbox = db.query(EmailOutbox).one()
    assert outbox.subject == "Tu cuenta de FashionStore está lista"
    assert "Tu plan Basic" in outbox.text_body
    assert "mensual" in outbox.text_body
    assert "49.00 BOB" in outbox.text_body
    assert "https://app.example.com/login" in outbox.text_body
    assert "iniciá sesión" in outbox.text_body.lower()
    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" in outbox.html_body
    assert '<img src=x onerror="alert(1)">' not in outbox.html_body
    assert "StrongPass" not in outbox.html_body
    duplicate = stripe_service.handle_webhook(db, __import__("json").dumps(event).encode(), "valid-signature")
    assert duplicate["duplicate"] is True
    assert db.query(EmailOutbox).count() == 1


def test_unpaid_mismatched_or_expired_checkout_never_activates(monkeypatch, db):
    pending = _pending_for_webhook(db)
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.settings.stripe_webhook_secret", "whsec_test")
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.verify_webhook_signature", lambda *_: True)
    import json
    unpaid = _checkout_event(metadata={"pending_signup_id": str(pending.id)}, payment_status="unpaid")
    assert stripe_service.handle_webhook(db, json.dumps(unpaid).encode(), "valid-signature")["activated"] is False
    mismatch = _checkout_event(event_id="evt_mismatch", session_id="cs_other", metadata={"pending_signup_id": str(pending.id)})
    assert stripe_service.handle_webhook(db, json.dumps(mismatch).encode(), "valid-signature")["activated"] is False
    expired = {"id": "evt_expired", "type": "checkout.session.expired", "data": {"object": {
        "id": pending.stripe_session_id, "metadata": {"pending_signup_id": str(pending.id)}
    }}}
    assert stripe_service.handle_webhook(db, json.dumps(expired).encode(), "valid-signature")["expired"] is True
    assert db.query(Tenant).count() == 0
    assert db.query(PendingPaidSignup).one().status == "EXPIRED"


def test_paid_checkout_rejects_email_registered_in_another_tenant_without_stripe(monkeypatch, db):
    plan = SubscriptionPlan(
        code="BASIC", name="Basic", price_monthly=Decimal("49.00"), price_annual=Decimal("490.00"),
        currency="BOB", max_active_branches=2, is_active=True,
    )
    role = Role(code="ADMIN", name="Administrator", is_active=True)
    tenant = Tenant(name="Existing", status="ACTIVE")
    db.add_all([plan, role, tenant])
    db.flush()
    db.add(User(
        tenant_id=tenant.id, role_id=role.id, first_name="Existing", last_name="Admin",
        email="ada@example.com", phone="70000001", password_hash="hashed", is_active=True,
    ))
    db.commit()
    called = False

    def fail_if_called(**_kwargs):
        nonlocal called
        called = True
        raise AssertionError("Stripe must not be called for a globally registered email")

    with pytest.raises(Exception) as error:
        create_paid_checkout(db, _paid_request(), session_creator=fail_if_called)

    assert getattr(error.value, "status_code", None) == 409
    assert called is False
    assert db.query(PendingPaidSignup).count() == 0


def test_webhook_receipt_unique_collision_returns_idempotent_success(monkeypatch, db):
    _pending_for_webhook(db)
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.settings.stripe_webhook_secret", "whsec_test")
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.verify_webhook_signature", lambda *_: True)
    import json
    event = _checkout_event(event_id="evt_concurrent", metadata={"pending_signup_id": "1"})
    original_flush = db.flush
    collided = False

    def flush_with_concurrent_receipt(*args, **kwargs):
        nonlocal collided
        if not collided:
            collided = True
            db.rollback()
            db.add(ProcessedStripeEvent(event_id="evt_concurrent", event_type="checkout.session.completed"))
            original_flush()
            db.commit()
            raise IntegrityError("duplicate receipt", {}, Exception("unique violation"))
        return original_flush(*args, **kwargs)

    monkeypatch.setattr(db, "flush", flush_with_concurrent_receipt)
    result = stripe_service.handle_webhook(db, json.dumps(event).encode(), "valid-signature")

    assert result["received"] is True
    assert result["duplicate"] is True
    assert db.query(Tenant).count() == 0
    assert db.query(PendingPaidSignup).one().status == "CHECKOUT_CREATED"


def test_stale_paid_event_cannot_reactivate_canceled_subscription(monkeypatch, db):
    pending = _pending_for_webhook(db)
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.settings.stripe_webhook_secret", "whsec_test")
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.verify_webhook_signature", lambda *_: True)
    import json
    stripe_service.handle_webhook(db, json.dumps({**_checkout_event(metadata={"pending_signup_id": str(pending.id)}), "created": 50}).encode(), "valid-signature")
    canceled = {"id": "evt_cancel_ordered", "type": "customer.subscription.deleted", "created": 200,
                "data": {"object": {"id": "sub_123"}}}
    stale_paid = {"id": "evt_stale_paid", "type": "invoice.paid", "created": 100,
                  "data": {"object": {"subscription": "sub_123"}}}
    stripe_service.handle_webhook(db, json.dumps(canceled).encode(), "valid-signature")
    stripe_service.handle_webhook(db, json.dumps(stale_paid).encode(), "valid-signature")
    assert db.query(Subscription).one().status == "CANCELLED"


def test_newer_paid_event_restores_suspended_subscription(monkeypatch, db):
    pending = _pending_for_webhook(db)
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.settings.stripe_webhook_secret", "whsec_test")
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.verify_webhook_signature", lambda *_: True)
    import json
    stripe_service.handle_webhook(db, json.dumps({**_checkout_event(metadata={"pending_signup_id": str(pending.id)}), "created": 50}).encode(), "valid-signature")
    failed = {"id": "evt_failed_ordered", "type": "invoice.payment_failed", "created": 100,
              "data": {"object": {"subscription": "sub_123"}}}
    paid = {"id": "evt_paid_ordered", "type": "invoice.paid", "created": 200,
            "data": {"object": {"subscription": "sub_123"}}}
    stripe_service.handle_webhook(db, json.dumps(failed).encode(), "valid-signature")
    stripe_service.handle_webhook(db, json.dumps(paid).encode(), "valid-signature")
    assert db.query(Subscription).one().status == "ACTIVE"


@pytest.mark.parametrize("provider_status", ["incomplete", "paused"])
def test_non_access_granting_provider_states_are_suspended(monkeypatch, db, provider_status):
    pending = _pending_for_webhook(db)
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.settings.stripe_webhook_secret", "whsec_test")
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.verify_webhook_signature", lambda *_: True)
    import json
    stripe_service.handle_webhook(db, json.dumps(_checkout_event(metadata={"pending_signup_id": str(pending.id)})).encode(), "valid-signature")
    update = {"id": f"evt_{provider_status}", "type": "customer.subscription.updated",
              "data": {"object": {"id": "sub_123", "status": provider_status}}}
    stripe_service.handle_webhook(db, json.dumps(update).encode(), "valid-signature")
    assert db.query(Subscription).one().status == "SUSPENDED"


def test_webhook_refuses_activation_if_email_became_registered(monkeypatch, db):
    pending = _pending_for_webhook(db)
    role = db.query(Role).filter_by(code="ADMIN").one()
    tenant = Tenant(name="Existing", status="ACTIVE")
    db.add(tenant)
    db.flush()
    db.add(User(tenant_id=tenant.id, role_id=role.id, first_name="Existing", last_name="Admin",
                email=pending.email, phone="70000001", password_hash="hashed", is_active=True))
    db.commit()
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.settings.stripe_webhook_secret", "whsec_test")
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.verify_webhook_signature", lambda *_: True)
    import json
    result = stripe_service.handle_webhook(db, json.dumps(_checkout_event(metadata={"pending_signup_id": str(pending.id)})).encode(), "valid-signature")
    assert result["activated"] is False
    assert result["email_conflict"] is True
    assert db.query(Tenant).count() == 1
    assert db.query(Subscription).count() == 0
    assert db.query(PendingPaidSignup).one().status == "EMAIL_CONFLICT"


def test_webhook_replay_is_idempotent_and_subscription_updates_are_restricted(monkeypatch, db):
    pending = _pending_for_webhook(db)
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.settings.stripe_webhook_secret", "whsec_test")
    monkeypatch.setattr("app.modules.subscriptions.stripe_service.verify_webhook_signature", lambda *_: True)
    import json
    event = _checkout_event(metadata={"pending_signup_id": str(pending.id)})
    stripe_service.handle_webhook(db, json.dumps(event).encode(), "valid-signature")
    replay = stripe_service.handle_webhook(db, json.dumps(event).encode(), "valid-signature")
    assert replay["duplicate"] is True
    assert db.query(Tenant).count() == db.query(User).count() == db.query(Subscription).count() == 1
    update = {"id": "evt_failed", "type": "invoice.payment_failed", "data": {"object": {"subscription": "sub_123"}}}
    stripe_service.handle_webhook(db, json.dumps(update).encode(), "valid-signature")
    assert db.query(Subscription).one().status == "SUSPENDED"
    canceled = {"id": "evt_canceled", "type": "customer.subscription.deleted", "data": {"object": {"id": "sub_123"}}}
    stripe_service.handle_webhook(db, json.dumps(canceled).encode(), "valid-signature")
    assert db.query(Subscription).one().status == "CANCELLED"
