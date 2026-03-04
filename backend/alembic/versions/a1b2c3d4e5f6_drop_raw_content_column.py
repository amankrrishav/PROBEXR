"""Drop raw_content column from document table

Revision ID: a1b2c3d4e5f6
Revises: 97697c7751ca
Create Date: 2026-03-04 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '97697c7751ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the raw_content column — it was never read and caused DB bloat."""
    with op.batch_alter_table('document') as batch_op:
        batch_op.drop_column('raw_content')


def downgrade() -> None:
    """Re-add raw_content column."""
    with op.batch_alter_table('document') as batch_op:
        batch_op.add_column(
            sa.Column('raw_content', sa.Text(), nullable=False, server_default='')
        )
