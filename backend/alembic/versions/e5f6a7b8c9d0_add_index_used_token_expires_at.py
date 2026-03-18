"""Add index on used_token.expires_at for token GC performance

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-18 00:00:00.000000

The token GC job runs hourly with:
    DELETE FROM used_token WHERE expires_at < now

Without an index on expires_at this is a full table scan on every run.
This migration adds a BTREE index on expires_at so the GC query is fast
even at high used_token volume (magic links, email verification tokens).

Mirrors the same fix applied to refreshtoken.expires_at in d4e5f6a7b8c9.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        op.f('ix_used_token_expires_at'),
        'used_token',
        ['expires_at'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_used_token_expires_at'),
        table_name='used_token',
    )