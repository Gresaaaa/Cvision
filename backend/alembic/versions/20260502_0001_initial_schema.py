"""Initial schema for CVision.

Revision ID: 20260502_0001
Revises:
Create Date: 2026-05-02
"""

from alembic import op

from app.db.base import Base
from app.models import *  # noqa: F401,F403

revision = "20260502_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
