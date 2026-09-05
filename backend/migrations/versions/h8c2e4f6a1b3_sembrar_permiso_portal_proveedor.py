"""Agrega el permiso del portal de proveedor.

Revision ID: h8c2e4f6a1b3
Revises: g7b9d1e3f5a7
"""

from alembic import op


revision = "h8c2e4f6a1b3"
down_revision = "g7b9d1e3f5a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("INSERT INTO permisos (code, name, is_active) VALUES ('suppliers.portal', 'Consultar portal de proveedor', TRUE) ON CONFLICT (code) DO NOTHING")
    op.execute("INSERT INTO rol_permisos (role_id, permission_id) SELECT r.id, p.id FROM roles r CROSS JOIN permisos p WHERE r.code = 'SUPPLIER' AND p.code = 'suppliers.portal' ON CONFLICT DO NOTHING")


def downgrade() -> None:
    op.execute("DELETE FROM rol_permisos WHERE permission_id = (SELECT id FROM permisos WHERE code = 'suppliers.portal')")
    op.execute("DELETE FROM permisos WHERE code = 'suppliers.portal'")
