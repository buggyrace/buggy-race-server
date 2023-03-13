"""rename user notes to comment

Revision ID: c272132ca84c
Revises: d8a47e2601fa
Create Date: 2023-03-13 11:06:19.086213

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'c272132ca84c'
down_revision = 'd8a47e2601fa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('comment', sa.Text(), nullable=True))
    op.drop_column('users', 'notes')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('notes', mysql.TEXT(), nullable=True))
    op.drop_column('users', 'comment')
    # ### end Alembic commands ###
