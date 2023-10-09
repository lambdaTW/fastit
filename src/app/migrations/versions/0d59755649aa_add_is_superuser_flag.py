"""add is_superuser flag

Revision ID: 0d59755649aa
Revises: b130fb2851db
Create Date: 2023-10-02 19:36:07.247806

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0d59755649aa"
down_revision: Union[str, None] = "b130fb2851db"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("user", sa.Column("is_superuser", sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user", "is_superuser")
    # ### end Alembic commands ###