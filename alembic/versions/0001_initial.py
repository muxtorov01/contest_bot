"""initial migration - barcha asosiy jadvallar

Revision ID: 0001
Revises:
Create Date: 2026-08-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    contest_status = sa.Enum("scheduled", "active", "ended", "stopped", name="contest_status")
    referral_status = sa.Enum("pending", "verified", "cancelled", name="referral_status")
    admin_role = sa.Enum("admin", "superadmin", name="admin_role")

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_captcha_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("captcha_fail_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("captcha_blocked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "contests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", contest_status, nullable=False, server_default="scheduled"),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "required_channels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contest_id", sa.Integer(), sa.ForeignKey("contests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("invite_link", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contest_id", sa.Integer(), sa.ForeignKey("contests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referrer_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invited_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", referral_status, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("invited_id", name="uq_referral_invited_once"),
    )

    op.create_table(
        "admins",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("role", admin_role, nullable=False, server_default="admin"),
        sa.Column("added_by", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "captcha_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("ix_referrals_contest_id", "referrals", ["contest_id"])
    op.create_index("ix_referrals_referrer_id", "referrals", ["referrer_id"])
    op.create_index("ix_required_channels_contest_id", "required_channels", ["contest_id"])


def downgrade() -> None:
    op.drop_table("captcha_attempts")
    op.drop_table("referrals")
    op.drop_table("required_channels")
    op.drop_table("admins")
    op.drop_table("contests")
    op.drop_table("users")
    sa.Enum(name="contest_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="referral_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="admin_role").drop(op.get_bind(), checkfirst=True)
