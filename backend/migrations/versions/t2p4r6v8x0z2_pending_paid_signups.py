"""Persist pending paid SaaS registrations for hosted checkout."""

from alembic import op
import sqlalchemy as sa

revision = "t2p4r6v8x0z2"
down_revision = "s1o3m5q7u9w1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pending_paid_signups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=150), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("billing_interval", sa.String(length=10), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="PENDING", nullable=False),
        sa.Column("stripe_session_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_session_url", sa.String(length=1000), nullable=True),
        sa.Column("stripe_idempotency_key", sa.String(length=255), nullable=True, unique=True),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_session_id", name="uq_pending_paid_signups_stripe_session_id"),
    )
    op.create_index("ix_pending_paid_signups_plan_id", "pending_paid_signups", ["plan_id"])
    op.create_index("ix_pending_paid_signups_email_status", "pending_paid_signups", ["email", "status"])
    op.create_index(
        "uq_pending_paid_signups_in_flight_email",
        "pending_paid_signups",
        ["email"],
        unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'CHECKOUT_CREATED')"),
        sqlite_where=sa.text("status IN ('PENDING', 'CHECKOUT_CREATED')"),
    )


def downgrade() -> None:
    op.drop_index("uq_pending_paid_signups_in_flight_email", table_name="pending_paid_signups")
    op.drop_index("ix_pending_paid_signups_email_status", table_name="pending_paid_signups")
    op.drop_index("ix_pending_paid_signups_plan_id", table_name="pending_paid_signups")
    op.drop_table("pending_paid_signups")
