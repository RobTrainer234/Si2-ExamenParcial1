"""Add CU26 credit-note redemption and split-tender settlement ledger."""
from alembic import op
import sqlalchemy as sa

revision = "cu26ret002a"
down_revision = "cu26ret001a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("devoluciones", sa.Column("saldo_nota_credito", sa.Numeric(12, 2), nullable=True))
    op.create_unique_constraint("uq_devoluciones_tenant_credit_note_code", "devoluciones", ["tenant_id", "codigo_nota_credito"])
    op.create_table(
        "credit_note_redemptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("credit_note_id", sa.Integer(), sa.ForeignKey("devoluciones.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sale_id", sa.Integer(), sa.ForeignKey("ventas.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cashier_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("pagos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("applied_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("post_redemption_balance", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_credit_note_redemptions_tenant_key"),
        sa.UniqueConstraint("payment_id", name="uq_credit_note_redemptions_payment_id"),
        sa.CheckConstraint("applied_amount > 0", name="ck_credit_note_redemptions_amount_positive"),
    )
    op.create_index("ix_credit_note_redemptions_tenant_id", "credit_note_redemptions", ["tenant_id"])
    op.create_index("ix_credit_note_redemptions_credit_note_id", "credit_note_redemptions", ["credit_note_id"])
    op.create_index("ix_credit_note_redemptions_sale_id", "credit_note_redemptions", ["sale_id"])
    op.create_index("ix_credit_note_redemptions_cashier_id", "credit_note_redemptions", ["cashier_id"])


def downgrade() -> None:
    op.drop_table("credit_note_redemptions")
    op.drop_constraint("uq_devoluciones_tenant_credit_note_code", "devoluciones", type_="unique")
    op.drop_column("devoluciones", "saldo_nota_credito")
