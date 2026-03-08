"""Add phase 2 models

Revision ID: 17d85c749788
Revises: 36d23ace56e2
Create Date: 2026-02-28 01:35:50.474856

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '17d85c749788'
down_revision: Union[str, Sequence[str], None] = '36d23ace56e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('document',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('url', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('raw_content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('cleaned_content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_user_id'), 'document', ['user_id'], unique=False)
    op.create_table('synthesis',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('summary', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_synthesis_user_id'), 'synthesis', ['user_id'], unique=False)
    op.create_table('audiosummary',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('document_id', sa.BigInteger(), nullable=True),
    sa.Column('audio_url', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('provider', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['document.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audiosummary_document_id'), 'audiosummary', ['document_id'], unique=False)
    op.create_index(op.f('ix_audiosummary_user_id'), 'audiosummary', ['user_id'], unique=False)
    op.create_table('chatsession',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('document_id', sa.BigInteger(), nullable=True),
    sa.Column('context', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['document.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chatsession_document_id'), 'chatsession', ['document_id'], unique=False)
    op.create_index(op.f('ix_chatsession_user_id'), 'chatsession', ['user_id'], unique=False)
    op.create_table('flashcardset',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('document_id', sa.BigInteger(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['document.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_flashcardset_document_id'), 'flashcardset', ['document_id'], unique=False)
    op.create_index(op.f('ix_flashcardset_user_id'), 'flashcardset', ['user_id'], unique=False)
    op.create_table('chatmessage',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('session_id', sa.BigInteger(), nullable=False),
    sa.Column('role', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['chatsession.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chatmessage_role'), 'chatmessage', ['role'], unique=False)
    op.create_index(op.f('ix_chatmessage_session_id'), 'chatmessage', ['session_id'], unique=False)
    op.create_table('flashcard',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('set_id', sa.BigInteger(), nullable=False),
    sa.Column('front', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('back', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['set_id'], ['flashcardset.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_flashcard_set_id'), 'flashcard', ['set_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_flashcard_set_id'), table_name='flashcard')
    op.drop_table('flashcard')
    op.drop_index(op.f('ix_chatmessage_session_id'), table_name='chatmessage')
    op.drop_index(op.f('ix_chatmessage_role'), table_name='chatmessage')
    op.drop_table('chatmessage')
    op.drop_index(op.f('ix_flashcardset_user_id'), table_name='flashcardset')
    op.drop_index(op.f('ix_flashcardset_document_id'), table_name='flashcardset')
    op.drop_table('flashcardset')
    op.drop_index(op.f('ix_chatsession_user_id'), table_name='chatsession')
    op.drop_index(op.f('ix_chatsession_document_id'), table_name='chatsession')
    op.drop_table('chatsession')
    op.drop_index(op.f('ix_audiosummary_user_id'), table_name='audiosummary')
    op.drop_index(op.f('ix_audiosummary_document_id'), table_name='audiosummary')
    op.drop_table('audiosummary')
    op.drop_index(op.f('ix_synthesis_user_id'), table_name='synthesis')
    op.drop_table('synthesis')
    op.drop_index(op.f('ix_document_user_id'), table_name='document')
    op.drop_table('document')
