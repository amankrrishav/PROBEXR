"""Add updated_at and deleted_at columns to document, updated_at to user.

Revision ID: f1a2b3c4d5e6
Revises: e5f6a7b8c9d0
Create Date: 2026-04-01 01:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Document: add updated_at and deleted_at
    op.add_column("document", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("document", sa.Column("deleted_at", sa.DateTime(), nullable=True))

    # User: add updated_at
    op.add_column("user", sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("user", "updated_at")
    op.drop_column("document", "deleted_at")
    op.drop_column("document", "updated_at")
