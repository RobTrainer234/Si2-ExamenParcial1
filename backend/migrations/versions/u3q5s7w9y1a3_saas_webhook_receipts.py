"""Persist SaaS Stripe provider identifiers and webhook receipts."""

from alembic import op
import sqlalchemy as sa

revision = "u3q5s7w9y1a3"
down_revision = "t2p4r6v8x0z2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("subscriptions", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("provider_customer_id", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("provider_subscription_id", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("billing_interval", sa.String(length=10), nullable=True))
        batch_op.create_unique_constraint("uq_subscriptions_provider_subscription_id", ["provider_subscription_id"])
    op.create_index("ix_subscriptions_provider_customer_id", "subscriptions", ["provider_customer_id"])
    op.create_index("ix_subscriptions_provider_subscription_id", "subscriptions", ["provider_subscription_id"])
    op.create_table(
        "processed_stripe_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_processed_stripe_events_event_id"),
    )


def downgrade() -> None:
    op.drop_table("processed_stripe_events")
    op.drop_index("ix_subscriptions_provider_subscription_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_provider_customer_id", table_name="subscriptions")
    with op.batch_alter_table("subscriptions", recreate="always") as batch_op:
        batch_op.drop_constraint("uq_subscriptions_provider_subscription_id", type_="unique")
        batch_op.drop_column("billing_interval")
        batch_op.drop_column("provider_subscription_id")
        batch_op.drop_column("provider_customer_id")
