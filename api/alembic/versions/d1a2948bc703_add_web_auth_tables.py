"""add web auth tables

Revision ID: d1a2948bc703
Revises: c8f7341ea920
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision: str = "d1a2948bc703"
down_revision: Union[str, Sequence[str], None] = "c8f7341ea920"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("web_profiles",sa.Column("account_id",sa.String(36),primary_key=True),sa.Column("display_name",sa.String(40),nullable=False),sa.Column("country_code",sa.String(2)),sa.Column("avatar_url",sa.String(500)),sa.Column("bio",sa.Text()),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    op.create_table("web_sessions",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("account_id",sa.String(36),nullable=False),sa.Column("token_hash",sa.String(64),nullable=False,unique=True),sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False));op.create_index("ix_web_sessions_account_id","web_sessions",["account_id"]);op.create_index("ix_web_sessions_token_hash","web_sessions",["token_hash"])
    op.create_table("captcha_challenges",sa.Column("id",sa.String(64),primary_key=True),sa.Column("answer_hash",sa.String(64),nullable=False),sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False),sa.Column("used",sa.Boolean(),nullable=False))
    op.create_table("password_reset_tokens",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("account_id",sa.String(36),nullable=False),sa.Column("token_hash",sa.String(64),nullable=False,unique=True),sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False),sa.Column("used",sa.Boolean(),nullable=False));op.create_index("ix_password_reset_tokens_account_id","password_reset_tokens",["account_id"]);op.create_index("ix_password_reset_tokens_token_hash","password_reset_tokens",["token_hash"])

def downgrade() -> None:
    op.drop_table("password_reset_tokens");op.drop_table("captcha_challenges");op.drop_table("web_sessions");op.drop_table("web_profiles")
