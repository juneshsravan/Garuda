"""Add is_email_verified to users and mark existing users as verified

Revision ID: 20261019_0002
Revises: 20261006_0001
Create Date: 2026-10-19 18:30:00.000000

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
    # 1. Add is_email_verified column with server_default=false
    op.add_column(
        "users",
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    # 2. Mark EXISTING users as verified per requirement
    op.execute("UPDATE users SET is_email_verified = true;")


def downgrade() -> None:
    op.drop_column("users", "is_email_verified")
