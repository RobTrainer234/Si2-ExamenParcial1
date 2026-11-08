"""Persist Stripe event ordering metadata on subscriptions."""

from alembic import op
import sqlalchemy as sa

revision = "v4r6t8z0b2d4"
down_revision = "u3q5s7w9y1a3"
branch_labels = None
depends_on = None


def _synchronize_subscription_id_sequence() -> None:
    """Restore the recreated PostgreSQL serial sequence to the current table data."""
    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                sequence_name text;
                maximum_id bigint;
            BEGIN
                sequence_name := pg_get_serial_sequence('subscriptions', 'id');
                IF sequence_name IS NULL THEN
                    RETURN;
                END IF;

                SELECT MAX(id) INTO maximum_id FROM subscriptions;
                IF maximum_id IS NULL THEN
                    PERFORM setval(sequence_name::regclass, 1, false);
                ELSE
                    PERFORM setval(sequence_name::regclass, maximum_id, true);
                END IF;
            END
            $$;
            """
        )
    )


def upgrade() -> None:
    with op.batch_alter_table("subscriptions", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("provider_event_created_at", sa.DateTime(timezone=True), nullable=True))
    _synchronize_subscription_id_sequence()


def downgrade() -> None:
    with op.batch_alter_table("subscriptions", recreate="always") as batch_op:
        batch_op.drop_column("provider_event_created_at")
    _synchronize_subscription_id_sequence()
