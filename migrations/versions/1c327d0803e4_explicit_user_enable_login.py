"""explicit user enable-login

Revision ID: 1c327d0803e4
Revises: 00152d1270ad
Create Date: 2024-06-19 11:50:16.096183

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c327d0803e4'
down_revision = '00152d1270ad'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'is_login_enabled',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true()) # hand-rolled default
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_login_enabled')

    # ### end Alembic commands ###
