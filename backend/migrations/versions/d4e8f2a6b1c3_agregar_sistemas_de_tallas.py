"""Add size types and product size systems.

Revision ID: d4e8f2a6b1c3
Revises: c3d7e9f1a2b4
"""

from alembic import op
import sqlalchemy as sa


revision = "d4e8f2a6b1c3"
down_revision = "c3d7e9f1a2b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tallas", sa.Column("size_type", sa.String(length=16), nullable=False, server_default="ALPHA"))
    op.add_column("tallas", sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("productos", sa.Column("size_system", sa.String(length=16), nullable=False, server_default="ALPHA"))

    connection = op.get_bind()
    connection.execute(sa.text("UPDATE tallas SET size_type = 'NUMERIC', sort_order = CAST(name AS INTEGER) WHERE name ~ '^[0-9]+$'"))
    connection.execute(sa.text("UPDATE tallas SET size_type = 'ONE_SIZE', sort_order = 999 WHERE lower(name) IN ('unica', 'única', 'one size', 'os')"))
    connection.execute(sa.text("UPDATE tallas SET sort_order = CASE upper(name) WHEN 'XS' THEN 10 WHEN 'S' THEN 20 WHEN 'M' THEN 30 WHEN 'L' THEN 40 WHEN 'XL' THEN 50 WHEN 'XXL' THEN 60 ELSE 100 END WHERE size_type = 'ALPHA' AND sort_order = 0"))
    connection.execute(sa.text("UPDATE productos SET size_system = CASE WHEN EXISTS (SELECT 1 FROM variantes_producto v JOIN tallas t ON t.id = v.size_id WHERE v.product_id = productos.id AND t.size_type = 'NUMERIC') THEN 'NUMERIC' WHEN EXISTS (SELECT 1 FROM variantes_producto v JOIN tallas t ON t.id = v.size_id WHERE v.product_id = productos.id AND t.size_type = 'ONE_SIZE') THEN 'ONE_SIZE' ELSE 'ALPHA' END"))


def downgrade() -> None:
    op.drop_column("productos", "size_system")
    op.drop_column("tallas", "sort_order")
    op.drop_column("tallas", "size_type")
