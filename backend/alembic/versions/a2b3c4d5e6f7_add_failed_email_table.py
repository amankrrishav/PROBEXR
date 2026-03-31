"""Add failed_email dead-letter table.

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-04-01 01:15:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "failedemail",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("to_email", sa.String(length=320), nullable=False, index=True),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("error", sa.Text(), server_default=""),
        sa.Column("template", sa.String(length=100), server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("retried_at", sa.DateTime(), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("failedemail")
