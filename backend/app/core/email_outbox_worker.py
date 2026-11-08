from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.brevo_email import send_transactional_email
from app.core.config import settings
from app.core.models import EmailOutbox


def process_email_outbox(db: Session, *, limit: int | None = None) -> int:
    if not settings.brevo_api_key or not settings.brevo_sender_email:
        return 0
    now = datetime.now(UTC)
    rows = db.scalars(
        select(EmailOutbox).where(
            EmailOutbox.status.in_(("PENDING", "RETRY")),
            EmailOutbox.next_attempt_at <= now,
            or_(EmailOutbox.leased_until.is_(None), EmailOutbox.leased_until < now),
        ).order_by(EmailOutbox.id).with_for_update(skip_locked=True).limit(limit or settings.email_worker_batch_size)
    ).all()
    processed = 0
    for row in rows:
        row.leased_until = now + timedelta(minutes=5)
        row.attempts += 1
        try:
            send_transactional_email(recipient_email=row.recipient_email, subject=row.subject, html_content=row.html_body, text_content=row.text_body)
        except Exception as exc:
            row.status = "RETRY"
            row.last_error = type(exc).__name__[:500]
            row.next_attempt_at = now + timedelta(seconds=min(3600, 2 ** min(row.attempts, 10)))
        else:
            row.status = "SENT"
            row.sent_at = now
            row.last_error = None
        row.leased_until = None
        processed += 1
    db.commit()
    return processed


def run_worker() -> None:
    import time
    from app.core.database import SessionLocal
    while True:
        with SessionLocal() as db:
            process_email_outbox(db)
        time.sleep(10)
