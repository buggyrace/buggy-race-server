"""add results upload timestamp to races

Revision ID: 318931324601
Revises: 0d10dae169f6
Create Date: 2023-03-16 19:16:04.469436

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '318931324601'
down_revision = '0d10dae169f6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('races', sa.Column('results_uploaded_at', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('races', 'results_uploaded_at')
    # ### end Alembic commands ###
