"""empty message

Revision ID: 5093617c75e7
Revises: 06f432ba3e02
Create Date: 2020-10-17 17:57:43.034643

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5093617c75e7'
down_revision = '06f432ba3e02'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Venue', sa.Column('geners', sa.String(length=500), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Venue', 'geners')
    # ### end Alembic commands ###
