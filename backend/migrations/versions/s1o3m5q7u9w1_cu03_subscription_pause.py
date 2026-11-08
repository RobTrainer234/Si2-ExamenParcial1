"""Add CU-03 subscription pause timestamp and state."""

from alembic import op
import sqlalchemy as sa

revision = "s1o3m5q7u9w1"
down_revision = "r9n2p5q7s9t1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("subscriptions", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.drop_constraint("ck_subscriptions_status_valid", type_="check")
        batch_op.create_check_constraint(
            "ck_subscriptions_status_valid",
            "status IN ('ACTIVE', 'CANCELLED', 'EXPIRED', 'SUSPENDED', 'PAUSED')",
        )


def downgrade() -> None:
    # PAUSED did not exist in the predecessor schema; preserve access blocking
    # semantics by mapping it to the legacy blocked state before rebuilding.
    op.execute("UPDATE subscriptions SET status = 'SUSPENDED' WHERE status = 'PAUSED'")
    with op.batch_alter_table("subscriptions", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_subscriptions_status_valid", type_="check")
        batch_op.drop_column("paused_at")
        batch_op.create_check_constraint(
            "ck_subscriptions_status_valid",
            "status IN ('ACTIVE', 'CANCELLED', 'EXPIRED', 'SUSPENDED')",
        )
