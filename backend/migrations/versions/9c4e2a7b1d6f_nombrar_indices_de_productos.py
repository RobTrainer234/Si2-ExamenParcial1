"""Traducir los indices de temporada y coleccion."""
from alembic import op


revision = "9c4e2a7b1d6f"
down_revision = "8b3d1e5f7a9c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('ALTER INDEX "ix_products_collection_id" RENAME TO "ix_productos_collection_id"')
    op.execute('ALTER INDEX "ix_products_season_id" RENAME TO "ix_productos_season_id"')


def downgrade() -> None:
    op.execute('ALTER INDEX "ix_productos_season_id" RENAME TO "ix_products_season_id"')
    op.execute('ALTER INDEX "ix_productos_collection_id" RENAME TO "ix_products_collection_id"')
