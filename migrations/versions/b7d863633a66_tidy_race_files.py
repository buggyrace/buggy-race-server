"""tidy race files

Revision ID: b7d863633a66
Revises: 5b17feb28a87
Create Date: 2023-06-19 18:17:42.154460

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'b7d863633a66'
down_revision = '5b17feb28a87'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('races', sa.Column('race_file_url', sa.String(length=255), nullable=True))
    op.drop_index('race_log_url', table_name='races')
    op.drop_index('result_log_url', table_name='races')
    op.create_unique_constraint(None, 'races', ['race_file_url'])
    op.drop_column('races', 'result_log_url')
    op.drop_column('races', 'race_log_url')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('races', sa.Column('race_log_url', mysql.VARCHAR(length=255), nullable=True))
    op.add_column('races', sa.Column('result_log_url', mysql.VARCHAR(length=255), nullable=True))
    op.drop_constraint(None, 'races', type_='unique')
    op.create_index('result_log_url', 'races', ['result_log_url'], unique=False)
    op.create_index('race_log_url', 'races', ['race_log_url'], unique=False)
    op.drop_column('races', 'race_file_url')
    # ### end Alembic commands ###
