"""initial stage 1 schema

Revision ID: 0001_initial_stage1_schema
Revises:
Create Date: 2026-06-15 23:57:30
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_stage1_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="VIEWER"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "user_settings",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("timezone", sa.String(length=50), nullable=False, server_default="UTC"),
        sa.Column("language", sa.String(length=20), nullable=False, server_default="en"),
        sa.Column("theme", sa.String(length=20), nullable=False, server_default="dark"),
        sa.Column("telegram_chat_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_user_settings_user_id"), "user_settings", ["user_id"], unique=True)

    op.create_table(
        "exchanges",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("exchange_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "assets",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("symbol", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("asset_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(op.f("ix_assets_asset_type"), "assets", ["asset_type"])
    op.create_index(op.f("ix_assets_symbol"), "assets", ["symbol"])

    op.create_table(
        "exchange_accounts",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("exchange_id", sa.String(length=36), nullable=False),
        sa.Column("api_key_encrypted", sa.String(length=512), nullable=False),
        sa.Column("api_secret_encrypted", sa.String(length=512), nullable=False),
        sa.Column("is_testnet", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["exchange_id"], ["exchanges.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_exchange_accounts_exchange_id"), "exchange_accounts", ["exchange_id"])
    op.create_index(op.f("ix_exchange_accounts_user_id"), "exchange_accounts", ["user_id"])

    op.create_table(
        "market_pairs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("exchange_id", sa.String(length=36), nullable=False),
        sa.Column("base_asset_id", sa.String(length=36), nullable=False),
        sa.Column("quote_asset_id", sa.String(length=36), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["base_asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["exchange_id"], ["exchanges.id"]),
        sa.ForeignKeyConstraint(["quote_asset_id"], ["assets.id"]),
    )
    op.create_index(op.f("ix_market_pairs_exchange_id"), "market_pairs", ["exchange_id"])
    op.create_index(op.f("ix_market_pairs_symbol"), "market_pairs", ["symbol"])

    op.create_table(
        "candles",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("market_pair_id", sa.String(length=36), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("open", sa.Numeric(20, 8), nullable=False),
        sa.Column("high", sa.Numeric(20, 8), nullable=False),
        sa.Column("low", sa.Numeric(20, 8), nullable=False),
        sa.Column("close", sa.Numeric(20, 8), nullable=False),
        sa.Column("volume", sa.Numeric(20, 8), nullable=False),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["market_pair_id"], ["market_pairs.id"]),
    )
    op.create_index(op.f("ix_candles_market_pair_id"), "candles", ["market_pair_id"])
    op.create_index(op.f("ix_candles_open_time"), "candles", ["open_time"])
    op.create_index(op.f("ix_candles_timeframe"), "candles", ["timeframe"])
    op.create_index(op.f("ix_candles_market_pair_timeframe_open_time"), "candles", ["market_pair_id", "timeframe", "open_time"], unique=True)

    op.create_table(
        "order_book_snapshots",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("market_pair_id", sa.String(length=36), nullable=False),
        sa.Column("bid_volume", sa.Numeric(20, 8), nullable=False),
        sa.Column("ask_volume", sa.Numeric(20, 8), nullable=False),
        sa.Column("spread", sa.Numeric(20, 8), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["market_pair_id"], ["market_pairs.id"]),
    )
    op.create_index(op.f("ix_order_book_snapshots_captured_at"), "order_book_snapshots", ["captured_at"])
    op.create_index(op.f("ix_order_book_snapshots_market_pair_id"), "order_book_snapshots", ["market_pair_id"])

    op.create_table(
        "funding_rates",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("market_pair_id", sa.String(length=36), nullable=False),
        sa.Column("funding_rate", sa.Numeric(20, 8), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["market_pair_id"], ["market_pairs.id"]),
    )
    op.create_index(op.f("ix_funding_rates_captured_at"), "funding_rates", ["captured_at"])
    op.create_index(op.f("ix_funding_rates_market_pair_id"), "funding_rates", ["market_pair_id"])

    op.create_table(
        "open_interest_records",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("market_pair_id", sa.String(length=36), nullable=False),
        sa.Column("open_interest", sa.Numeric(20, 8), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["market_pair_id"], ["market_pairs.id"]),
    )
    op.create_index(op.f("ix_open_interest_records_captured_at"), "open_interest_records", ["captured_at"])
    op.create_index(op.f("ix_open_interest_records_market_pair_id"), "open_interest_records", ["market_pair_id"])

    op.create_table(
        "strategies",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("strategy_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="INACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(op.f("ix_strategies_code"), "strategies", ["code"], unique=True)
    op.create_index(op.f("ix_strategies_strategy_type"), "strategies", ["strategy_type"])
    op.create_index(op.f("ix_strategies_status"), "strategies", ["status"])

    op.create_table(
        "strategy_parameters",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("strategy_id", sa.String(length=36), nullable=False),
        sa.Column("parameter_name", sa.String(length=100), nullable=False),
        sa.Column("parameter_value", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_strategy_parameters_strategy_id"), "strategy_parameters", ["strategy_id"])

    op.create_table(
        "signals",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("strategy_id", sa.String(length=36), nullable=False),
        sa.Column("market_pair_id", sa.String(length=36), nullable=False),
        sa.Column("signal_type", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=False),
        sa.Column("entry_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("stop_loss", sa.Numeric(20, 8), nullable=True),
        sa.Column("take_profit", sa.Numeric(20, 8), nullable=True),
        sa.Column("reason", sa.String(length=2000), nullable=False),
        sa.Column("signal_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["market_pair_id"], ["market_pairs.id"]),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"]),
    )
    op.create_index(op.f("ix_signals_market_pair_id"), "signals", ["market_pair_id"])
    op.create_index(op.f("ix_signals_signal_time"), "signals", ["signal_time"])
    op.create_index(op.f("ix_signals_status"), "signals", ["status"])
    op.create_index(op.f("ix_signals_strategy_id"), "signals", ["strategy_id"])

    op.create_table(
        "orders",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("exchange_account_id", sa.String(length=36), nullable=False),
        sa.Column("signal_id", sa.String(length=36), nullable=True),
        sa.Column("exchange_order_id", sa.String(length=255), nullable=True),
        sa.Column("order_type", sa.String(length=20), nullable=False),
        sa.Column("side", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("price", sa.Numeric(20, 8), nullable=True),
        sa.Column("filled_quantity", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="NEW"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["exchange_account_id"], ["exchange_accounts.id"]),
        sa.ForeignKeyConstraint(["signal_id"], ["signals.id"]),
    )
    op.create_index(op.f("ix_orders_exchange_account_id"), "orders", ["exchange_account_id"])
    op.create_index(op.f("ix_orders_exchange_order_id"), "orders", ["exchange_order_id"])
    op.create_index(op.f("ix_orders_signal_id"), "orders", ["signal_id"])
    op.create_index(op.f("ix_orders_status"), "orders", ["status"])

    op.create_table(
        "positions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("exchange_account_id", sa.String(length=36), nullable=False),
        sa.Column("market_pair_id", sa.String(length=36), nullable=False),
        sa.Column("strategy_id", sa.String(length=36), nullable=False),
        sa.Column("entry_order_id", sa.String(length=36), nullable=True),
        sa.Column("entry_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("current_price", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("unrealized_pnl", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["exchange_account_id"], ["exchange_accounts.id"]),
        sa.ForeignKeyConstraint(["entry_order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["market_pair_id"], ["market_pairs.id"]),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"]),
    )
    op.create_index(op.f("ix_positions_exchange_account_id"), "positions", ["exchange_account_id"])
    op.create_index(op.f("ix_positions_market_pair_id"), "positions", ["market_pair_id"])
    op.create_index(op.f("ix_positions_status"), "positions", ["status"])
    op.create_index(op.f("ix_positions_strategy_id"), "positions", ["strategy_id"])

    op.create_table(
        "trades",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("position_id", sa.String(length=36), nullable=False),
        sa.Column("strategy_id", sa.String(length=36), nullable=False),
        sa.Column("entry_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("exit_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("gross_profit", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("net_profit", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("profit_percentage", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"]),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"]),
    )
    op.create_index(op.f("ix_trades_closed_at"), "trades", ["closed_at"])
    op.create_index(op.f("ix_trades_position_id"), "trades", ["position_id"])
    op.create_index(op.f("ix_trades_strategy_id"), "trades", ["strategy_id"])

    op.create_table(
        "risk_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("max_risk_per_trade", sa.Numeric(5, 2), nullable=False, server_default=sa.text("1.00")),
        sa.Column("max_daily_loss", sa.Numeric(5, 2), nullable=False, server_default=sa.text("3.00")),
        sa.Column("max_drawdown", sa.Numeric(5, 2), nullable=False, server_default=sa.text("15.00")),
        sa.Column("max_open_positions", sa.Integer(), nullable=False, server_default=sa.text("5")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_risk_profiles_user_id"), "risk_profiles", ["user_id"])

    op.create_table(
        "risk_events",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_risk_events_event_type"), "risk_events", ["event_type"])
    op.create_index(op.f("ix_risk_events_severity"), "risk_events", ["severity"])
    op.create_index(op.f("ix_risk_events_user_id"), "risk_events", ["user_id"])

    op.create_table(
        "portfolios",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("portfolio_name", sa.String(length=100), nullable=False, server_default="Default"),
        sa.Column("currency", sa.String(length=20), nullable=False, server_default="USDT"),
        sa.Column("total_value", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("cash_balance", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_portfolios_user_id"), "portfolios", ["user_id"])

    op.create_table(
        "portfolio_allocations",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("portfolio_id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("target_percentage", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("current_percentage", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_portfolio_allocations_asset_id"), "portfolio_allocations", ["asset_id"])
    op.create_index(op.f("ix_portfolio_allocations_portfolio_id"), "portfolio_allocations", ["portfolio_id"])

    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("portfolio_id", sa.String(length=36), nullable=False),
        sa.Column("total_value", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("cash_balance", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("open_positions", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("daily_pnl", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("total_pnl", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_portfolio_snapshots_captured_at"), "portfolio_snapshots", ["captured_at"])
    op.create_index(op.f("ix_portfolio_snapshots_portfolio_id"), "portfolio_snapshots", ["portfolio_id"])

    op.create_table(
        "exposure_records",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("portfolio_id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("exposure_percentage", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_exposure_records_asset_id"), "exposure_records", ["asset_id"])
    op.create_index(op.f("ix_exposure_records_captured_at"), "exposure_records", ["captured_at"])
    op.create_index(op.f("ix_exposure_records_portfolio_id"), "exposure_records", ["portfolio_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.String(length=2000), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_notifications_notification_type"), "notifications", ["notification_type"])
    op.create_index(op.f("ix_notifications_status"), "notifications", ["status"])
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("old_value", sa.JSON(), nullable=True),
        sa.Column("new_value", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"])
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"])
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"])
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"])

    op.create_table(
        "system_metrics",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("metric_value", sa.Numeric(20, 8), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_system_metrics_captured_at"), "system_metrics", ["captured_at"])
    op.create_index(op.f("ix_system_metrics_metric_name"), "system_metrics", ["metric_name"])

    op.create_table(
        "system_alerts",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("alert_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("message", sa.String(length=2000), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(op.f("ix_system_alerts_alert_type"), "system_alerts", ["alert_type"])
    op.create_index(op.f("ix_system_alerts_severity"), "system_alerts", ["severity"])
    op.create_index(op.f("ix_system_alerts_status"), "system_alerts", ["status"])


def downgrade() -> None:
    op.drop_table("system_alerts")
    op.drop_table("system_metrics")
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("exposure_records")
    op.drop_table("portfolio_snapshots")
    op.drop_table("portfolio_allocations")
    op.drop_table("portfolios")
    op.drop_table("risk_events")
    op.drop_table("risk_profiles")
    op.drop_table("trades")
    op.drop_table("positions")
    op.drop_table("orders")
    op.drop_table("signals")
    op.drop_table("strategy_parameters")
    op.drop_table("strategies")
    op.drop_table("open_interest_records")
    op.drop_table("funding_rates")
    op.drop_table("order_book_snapshots")
    op.drop_table("candles")
    op.drop_table("market_pairs")
    op.drop_table("exchange_accounts")
    op.drop_table("assets")
    op.drop_table("exchanges")
    op.drop_table("user_settings")
    op.drop_table("users")
