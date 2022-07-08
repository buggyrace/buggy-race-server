"""Add announcements

Revision ID: 63514d7c68ab
Revises: 88c69da5950c
Create Date: 2022-07-06 10:41:45.291815

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '63514d7c68ab'
down_revision = '88c69da5950c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('announcements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('type', sa.String(length=32), nullable=True),
    sa.Column('is_visible', sa.Boolean(), nullable=True),
    sa.Column('is_html', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('announcements')
    # ### end Alembic commands ###