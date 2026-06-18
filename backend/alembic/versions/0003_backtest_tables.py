"""backtest tables

Revision ID: 0003_backtest_tables
Revises: 0002_exchange_account_sync_metadata
Create Date: 2026-06-16

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003_backtest_tables"
down_revision = "0002_exchange_account_sync_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "backtest_configs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("strategy_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("position_sizing_method", sa.String(length=20), nullable=False, server_default="FIXED"),
        sa.Column("position_size_value", sa.Numeric(), nullable=False),
        sa.Column("max_positions", sa.Integer(), nullable=False, server_default=sa.text("5")),
        sa.Column("slippage_model", sa.JSON(), nullable=False),
        sa.Column("commission_model", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_backtest_configs_strategy_id"), "backtest_configs", ["strategy_id"])

    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("strategy_id", sa.String(length=36), nullable=False),
        sa.Column("config_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("progress", sa.Numeric(), nullable=False, server_default=sa.text("0")),
        sa.Column("initial_capital", sa.Numeric(), nullable=False),
        sa.Column("final_capital", sa.Numeric(), nullable=True),
        sa.Column("total_trades", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["config_id"], ["backtest_configs.id"]),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_backtest_runs_strategy_id"), "backtest_runs", ["strategy_id"])
    op.create_index(op.f("ix_backtest_runs_user_id"), "backtest_runs", ["user_id"])
    op.create_index(op.f("ix_backtest_runs_status"), "backtest_runs", ["status"])

    op.create_table(
        "backtest_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("backtest_run_id", sa.String(length=36), nullable=False),
        sa.Column("market_pair_id", sa.String(length=36), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("candle_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["backtest_run_id"], ["backtest_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["market_pair_id"], ["market_pairs.id"]),
    )
    op.create_index(op.f("ix_backtest_sessions_backtest_run_id"), "backtest_sessions", ["backtest_run_id"])

    op.create_table(
        "backtest_trades",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("backtest_run_id", sa.String(length=36), nullable=False),
        sa.Column("backtest_session_id", sa.String(length=36), nullable=False),
        sa.Column("signal_id", sa.String(length=36), nullable=True),
        sa.Column("strategy_id", sa.String(length=36), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("entry_price", sa.Numeric(), nullable=False),
        sa.Column("exit_price", sa.Numeric(), nullable=True),
        sa.Column("quantity", sa.Numeric(), nullable=False),
        sa.Column("entry_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exit_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("gross_profit", sa.Numeric(), nullable=False, server_default=sa.text("0")),
        sa.Column("commission_cost", sa.Numeric(), nullable=False, server_default=sa.text("0")),
        sa.Column("slippage_cost", sa.Numeric(), nullable=False, server_default=sa.text("0")),
        sa.Column("net_profit", sa.Numeric(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["backtest_run_id"], ["backtest_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["backtest_session_id"], ["backtest_sessions.id"]),
        sa.ForeignKeyConstraint(["signal_id"], ["signals.id"]),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"]),
    )
    op.create_index(op.f("ix_backtest_trades_backtest_run_id"), "backtest_trades", ["backtest_run_id"])
    op.create_index(op.f("ix_backtest_trades_status"), "backtest_trades", ["status"])
    op.create_index(op.f("ix_backtest_trades_entry_time"), "backtest_trades", ["entry_time"])

    op.create_table(
        "backtest_metrics",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("backtest_run_id", sa.String(length=36), nullable=False),
        sa.Column("metric_name", sa.String(length=50), nullable=False),
        sa.Column("metric_value", sa.Numeric(), nullable=False),
        sa.Column("metric_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["backtest_run_id"], ["backtest_runs.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_backtest_metrics_backtest_run_id"), "backtest_metrics", ["backtest_run_id"])
    op.create_index(op.f("ix_backtest_metrics_metric_name"), "backtest_metrics", ["metric_name"])

    op.add_column("signals", sa.Column("backtest_run_id", sa.String(length=36), nullable=True))
    op.create_index(op.f("ix_signals_backtest_run_id"), "signals", ["backtest_run_id"])
    op.create_foreign_key("signals_backtest_run_id_fkey", "signals", "backtest_runs", ["backtest_run_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("signals_backtest_run_id_fkey", "signals", type_="foreignkey")
    op.drop_index(op.f("ix_signals_backtest_run_id"), table_name="signals")
    op.drop_column("signals", "backtest_run_id")
    op.drop_table("backtest_metrics")
    op.drop_table("backtest_trades")
    op.drop_table("backtest_sessions")
    op.drop_table("backtest_runs")
    op.drop_table("backtest_configs")