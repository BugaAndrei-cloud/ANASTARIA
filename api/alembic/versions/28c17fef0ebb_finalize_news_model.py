"""finalize news model

Revision ID: 28c17fef0ebb
Revises: 039326bec39f
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "28c17fef0ebb"
down_revision: Union[str, Sequence[str], None] = "039326bec39f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns as nullable first.
    op.add_column(
        "news",
        sa.Column("content", sa.Text(), nullable=True),
    )

    op.add_column(
        "news",
        sa.Column("category", sa.String(length=50), nullable=True),
    )

    op.add_column(
        "news",
        sa.Column("image_url", sa.String(length=1000), nullable=True),
    )

    op.add_column(
        "news",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Fill existing rows.
    op.execute(
        "UPDATE news SET category = 'UPDATE' WHERE category IS NULL"
    )

    op.execute(
        "UPDATE news SET updated_at = created_at WHERE updated_at IS NULL"
    )

    # Now make required fields NOT NULL.
    op.alter_column(
        "news",
        "category",
        existing_type=sa.String(length=50),
        nullable=False,
    )

    op.alter_column(
        "news",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )

    # Old fields are no longer used by ANASTARIA.
    op.drop_column("news", "source")
    op.drop_column("news", "url")


def downgrade() -> None:
    op.add_column(
        "news",
        sa.Column("url", sa.String(length=1000), nullable=True),
    )

    op.add_column(
        "news",
        sa.Column("source", sa.String(length=255), nullable=True),
    )

    op.drop_column("news", "updated_at")
    op.drop_column("news", "image_url")
    op.drop_column("news", "category")
    op.drop_column("news", "content")
