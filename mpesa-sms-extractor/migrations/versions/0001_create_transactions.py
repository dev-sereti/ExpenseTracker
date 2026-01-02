from alembic import op
import sqlalchemy as sa


revision = "0001_create_transactions"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transaction_code", sa.String(length=32), nullable=False),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("transaction_mode", sa.String(length=16), nullable=False),
        sa.Column("sender_name", sa.String(length=128), nullable=True),
        sa.Column("receiver_name", sa.String(length=128), nullable=True),
        sa.Column("raw_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_transactions_transaction_code", "transactions", ["transaction_code"], unique=True)
    op.create_index("ix_transactions_date", "transactions", ["transaction_date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_transactions_date", table_name="transactions")
    op.drop_index("ix_transactions_transaction_code", table_name="transactions")
    op.drop_table("transactions")