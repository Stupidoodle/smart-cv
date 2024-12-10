"""Add assistant, tool, conversation, message, run models

Revision ID: a7465a62557f
Revises: 845f14fba147
Create Date: 2024-12-09 18:28:35.706875

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7465a62557f'
down_revision: Union[str, None] = '845f14fba147'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('profiles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('feedback_preference', sa.String(length=100), nullable=False),
    sa.Column('confidence_level', sa.String(length=100), nullable=False),
    sa.Column('criticism_reaction', sa.String(length=100), nullable=False),
    sa.Column('rejection_reaction', sa.String(length=100), nullable=False),
    sa.Column('motivation', sa.String(length=100), nullable=False),
    sa.Column('primary_goal', sa.String(length=100), nullable=False),
    sa.Column('analysis_goal', sa.String(length=100), nullable=False),
    sa.Column('feedback_type', sa.String(length=100), nullable=False),
    sa.Column('improvement_type', sa.String(length=100), nullable=False),
    sa.Column('explanation_type', sa.String(length=100), nullable=False),
    sa.Column('challenge_approach', sa.String(length=100), nullable=False),
    sa.Column('priority_focus', sa.String(length=100), nullable=False),
    sa.Column('improvement_confidence', sa.String(length=100), nullable=False),
    sa.Column('role_reason', sa.String(length=100), nullable=False),
    sa.Column('role_type', sa.ARRAY(sa.String(length=100)), nullable=False),
    sa.Column('application_status', sa.String(length=100), nullable=False),
    sa.Column('top_challenges', sa.ARRAY(sa.String(length=100)), nullable=False),
    sa.Column('cv_confidence', sa.String(length=100), nullable=False),
    sa.Column('cv_prep', sa.String(length=100), nullable=False),
    sa.Column('cv_struggles', sa.ARRAY(sa.String(length=100)), nullable=False),
    sa.Column('tracking_method', sa.String(length=100), nullable=False),
    sa.Column('search_improvements', sa.ARRAY(sa.String(length=100)), nullable=False),
    sa.Column('github_url', sa.String(length=255), nullable=True),
    sa.Column('linkedin_url', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_profiles_id'), 'profiles', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_profiles_id'), table_name='profiles')
    op.drop_table('profiles')
    # ### end Alembic commands ###