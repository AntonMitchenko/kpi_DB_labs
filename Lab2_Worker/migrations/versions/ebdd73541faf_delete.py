"""delete

Revision ID: ebdd73541faf
Revises: 084e56a7da5e
Create Date: 2023-10-27 20:49:00.833077

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ebdd73541faf'
down_revision = '084e56a7da5e'
branch_labels = None
depends_on = None



def upgrade():
    print("Clear old data...")

    op.drop_table('res_zno')

    print("Migrating was done!")

def downgrade():
    pass