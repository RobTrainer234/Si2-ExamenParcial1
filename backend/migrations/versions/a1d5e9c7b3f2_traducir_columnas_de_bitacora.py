"""Traducir las columnas de la bitacora al español."""
from alembic import op


revision = "a1d5e9c7b3f2"
down_revision = "9c4e2a7b1d6f"
branch_labels = None
depends_on = None


COLUMNAS = (
    ("user_id", "usuario_id"),
    ("action", "accion"),
    ("entity_type", "tipo_entidad"),
    ("entity_id", "entidad_id"),
    ("description", "descripcion"),
    ("old_values", "valores_anteriores"),
    ("new_values", "valores_nuevos"),
    ("ip_address", "direccion_ip"),
    ("user_agent", "agente_usuario"),
    ("created_at", "fecha_creacion"),
)


def upgrade() -> None:
    for anterior, nuevo in COLUMNAS:
        op.alter_column("bitacora", anterior, new_column_name=nuevo)


def downgrade() -> None:
    for anterior, nuevo in reversed(COLUMNAS):
        op.alter_column("bitacora", nuevo, new_column_name=anterior)
