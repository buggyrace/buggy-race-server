"""race replay fields

Revision ID: 7663bd1779cb
Revises: a38ed3aabb7a
Create Date: 2023-06-04 11:03:17.482094

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7663bd1779cb'
down_revision = 'a38ed3aabb7a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('races', sa.Column('track_image_url', sa.String(length=255), nullable=True))
    op.add_column('races', sa.Column('track_svg_url', sa.String(length=255), nullable=True))
    op.add_column('races', sa.Column('max_laps', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('races', 'max_laps')
    op.drop_column('races', 'track_svg_url')
    op.drop_column('races', 'track_image_url')
    # ### end Alembic commands ###
