"""Completa reglas de integridad y expiracion de reservas.

Revision ID: l3g6b8c0d2e4
Revises: k2f5a7b9c1d3
"""

from alembic import op


revision = "l3g6b8c0d2e4"
down_revision = "k2f5a7b9c1d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_reservations_status_valid",
        "reservas",
        "status IN ('PENDING', 'PREPARING', 'READY', 'ATTENDED', 'CANCELLED', 'EXPIRED')",
    )
    op.create_index("ix_reservas_status_expires_at", "reservas", ["status", "expires_at"])
    op.create_index("ix_reservas_branch_status", "reservas", ["branch_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_reservas_branch_status", table_name="reservas")
    op.drop_index("ix_reservas_status_expires_at", table_name="reservas")
    op.drop_constraint("ck_reservations_status_valid", "reservas", type_="check")
