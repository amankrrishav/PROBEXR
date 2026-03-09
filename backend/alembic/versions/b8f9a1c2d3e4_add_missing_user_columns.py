"""Add missing user columns (full_name, avatar_url, is_verified, google_id, github_id)

Revision ID: b8f9a1c2d3e4
Revises: a1b2c3d4e5f6
Create Date: 2026-03-10 01:05:00.000000

The User model gained these columns after the initial migration but they were
never added to the production PostgreSQL database:
  - full_name, avatar_url, is_verified (profile/auth)
  - google_id, github_id (social login)
  - hashed_password changed from NOT NULL to nullable (social-only users)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b8f9a1c2d3e4'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing columns to user table."""
    # Profile columns
    op.add_column('user', sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('user', sa.Column('avatar_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True))

    # Auth column
    op.add_column('user', sa.Column('is_verified', sa.Boolean(), nullable=True, server_default=sa.text('false')))

    # Social login columns
    op.add_column('user', sa.Column('google_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('user', sa.Column('github_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True))

    # Create unique indexes for social IDs
    op.create_index(op.f('ix_user_google_id'), 'user', ['google_id'], unique=True)
    op.create_index(op.f('ix_user_github_id'), 'user', ['github_id'], unique=True)

    # Make hashed_password nullable (for social-only users who have no password)
    op.alter_column('user', 'hashed_password', existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    """Remove added columns."""
    op.alter_column('user', 'hashed_password', existing_type=sa.String(), nullable=False)
    op.drop_index(op.f('ix_user_github_id'), table_name='user')
    op.drop_index(op.f('ix_user_google_id'), table_name='user')
    op.drop_column('user', 'github_id')
    op.drop_column('user', 'google_id')
    op.drop_column('user', 'is_verified')
    op.drop_column('user', 'avatar_url')
    op.drop_column('user', 'full_name')
