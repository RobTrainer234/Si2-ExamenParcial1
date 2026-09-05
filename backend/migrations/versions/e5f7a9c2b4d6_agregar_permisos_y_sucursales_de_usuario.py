"""Agregar permisos normalizados y asignaciones de usuarios a sucursales.

Revision ID: e5f7a9c2b4d6
Revises: d4e8f2a6b1c3
"""

from alembic import op
import sqlalchemy as sa


revision = "e5f7a9c2b4d6"
down_revision = "d4e8f2a6b1c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "permisos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("code", name="uq_permisos_code"),
    )
    op.create_table(
        "rol_permisos",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permisos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )
    op.create_table(
        "usuario_sucursales",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["sucursales.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "branch_id"),
    )


def downgrade() -> None:
    op.drop_table("usuario_sucursales")
    op.drop_table("rol_permisos")
    op.drop_table("permisos")
