"""Agregar publico objetivo a los productos."""
from alembic import op
import sqlalchemy as sa


revision = "c3d7e9f1a2b4"
down_revision = "b2e6f8a4c1d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("productos", sa.Column("audience", sa.String(length=16), nullable=False, server_default="UNISEX"))
    op.create_index("ix_productos_audience", "productos", ["audience"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_productos_audience", table_name="productos")
    op.drop_column("productos", "audience")
