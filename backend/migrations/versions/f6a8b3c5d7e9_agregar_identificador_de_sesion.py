"""Agregar identificador para invalidar access tokens por sesión.

Revision ID: f6a8b3c5d7e9
Revises: e5f7a9c2b4d6
"""

from alembic import op
import sqlalchemy as sa


revision = "f6a8b3c5d7e9"
down_revision = "e5f7a9c2b4d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sesiones_actualizacion", sa.Column("session_id", sa.String(length=64), nullable=True))
    op.create_index("ix_sesiones_actualizacion_session_id", "sesiones_actualizacion", ["session_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_sesiones_actualizacion_session_id", table_name="sesiones_actualizacion")
    op.drop_column("sesiones_actualizacion", "session_id")
