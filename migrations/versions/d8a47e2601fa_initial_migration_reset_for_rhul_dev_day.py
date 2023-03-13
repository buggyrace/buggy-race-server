"""initial migration, reset for RHUL dev-day

Revision ID: d8a47e2601fa
Revises: 
Create Date: 2023-03-08 00:55:05.558567

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8a47e2601fa'
down_revision = None
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
    op.create_table('races',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=80), nullable=False),
    sa.Column('desc', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('start_at', sa.DateTime(), nullable=False),
    sa.Column('cost_limit', sa.Integer(), nullable=True),
    sa.Column('is_visible', sa.Boolean(), nullable=True),
    sa.Column('result_log_url', sa.String(length=120), nullable=True),
    sa.Column('league', sa.String(length=32), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('result_log_url')
    )
    op.create_table('settings',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('value', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=True),
    sa.Column('phase', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=16), nullable=False),
    sa.Column('title', sa.String(length=80), nullable=False),
    sa.Column('problem_text', sa.Text(), nullable=False),
    sa.Column('solution_text', sa.Text(), nullable=False),
    sa.Column('hints_text', sa.Text(), nullable=False),
    sa.Column('is_enabled', sa.Boolean(), nullable=False),
    sa.Column('sort_position', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('ext_username', sa.String(length=80), nullable=True),
    sa.Column('email', sa.String(length=80), nullable=True),
    sa.Column('password', sa.LargeBinary(length=128), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('first_name', sa.String(length=30), nullable=True),
    sa.Column('last_name', sa.String(length=30), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.Column('latest_json', sa.Text(), nullable=True),
    sa.Column('github_username', sa.Text(), nullable=True),
    sa.Column('github_access_token', sa.Text(), nullable=True),
    sa.Column('is_student', sa.Boolean(), nullable=True),
    sa.Column('logged_in_at', sa.DateTime(), nullable=True),
    sa.Column('uploaded_at', sa.DateTime(), nullable=True),
    sa.Column('api_secret', sa.String(length=30), nullable=True),
    sa.Column('api_secret_at', sa.DateTime(), nullable=True),
    sa.Column('api_key', sa.String(length=30), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('ext_username'),
    sa.UniqueConstraint('username')
    )
    op.create_table('buggies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('buggy_id', sa.Integer(), nullable=True),
    sa.Column('qty_wheels', sa.Integer(), nullable=True),
    sa.Column('flag_color', sa.String(length=32), nullable=True),
    sa.Column('flag_color_secondary', sa.String(length=32), nullable=True),
    sa.Column('flag_pattern', sa.String(length=8), nullable=True),
    sa.Column('power_type', sa.String(length=16), nullable=True),
    sa.Column('power_units', sa.Integer(), nullable=True),
    sa.Column('aux_power_type', sa.String(length=16), nullable=True),
    sa.Column('aux_power_units', sa.Integer(), nullable=True),
    sa.Column('tyres', sa.String(length=16), nullable=True),
    sa.Column('qty_tyres', sa.Integer(), nullable=True),
    sa.Column('armour', sa.String(length=16), nullable=True),
    sa.Column('attack', sa.String(length=16), nullable=True),
    sa.Column('qty_attacks', sa.Integer(), nullable=True),
    sa.Column('hamster_booster', sa.Integer(), nullable=True),
    sa.Column('fireproof', sa.Boolean(), nullable=True),
    sa.Column('insulated', sa.Boolean(), nullable=True),
    sa.Column('antibiotic', sa.Boolean(), nullable=True),
    sa.Column('banging', sa.Boolean(), nullable=True),
    sa.Column('algo', sa.String(length=16), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('total_cost', sa.Integer(), nullable=True),
    sa.Column('mass', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('notes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('roles')
    op.drop_table('notes')
    op.drop_table('buggies')
    op.drop_table('users')
    op.drop_table('tasks')
    op.drop_table('settings')
    op.drop_table('races')
    op.drop_table('announcements')
    # ### end Alembic commands ###