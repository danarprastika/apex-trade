"""portfolio analytics metrics

Revision ID: 0006_portfolio_analytics
Revises: 0004_feature_flag_system_tables
Create Date: 2026-06-18

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0006_portfolio_analytics"
down_revision = "0004_feature_flag_system_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add portfolio_id to positions (nullable for backward compatibility)
    op.add_column("positions", sa.Column("portfolio_id", sa.String(length=36), sa.ForeignKey("portfolios.id"), nullable=True))
    op.create_index("ix_positions_portfolio_id", "positions", ["portfolio_id"])

    # Create performance_metrics table
    op.create_table(
        "performance_metrics",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("portfolio_id", sa.String(length=36), sa.ForeignKey("portfolios.id"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_type", sa.String(length=20), nullable=False),
        sa.Column("total_return", sa.Numeric(20, 8), nullable=True),
        sa.Column("sharpe_ratio", sa.Numeric(10, 6), nullable=True),
        sa.Column("sortino_ratio", sa.Numeric(10, 6), nullable=True),
        sa.Column("calmar_ratio", sa.Numeric(10, 6), nullable=True),
        sa.Column("profit_factor", sa.Numeric(20, 8), nullable=True),
        sa.Column("win_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("expectancy", sa.Numeric(20, 8), nullable=True),
        sa.Column("max_drawdown", sa.Numeric(20, 8), nullable=True),
        sa.Column("risk_adjusted_return", sa.Numeric(20, 8), nullable=True),
        sa.Column("total_trades", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("winning_trades", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("losing_trades", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("gross_profit", sa.Numeric(20, 8), nullable=True),
        sa.Column("gross_loss", sa.Numeric(20, 8), nullable=True),
        sa.Column("volatility", sa.Numeric(20, 8), nullable=True),
        sa.Column("downside_deviation", sa.Numeric(20, 8), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_performance_metrics_user_id", "performance_metrics", ["user_id"])
    op.create_index("ix_performance_metrics_portfolio_id", "performance_metrics", ["portfolio_id"])
    op.create_index("ix_performance_metrics_period", "performance_metrics", ["period_start", "period_end"])


def downgrade() -> None:
    op.drop_index("ix_performance_metrics_period", table_name="performance_metrics")
    op.drop_index("ix_performance_metrics_portfolio_id", table_name="performance_metrics")
    op.drop_index("ix_performance_metrics_user_id", table_name="performance_metrics")
    op.drop_table("performance_metrics")
    op.drop_index("ix_positions_portfolio_id", table_name="positions")
    op.drop_column("positions", "portfolio_id")