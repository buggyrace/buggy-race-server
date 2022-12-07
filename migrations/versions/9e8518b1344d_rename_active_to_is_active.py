"""rename active to is_active

Revision ID: 9e8518b1344d
Revises: cca386ae4d08
Create Date: 2022-12-05 13:15:24.631247

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '9e8518b1344d'
down_revision = 'cca386ae4d08'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True))
    op.drop_column('users', 'active')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('active', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.drop_column('users', 'is_active')
    # ### end Alembic commands ###