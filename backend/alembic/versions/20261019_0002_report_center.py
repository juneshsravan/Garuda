"""Add report center fields to reports table

Revision ID: 20261019_0002
Revises: 20261006_0001
Create Date: 2026-10-19 16:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20261019_0002"
down_revision: Union[str, None] = "20261006_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new report center columns
    op.add_column("reports", sa.Column("scam_type", sa.String(length=50), nullable=False, server_default="other"))
    op.add_column("reports", sa.Column("content", sa.Text(), nullable=False, server_default=""))
    op.add_column("reports", sa.Column("scammer_phone", sa.String(length=50), nullable=True))
    op.add_column("reports", sa.Column("scammer_upi", sa.String(length=255), nullable=True))
    op.add_column("reports", sa.Column("scammer_url", sa.Text(), nullable=True))
    op.add_column("reports", sa.Column("amount_lost", sa.Numeric(precision=12, scale=2), nullable=True))

    # Make legacy columns nullable
    op.alter_column("reports", "category", existing_type=sa.String(length=100), nullable=True)
    op.alter_column("reports", "title", existing_type=sa.String(length=255), nullable=True)
    op.alter_column("reports", "description", existing_type=sa.Text(), nullable=True)

    # Indexes
    op.create_index("ix_reports_scam_type", "reports", ["scam_type"])
    op.create_index("ix_reports_scammer_phone", "reports", ["scammer_phone"])
    op.create_index("ix_reports_scammer_upi", "reports", ["scammer_upi"])


def downgrade() -> None:
    op.drop_index("ix_reports_scammer_upi", table_name="reports")
    op.drop_index("ix_reports_scammer_phone", table_name="reports")
    op.drop_index("ix_reports_scam_type", table_name="reports")

    op.alter_column("reports", "description", existing_type=sa.Text(), nullable=False)
    op.alter_column("reports", "title", existing_type=sa.String(length=255), nullable=False)
    op.alter_column("reports", "category", existing_type=sa.String(length=100), nullable=False)

    op.drop_column("reports", "amount_lost")
    op.drop_column("reports", "scammer_url")
    op.drop_column("reports", "scammer_upi")
    op.drop_column("reports", "scammer_phone")
    op.drop_column("reports", "content")
    op.drop_column("reports", "scam_type")
