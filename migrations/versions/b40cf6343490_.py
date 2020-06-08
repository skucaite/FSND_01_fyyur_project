"""empty message

Revision ID: b40cf6343490
Revises: e7a89cd26f08
Create Date: 2020-05-21 14:59:32.528639

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b40cf6343490'
down_revision = 'e7a89cd26f08'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('venue', sa.Column('seeking_description', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('venue', 'seeking_description')
    # ### end Alembic commands ###