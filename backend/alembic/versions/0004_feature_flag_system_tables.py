"""feature flag system tables

Revision ID: 0004_feature_flag_system_tables
Revises: 0003_backtest_tables
Create Date: 2026-06-16

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004_feature_flag_system_tables"
down_revision = "0003_backtest_tables"
branch_labels = None
depends_on = None


DEFAULT_FLAGS = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "key": "paper_trading.enabled",
        "name": "Paper Trading",
        "description": "Allows paper order execution and simulated portfolio updates.",
        "enabled": True,
        "environment": "all",
        "owner": "trading",
        "metadata": {"default": True},
        "is_kill_switch": False,
        "failure_mode": "fail_closed",
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "key": "live_trading.enabled",
        "name": "Live Trading",
        "description": "Safety-critical kill switch for real order submission.",
        "enabled": False,
        "environment": "all",
        "owner": "trading",
        "metadata": {"default": True, "ttl_seconds": 10},
        "is_kill_switch": True,
        "failure_mode": "fail_closed",
    },
    {
        "id": "00000000-0000-0000-0000-000000000003",
        "key": "ai_agents.enabled",
        "name": "AI Agents",
        "description": "Gates AI orchestration and AI-driven trading actions.",
        "enabled": False,
        "environment": "all",
        "owner": "ai-governance",
        "metadata": {"default": True, "ttl_seconds": 30},
        "is_kill_switch": True,
        "failure_mode": "fail_closed",
    },
    {
        "id": "00000000-0000-0000-0000-000000000004",
        "key": "news_analysis.enabled",
        "name": "News Analysis",
        "description": "Gates news collection, classification, and analysis.",
        "enabled": False,
        "environment": "all",
        "owner": "intelligence",
        "metadata": {"default": True, "ttl_seconds": 60},
        "is_kill_switch": False,
        "failure_mode": "fail_closed",
    },
    {
        "id": "00000000-0000-0000-0000-000000000005",
        "key": "sentiment_analysis.enabled",
        "name": "Sentiment Analysis",
        "description": "Gates sentiment collection and scoring.",
        "enabled": False,
        "environment": "all",
        "owner": "intelligence",
        "metadata": {"default": True, "ttl_seconds": 60},
        "is_kill_switch": False,
        "failure_mode": "fail_closed",
    },
    {
        "id": "00000000-0000-0000-0000-000000000006",
        "key": "experimental_features.enabled",
        "name": "Experimental Features",
        "description": "Global gate for unstable product and API features.",
        "enabled": False,
        "environment": "all",
        "owner": "platform",
        "metadata": {"default": True, "ttl_seconds": 60},
        "is_kill_switch": False,
        "failure_mode": "fail_closed",
    },
]


def upgrade() -> None:
    op.create_table(
        "feature_flags",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("environment", sa.String(length=20), nullable=False, server_default="development"),
        sa.Column("owner", sa.String(length=100), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("is_kill_switch", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("failure_mode", sa.String(length=20), nullable=False, server_default="fail_closed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(op.f("ix_feature_flags_key"), "feature_flags", ["key"], unique=True)
    op.create_index(op.f("ix_feature_flags_environment"), "feature_flags", ["environment"])

    op.create_table(
        "feature_flag_assignments",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("flag_id", sa.String(length=36), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", sa.String(length=100), nullable=True),
        sa.Column("target_role", sa.String(length=20), nullable=True),
        sa.Column("rollout_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("environment", sa.String(length=20), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["flag_id"], ["feature_flags.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_feature_flag_assignments_flag_id"), "feature_flag_assignments", ["flag_id"])
    op.create_index(op.f("ix_feature_flag_assignments_target_type"), "feature_flag_assignments", ["target_type"])
    op.create_index(op.f("ix_feature_flag_assignments_target_id"), "feature_flag_assignments", ["target_id"])
    op.create_index(op.f("ix_feature_flag_assignments_target_role"), "feature_flag_assignments", ["target_role"])
    op.create_index(op.f("ix_feature_flag_assignments_environment"), "feature_flag_assignments", ["environment"])

    op.create_table(
        "feature_flag_audit_logs",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("flag_id", sa.String(length=36), nullable=False),
        sa.Column("flag_key", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("old_value", sa.JSON(), nullable=True),
        sa.Column("new_value", sa.JSON(), nullable=True),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("actor_role", sa.String(length=20), nullable=True),
        sa.Column("ip_address", sa.String(length=100), nullable=True),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["flag_id"], ["feature_flags.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_feature_flag_audit_logs_flag_id"), "feature_flag_audit_logs", ["flag_id"])
    op.create_index(op.f("ix_feature_flag_audit_logs_flag_key"), "feature_flag_audit_logs", ["flag_key"])
    op.create_index(op.f("ix_feature_flag_audit_logs_action"), "feature_flag_audit_logs", ["action"])
    op.create_index(op.f("ix_feature_flag_audit_logs_actor_user_id"), "feature_flag_audit_logs", ["actor_user_id"])
    op.create_index(op.f("ix_feature_flag_audit_logs_created_at"), "feature_flag_audit_logs", ["created_at"])

    op.bulk_insert(
        sa.table(
            "feature_flags",
            sa.column("id", sa.String()),
            sa.column("key", sa.String()),
            sa.column("name", sa.String()),
            sa.column("description", sa.String()),
            sa.column("enabled", sa.Boolean()),
            sa.column("environment", sa.String()),
            sa.column("owner", sa.String()),
            sa.column("metadata", sa.JSON()),
            sa.column("is_kill_switch", sa.Boolean()),
            sa.column("failure_mode", sa.String()),
        ),
        DEFAULT_FLAGS,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_feature_flag_audit_logs_created_at"), table_name="feature_flag_audit_logs")
    op.drop_index(op.f("ix_feature_flag_audit_logs_actor_user_id"), table_name="feature_flag_audit_logs")
    op.drop_index(op.f("ix_feature_flag_audit_logs_action"), table_name="feature_flag_audit_logs")
    op.drop_index(op.f("ix_feature_flag_audit_logs_flag_key"), table_name="feature_flag_audit_logs")
    op.drop_index(op.f("ix_feature_flag_audit_logs_flag_id"), table_name="feature_flag_audit_logs")
    op.drop_table("feature_flag_audit_logs")
    op.drop_index(op.f("ix_feature_flag_assignments_environment"), table_name="feature_flag_assignments")
    op.drop_index(op.f("ix_feature_flag_assignments_target_role"), table_name="feature_flag_assignments")
    op.drop_index(op.f("ix_feature_flag_assignments_target_id"), table_name="feature_flag_assignments")
    op.drop_index(op.f("ix_feature_flag_assignments_target_type"), table_name="feature_flag_assignments")
    op.drop_index(op.f("ix_feature_flag_assignments_flag_id"), table_name="feature_flag_assignments")
    op.drop_table("feature_flag_assignments")
    op.drop_index(op.f("ix_feature_flags_environment"), table_name="feature_flags")
    op.drop_index(op.f("ix_feature_flags_key"), table_name="feature_flags")
    op.drop_table("feature_flags")
