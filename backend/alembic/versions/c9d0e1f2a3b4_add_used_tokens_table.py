"""Add used_tokens table for one-time magic link enforcement

Revision ID: c9d0e1f2a3b4
Revises: b8f9a1c2d3e4
Create Date: 2026-03-17 00:00:00.000000

Adds the `used_token` table which tracks consumed one-time JWTs
(magic links, email verification tokens) to prevent replay attacks.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, Sequence[str], None] = 'b8f9a1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create used_token table."""
    op.create_table(
        'used_token',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('jti', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('token_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_used_token_jti'), 'used_token', ['jti'], unique=True)
    op.create_index(op.f('ix_used_token_token_type'), 'used_token', ['token_type'], unique=False)
    op.create_index(op.f('ix_used_token_expires_at'), 'used_token', ['expires_at'], unique=False)


def downgrade() -> None:
    """Drop used_token table."""
    op.drop_index(op.f('ix_used_token_expires_at'), table_name='used_token')
    op.drop_index(op.f('ix_used_token_token_type'), table_name='used_token')
    op.drop_index(op.f('ix_used_token_jti'), table_name='used_token')
    op.drop_table('used_token')