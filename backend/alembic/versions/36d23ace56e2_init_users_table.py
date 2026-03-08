"""Init users table

Revision ID: 36d23ace56e2
Revises: 
Create Date: 2026-02-28 01:33:30.906214

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '36d23ace56e2'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('user',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('last_login_at', sa.DateTime(), nullable=True),
    sa.Column('signup_source', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('plan', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='free'),
    sa.Column('usage_today', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
    sa.Column('usage_reset_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_plan'), 'user', ['plan'], unique=False)
    op.create_index(op.f('ix_user_signup_source'), 'user', ['signup_source'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_user_signup_source'), table_name='user')
    op.drop_index(op.f('ix_user_plan'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
