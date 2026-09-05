"""Traducir el indice del usuario de la bitacora."""
from alembic import op


revision = "b2e6f8a4c1d7"
down_revision = "a1d5e9c7b3f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('ALTER INDEX "ix_bitacora_user_id" RENAME TO "ix_bitacora_usuario_id"')


def downgrade() -> None:
    op.execute('ALTER INDEX "ix_bitacora_usuario_id" RENAME TO "ix_bitacora_user_id"')
