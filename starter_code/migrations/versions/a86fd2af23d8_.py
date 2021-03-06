"""empty message

Revision ID: a86fd2af23d8
Revises: c2e3b2986cc3
Create Date: 2020-10-12 03:42:13.630843

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a86fd2af23d8'
down_revision = 'c2e3b2986cc3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('City',
    sa.Column('id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('state', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('name')
    )
    op.alter_column('Venue', 'city_name',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('Venue', 'city_name',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.drop_table('City')
    # ### end Alembic commands ###
