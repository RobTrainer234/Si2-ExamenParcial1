"""Add email verification and confirmation outbox state."""
from alembic import op
import sqlalchemy as sa

revision = "w5s7u9x1z3b5"
down_revision = "v4r6t8z0b2d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_verification_challenges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("send_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("capability_hash", sa.String(64)),
        sa.Column("capability_expires_at", sa.DateTime(timezone=True)),
        sa.Column("capability_bound_pending_id", sa.Integer()),
        sa.UniqueConstraint("email", name="uq_email_verification_email"),
    )
    op.create_index("ix_email_verification_challenges_email", "email_verification_challenges", ["email"])
    op.create_table(
        "email_outbox",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(80), nullable=False),
        sa.Column("dedupe_key", sa.String(255), nullable=False),
        sa.Column("recipient_email", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=False),
        sa.Column("text_body", sa.Text()),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("leased_until", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.String(500)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("dedupe_key", name="uq_email_outbox_dedupe_key"),
    )
    op.create_index("ix_email_outbox_status_next_attempt", "email_outbox", ["status", "next_attempt_at"])
    with op.batch_alter_table("pending_paid_signups") as batch_op:
        batch_op.add_column(sa.Column("checkout_capability_hash", sa.String(64)))
        batch_op.add_column(sa.Column("capability_expires_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    with op.batch_alter_table("pending_paid_signups") as batch_op:
        batch_op.drop_column("capability_expires_at")
        batch_op.drop_column("checkout_capability_hash")
    op.drop_index("ix_email_outbox_status_next_attempt", table_name="email_outbox")
    op.drop_table("email_outbox")
    op.drop_index("ix_email_verification_challenges_email", table_name="email_verification_challenges")
    op.drop_table("email_verification_challenges")
