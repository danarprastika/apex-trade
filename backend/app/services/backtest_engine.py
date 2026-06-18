from __future__ import annotations

import json
import logging
import math
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.database.models.backtest import BacktestSession, BacktestTrade
from app.database.models.market import Candle, MarketPair
from app.domain.models.backtest_models import (
    CommissionCalculator,
    CommissionConfig,
    PositionSizingCalculator,
    SlippageCalculator,
    SlippageConfig,
)
from app.domain.models.order_simulator import Order, OrderSide, OrderSimulator, OrderType
from app.domain.strategies.base import StrategyPlugin
from app.events.bus import EventBus
from app.events.types import ApexEvent
from app.integrations.redis.client import RedisClient
from app.schemas.risk import RiskDecision
from app.services.backtest_service import BacktestService
from app.services.risk_service import RiskService

if TYPE_CHECKING:
    from app.services.plugin_registry import PluginRegistry

logger = logging.getLogger(__name__)


class BacktestPosition:
    def __init__(
        self,
        symbol: str,
        strategy_id: str,
        entry_price: float,
        entry_time: datetime,
        quantity: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        side: str = "BUY",
    ):
        self.symbol = symbol
        self.strategy_id = strategy_id
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.quantity = quantity
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.side = side
        self.exit_time: datetime | None = None
        self.exit_price: float | None = None
        self.cumulative_pnl = 0.0
        self.status = "OPEN"

    def check_exit(self, current_price: float, current_time: datetime) -> bool:
        if self.status != "OPEN":
            return False

        if self.side == "BUY":
            if self.stop_loss and current_price <= self.stop_loss:
                self.exit_price = self.stop_loss
                self.exit_time = current_time
                self.status = "CLOSED"
                return True
            if self.take_profit and current_price >= self.take_profit:
                self.exit_price = self.take_profit
                self.exit_time = current_time
                self.status = "CLOSED"
                return True
        elif self.side == "SELL":
            if self.stop_loss and current_price >= self.stop_loss:
                self.exit_price = self.stop_loss
                self.exit_time = current_time
                self.status = "CLOSED"
                return True
            if self.take_profit and current_price <= self.take_profit:
                self.exit_price = self.take_profit
                self.exit_time = current_time
                self.status = "CLOSED"
                return True
        return False


class HistoricalDataLoader:
    def __init__(self, db: Session, redis_client: RedisClient | None = None, cache_ttl: int = 3600):
        self.db = db
        self.redis_client = redis_client
        self.cache_ttl = cache_ttl

    def load_candles(
        self, market_pair_id: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> list[Candle]:
        cache_key = f"candles:{market_pair_id}:{timeframe}:{start_date.isoformat()}:{end_date.isoformat()}"

        if self.redis_client:
            try:
                cached = self.redis_client.client.get(cache_key)
                if cached:
                    candle_data = json.loads(cached)
                    return [Candle(**c) for c in candle_data]
            except Exception as exc:
                logger.warning("Redis cache read failed: %s", exc)

        candles = (
            self.db.query(Candle)
            .where(Candle.market_pair_id == market_pair_id)
            .where(Candle.timeframe == timeframe)
            .where(Candle.open_time >= start_date)
            .where(Candle.close_time <= end_date)
            .order_by(Candle.open_time)
            .all()
        )

        if self.redis_client:
            try:
                candle_data = [
                    {
                        "id": c.id,
                        "market_pair_id": c.market_pair_id,
                        "timeframe": c.timeframe,
                        "open": float(c.open),
                        "high": float(c.high),
                        "low": float(c.low),
                        "close": float(c.close),
                        "volume": float(c.volume),
                        "open_time": c.open_time.isoformat(),
                        "close_time": c.close_time.isoformat() if c.close_time else None,
                    }
                    for c in candles
                ]
                self.redis_client.client.setex(cache_key, self.cache_ttl, json.dumps(candle_data))
            except Exception as exc:
                logger.warning("Redis cache write failed: %s", exc)

        return candles

    def get_cached_symbols(self, timeframe: str) -> list[str]:
        cache_key = f"symbols:timeframe:{timeframe}"
        if self.redis_client:
            try:
                cached = self.redis_client.client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass
        return []

    def invalidate_cache(self, market_pair_id: str | None = None) -> None:
        if not self.redis_client:
            return
        try:
            if market_pair_id:
                pattern = f"candles:{market_pair_id}:*"
                keys = list(self.redis_client.client.scan_iter(pattern))
                if keys:
                    self.redis_client.client.delete(*keys)
            else:
                self.redis_client.client.delete("candles:*", "symbols:*")
        except Exception as exc:
            logger.warning("Cache invalidation failed: %s", exc)


class BacktestEngine:
    def __init__(self, db: Session, user_id: str, event_bus: EventBus | None = None, redis_client: RedisClient | None = None):
        self.db = db
        self.user_id = user_id
        self.event_bus = event_bus
        self.backtest_service = BacktestService(db)
        self.risk_service = RiskService(db)
        self.data_loader = HistoricalDataLoader(db, redis_client)
        self.redis_client = redis_client
        self._cancelled = False

    async def run_backtest(
        self,
        run_id: str,
        strategy_plugin: StrategyPlugin,
        symbols: list[str],
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        config: dict[str, Any] | None = None,
    ) -> None:
        self._cancelled = False
        run = self.backtest_service.get_run(run_id)
        if run.status != "PENDING":
            raise ValidationError("Backtest run already started or completed")

        await self._emit_event("BACKTEST.STARTED", {"run_id": run_id, "user_id": self.user_id})

        run.status = "RUNNING"
        run.progress = 0.0
        self.backtest_service.update(run)

        slippage_config = SlippageConfig(
            model=config.get("slippage_model", {}).get("model", "FIXED") if config else "FIXED",
            max_slippage_pct=config.get("slippage_model", {}).get("max_slippage_pct", 0.001) if config else 0.001,
            volume_threshold=config.get("slippage_model", {}).get("volume_threshold", 1.0) if config else 1.0,
        )
        slippage_calc = SlippageCalculator(slippage_config)

        commission_config = CommissionConfig(
            model=config.get("commission_model", {}).get("model", "FLAT") if config else "FLAT",
            taker_fee=config.get("commission_model", {}).get("taker_fee", 0.001) if config else 0.001,
            maker_fee=config.get("commission_model", {}).get("maker_fee", 0.001) if config else 0.001,
        )
        commission_calc = CommissionCalculator(commission_config)

        order_simulator = OrderSimulator(slippage_calc, commission_calc)

        sizing_method = config.get("position_sizing_method", "FIXED") if config else "FIXED"
        sizing_value = config.get("position_size_value", 0.01) if config else 0.01
        size_calc = PositionSizingCalculator(method=sizing_method, value=sizing_value)
        max_positions = config.get("max_positions", 5) if config else 5

        current_capital = initial_capital
        positions: dict[str, list[BacktestPosition]] = {symbol: [] for symbol in symbols}
        symbol_volumes: dict[str, list[float]] = {symbol: [] for symbol in symbols}
        total_trades = 0
        pending_orders: list[Order] = []

        for symbol in symbols:
            market_pair = self.db.scalar(select(MarketPair).where(MarketPair.symbol == symbol))
            if not market_pair:
                logger.warning("Market pair not found for symbol=%s", symbol)
                continue

            session = BacktestSession(
                backtest_run_id=run_id,
                market_pair_id=market_pair.id,
                timeframe=timeframe,
                candle_count=0,
                status="RUNNING",
                start_time=start_date,
                end_time=end_date,
            )
            self.backtest_service.add(session)
            self.backtest_service.sessions.commit()
            self.backtest_service.sessions.refresh(session)

            candles = self.data_loader.load_candles(market_pair.id, timeframe, start_date, end_date)

            avg_volume = self._compute_avg_volume(candles)

            for idx, candle in enumerate(candles):
                if self._cancelled:
                    run.status = "CANCELLED"
                    run.progress = 0.0
                    run.completed_at = datetime.now(timezone.utc)
                    self.backtest_service.update(run)
                    return

                market_data = {
                    "symbol": symbol,
                    "timeframe": candle.timeframe,
                    "open": float(candle.open),
                    "high": float(candle.high),
                    "low": float(candle.low),
                    "close": float(candle.close),
                    "volume": float(candle.volume),
                    "open_time": candle.open_time,
                }

                symbol_volumes[symbol].append(float(candle.volume))
                current_avg_volume = sum(symbol_volumes[symbol]) / len(symbol_volumes[symbol]) if symbol_volumes[symbol] else avg_volume

                filled_orders = []
                for order in pending_orders[:]:
                    if order.symbol != symbol:
                        continue
                    fill = order_simulator.submit_order(order, candle, current_avg_volume)
                    if fill.filled_quantity > 0:
                        filled_orders.append(order)
                        open_positions_count = sum(1 for p in positions[symbol] if p.status == "OPEN")

                        if order.side == OrderSide.BUY:
                            risk_decision = self._evaluate_signal_risk(
                                self.user_id, run.strategy_id, symbol, fill.fill_price, fill.filled_quantity, current_capital
                            )
                            if not risk_decision.allowed:
                                await self._emit_event(
                                    "BACKTEST.SIGNAL_REJECTED",
                                    {"run_id": run_id, "symbol": symbol, "reason": str(risk_decision.veto_reasons)},
                                )
                                pending_orders.remove(order)
                                continue

                            if open_positions_count >= max_positions:
                                await self._emit_event(
                                    "BACKTEST.SIGNAL_REJECTED",
                                    {"run_id": run_id, "symbol": symbol, "reason": "max_positions_reached"},
                                )
                                pending_orders.remove(order)
                                continue

                            position = BacktestPosition(
                                symbol=symbol,
                                strategy_id=run.strategy_id,
                                entry_price=fill.fill_price,
                                entry_time=candle.close_time if hasattr(candle, "close_time") else candle.open_time,
                                quantity=fill.filled_quantity,
                                stop_loss=market_data.get("stop_loss"),
                                take_profit=market_data.get("take_profit"),
                                side="BUY",
                            )
                            positions[symbol].append(position)
                            commission = fill.commission
                            slippage_cost = fill.slippage * fill.filled_quantity
                            current_capital -= commission
                            await self._emit_event(
                                "BACKTEST.TRADE_OPENED",
                                {
                                    "run_id": run_id,
                                    "symbol": symbol,
                                    "entry_price": fill.fill_price,
                                    "quantity": fill.filled_quantity,
                                    "commission": commission,
                                    "slippage": slippage_cost,
                                },
                            )
                        elif order.side == OrderSide.SELL:
                            risk_decision = self._evaluate_signal_risk(
                                self.user_id, run.strategy_id, symbol, fill.fill_price, fill.filled_quantity, current_capital
                            )
                            if not risk_decision.allowed:
                                await self._emit_event(
                                    "BACKTEST.SIGNAL_REJECTED",
                                    {"run_id": run_id, "symbol": symbol, "reason": str(risk_decision.veto_reasons)},
                                )
                                pending_orders.remove(order)
                                continue

                            for pos in positions[symbol][:]:
                                if pos.status == "OPEN" and pos.side == "BUY":
                                    pos.exit_price = fill.fill_price
                                    pos.exit_time = candle.close_time if hasattr(candle, "close_time") else candle.open_time
                                    pos.status = "CLOSED"
                                    gross_profit = (pos.exit_price - pos.entry_price) * pos.quantity
                                    commission_pnl = fill.commission
                                    slippage_cost_pnl = fill.slippage * pos.quantity
                                    self._record_trade(pos, run_id, session.id, fill.fill_price, commission_pnl, slippage_cost_pnl)
                                    current_capital += gross_profit - commission_pnl
                                    total_trades += 1
                                    positions[symbol].remove(pos)
                                    await self._emit_event(
                                        "BACKTEST.TRADE_CLOSED",
                                        {"run_id": run_id, "symbol": symbol, "exit_price": fill.fill_price, "pnl": gross_profit},
                                    )
                                    pending_orders.remove(order)
                                    break
                    pending_orders.remove(order)

                signal_result = strategy_plugin.analyze(market_data)
                if signal_result:
                    await self._emit_event(
                        "BACKTEST.SIGNAL_GENERATED",
                        {"run_id": run_id, "symbol": symbol, "signal_type": signal_result.signal_type},
                    )

                    if signal_result.signal_type == "BUY":
                        risk_decision = self._evaluate_signal_risk(
                            self.user_id, run.strategy_id, symbol, signal_result.entry_price, None, current_capital
                        )
                        if not risk_decision.allowed:
                            await self._emit_event(
                                "BACKTEST.SIGNAL_REJECTED",
                                {"run_id": run_id, "symbol": symbol, "reason": str(risk_decision.veto_reasons)},
                            )
                            continue

                        open_positions_count = sum(1 for p in positions[symbol] if p.status == "OPEN")
                        if open_positions_count >= max_positions:
                            await self._emit_event(
                                "BACKTEST.SIGNAL_REJECTED",
                                {"run_id": run_id, "symbol": symbol, "reason": "max_positions_reached"},
                            )
                            continue

                        quantity = size_calc.calculate_quantity(current_capital, candle.close, signal_result.stop_loss)
                        if quantity > 0:
                            order = Order(
                                symbol=symbol,
                                order_type=OrderType.MARKET,
                                side=OrderSide.BUY,
                                quantity=quantity,
                                timestamp=candle.close_time if hasattr(candle, "close_time") else candle.open_time,
                                order_id=f"order_{run_id}_{idx}_{symbol}",
                            )
                            pending_orders.append(order)

                            fill = order_simulator.submit_order(order, candle, current_avg_volume)
                            if fill.filled_quantity > 0:
                                position = BacktestPosition(
                                    symbol=symbol,
                                    strategy_id=run.strategy_id,
                                    entry_price=fill.fill_price,
                                    entry_time=order.timestamp,
                                    quantity=fill.filled_quantity,
                                    stop_loss=float(signal_result.stop_loss) if signal_result.stop_loss else None,
                                    take_profit=float(signal_result.take_profit) if signal_result.take_profit else None,
                                    side="BUY",
                                )
                                positions[symbol].append(position)
                                commission_cost = fill.commission
                                slippage_cost = fill.slippage * fill.filled_quantity
                                current_capital -= commission_cost
                                await self._emit_event(
                                    "BACKTEST.TRADE_OPENED",
                                    {
                                        "run_id": run_id,
                                        "symbol": symbol,
                                        "entry_price": fill.fill_price,
                                        "quantity": fill.filled_quantity,
                                        "commission": commission_cost,
                                        "slippage": slippage_cost,
                                    },
                                )

                    elif signal_result.signal_type == "SELL":
                        risk_decision = self._evaluate_signal_risk(
                            self.user_id, run.strategy_id, symbol, signal_result.entry_price, None, current_capital
                        )
                        if not risk_decision.allowed:
                            await self._emit_event(
                                "BACKTEST.SIGNAL_REJECTED",
                                {"run_id": run_id, "symbol": symbol, "reason": str(risk_decision.veto_reasons)},
                            )
                            continue

                        for pos in positions[symbol][:]:
                            if pos.status == "OPEN" and pos.side == "BUY":
                                order = Order(
                                    symbol=symbol,
                                    order_type=OrderType.MARKET,
                                    side=OrderSide.SELL,
                                    quantity=pos.quantity,
                                    timestamp=candle.close_time if hasattr(candle, "close_time") else candle.open_time,
                                    order_id=f"order_{run_id}_{idx}_{symbol}_close",
                                )
                                pending_orders.append(order)
                                fill = order_simulator.submit_order(order, candle, current_avg_volume)
                                if fill.filled_quantity > 0:
                                    pos.exit_price = fill.fill_price
                                    pos.exit_time = order.timestamp
                                    pos.status = "CLOSED"
                                    gross_profit = (pos.exit_price - pos.entry_price) * pos.quantity
                                    commission_cost = fill.commission
                                    slippage_cost = fill.slippage * pos.quantity
                                    self._record_trade(pos, run_id, session.id, fill.fill_price, commission_cost, slippage_cost)
                                    current_capital += gross_profit - commission_cost
                                    total_trades += 1
                                    positions[symbol].remove(pos)
                                    await self._emit_event(
                                        "BACKTEST.TRADE_CLOSED",
                                        {"run_id": run_id, "symbol": symbol, "exit_price": fill.fill_price, "pnl": gross_profit},
                                    )
                                break

                for pos in positions[symbol][:]:
                    if pos.status == "OPEN" and pos.check_exit(float(candle.close), candle.close_time):
                        exit_order = Order(
                            symbol=symbol,
                            order_type=OrderType.MARKET,
                            side=OrderSide.SELL if pos.side == "BUY" else OrderSide.BUY,
                            quantity=pos.quantity,
                            timestamp=candle.close_time if hasattr(candle, "close_time") else candle.open_time,
                            order_id=f"exit_{run_id}_{pos.entry_time.timestamp()}",
                        )
                        pending_orders.append(exit_order)
                        fill = order_simulator.submit_order(exit_order, candle, current_avg_volume)
                        if fill.filled_quantity > 0:
                            pos.exit_price = fill.fill_price
                            pos.exit_time = exit_order.timestamp
                            pos.status = "CLOSED"
                            commission_cost = fill.commission
                            slippage_cost_pnl = fill.slippage * pos.quantity
                            self._record_trade(pos, run_id, session.id, fill.fill_price, commission_cost, slippage_cost_pnl)
                            if pos.side == "BUY":
                                gross_profit = (pos.exit_price - pos.entry_price) * pos.quantity
                                current_capital += gross_profit - commission_cost
                            total_trades += 1
                            positions[symbol].remove(pos)
                            await self._emit_event(
                                "BACKTEST.TRADE_CLOSED",
                                {"run_id": run_id, "symbol": symbol, "exit_price": fill.fill_price, "pnl": (pos.exit_price - pos.entry_price) * pos.quantity},
                            )

                progress = (idx + 1) / len(candles) if candles else 0
                self.backtest_service.update_run_status(run_id, "RUNNING", progress)
                self._update_capital_tracking(run_id, current_capital)

            session.status = "COMPLETED"
            session.candle_count = len(candles)
            self.db.add(session)
            self.db.commit()

        run.status = "COMPLETED"
        run.progress = 100.0
        run.final_capital = current_capital
        run.total_trades = total_trades
        run.completed_at = datetime.now(timezone.utc)
        self.db.add(run)
        self.db.commit()

        self._calculate_metrics(run_id)
        await self._emit_event("BACKTEST.COMPLETED", {"run_id": run_id, "total_trades": total_trades})

    def cancel(self) -> None:
        self._cancelled = True

    def _compute_avg_volume(self, candles: list[Candle]) -> float:
        if not candles:
            return 0.0
        volumes = [float(c.volume) for c in candles if c.volume]
        return sum(volumes) / len(volumes) if volumes else 0.0

    def _update_capital_tracking(self, run_id: str, current_capital: float) -> None:
        pass

    def _evaluate_signal_risk(self, user_id: str, strategy_id: str, symbol: str, price: float, quantity: float | None, capital: float) -> RiskDecision:
        try:
            if quantity is not None:
                risk_decision = self.risk_service.evaluate(user_id=user_id, risk_score=50.0, requested_position_size=quantity * price)
            else:
                risk_decision = self.risk_service.evaluate(user_id=user_id, risk_score=50.0, requested_position_size=capital * 0.02)
            return risk_decision
        except Exception as exc:
            logger.warning("Risk evaluation failed: %s", exc)
            return RiskDecision(
                allowed=True,
                reason="risk_evaluation_skipped",
                risk_score=50.0,
                position_size=quantity,
                max_risk_per_trade=1.0,
                max_daily_loss=3.0,
                max_drawdown=15.0,
                max_open_positions=5,
                open_positions=0,
                daily_loss=0.0,
                drawdown=0.0,
                veto_reasons=[],
            )

    def _record_trade(
        self,
        position: BacktestPosition,
        run_id: str,
        session_id: str,
        exit_price: float,
        additional_commission: float = 0.0,
        additional_slippage: float = 0.0,
    ) -> None:
        if not position.exit_price:
            position.exit_price = exit_price

        gross_profit = (position.exit_price - position.entry_price) * position.quantity
        commission = additional_commission
        slippage_cost = additional_slippage

        trade_data = {
            "backtest_run_id": run_id,
            "backtest_session_id": session_id,
            "strategy_id": position.strategy_id,
            "symbol": position.symbol,
            "entry_price": position.entry_price,
            "exit_price": position.exit_price,
            "quantity": position.quantity,
            "entry_time": position.entry_time,
            "exit_time": position.exit_time,
            "gross_profit": gross_profit,
            "commission_cost": commission,
            "slippage_cost": slippage_cost,
            "net_profit": gross_profit - commission - slippage_cost,
            "status": "CLOSED",
        }
        self.backtest_service.add_trade(trade_data)

    def _calculate_metrics(self, run_id: str) -> None:
        trades = self.backtest_service.trades.list_closed_by_run(run_id)
        run = self.backtest_service.get_run(run_id)

        if not trades:
            self.backtest_service.add_metric(run_id, "total_return", 0.0, {"description": "Total portfolio return"})
            self.backtest_service.add_metric(run_id, "annualized_return", 0.0, {"description": "Annualized return"})
            return

        initial_capital = float(run.initial_capital)
        final_capital = float(run.final_capital) if run.final_capital else initial_capital

        total_return = (final_capital - initial_capital) / initial_capital if initial_capital > 0 else 0.0

        days = (run.end_date - run.start_date).days
        annualized_return = ((1 + total_return) ** (365 / days) - 1) if days > 0 else 0.0

        winning = [t for t in trades if float(t.net_profit) > 0]
        losing = [t for t in trades if float(t.net_profit) <= 0]
        total_profit = sum(float(t.net_profit) for t in winning)
        total_loss = abs(sum(float(t.net_profit) for t in losing))
        profit_factor = total_profit / total_loss if total_loss > 0 else (float("inf") if total_profit > 0 else 0.0)
        win_rate = len(winning) / len(trades) if trades else 0.0

        total_commission = sum(float(t.commission_cost) for t in trades)
        total_slippage = sum(float(t.slippage_cost) for t in trades)

        durations = []
        for t in trades:
            if t.entry_time and t.exit_time:
                duration = (t.exit_time - t.entry_time).total_seconds() / 60
                durations.append(duration)
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        returns = [float(t.net_profit) / initial_capital for t in trades if initial_capital > 0]
        sharpe = self._sharpe_ratio(returns)
        sortino = self._sortino_ratio(returns)

        equity_curve = self._build_equity_curve(trades, initial_capital)
        max_dd = self._max_drawdown(equity_curve)

        largest_win = max((float(t.net_profit) for t in trades), default=0.0)
        largest_loss = min((float(t.net_profit) for t in trades), default=0.0)

        recovery_factor = abs(total_return / max_dd) if max_dd > 0 else 0.0
        ulcer_index = self._ulcer_index(equity_curve)

        trades_per_day = len(trades) / days if days > 0 else 0.0

        self.backtest_service.add_metric(run_id, "total_return", total_return, {"days": days})
        self.backtest_service.add_metric(run_id, "annualized_return", annualized_return, {"days": days})
        self.backtest_service.add_metric(run_id, "max_drawdown", max_dd)
        self.backtest_service.add_metric(run_id, "sharpe_ratio", sharpe)
        self.backtest_service.add_metric(run_id, "sortino_ratio", sortino)
        self.backtest_service.add_metric(run_id, "profit_factor", profit_factor if profit_factor != float("inf") else 0.0, {"is_inf": profit_factor == float("inf")})
        self.backtest_service.add_metric(run_id, "win_rate", win_rate)
        self.backtest_service.add_metric(run_id, "largest_win", largest_win)
        self.backtest_service.add_metric(run_id, "largest_loss", largest_loss)
        self.backtest_service.add_metric(run_id, "avg_trade_duration", avg_duration, {"unit": "minutes"})
        self.backtest_service.add_metric(run_id, "total_commission", total_commission)
        self.backtest_service.add_metric(run_id, "total_slippage", total_slippage)
        self.backtest_service.add_metric(run_id, "recovery_factor", recovery_factor)
        self.backtest_service.add_metric(run_id, "ulcer_index", ulcer_index)
        self.backtest_service.add_metric(run_id, "trades_per_day", trades_per_day)

    async def _emit_event(self, event_type: str, payload: dict[str, Any]) -> None:
        if self.event_bus:
            event = ApexEvent(type=event_type, payload=payload, correlation_id=payload.get("run_id"))
            await self.event_bus.publish(event)

    @staticmethod
    def _sharpe_ratio(returns: list[float]) -> float:
        if len(returns) < 2:
            return 0.0
        mean = sum(returns) / len(returns)
        std = math.sqrt(sum((r - mean) ** 2 for r in returns) / len(returns))
        return mean / std if std > 0 else 0.0

    @staticmethod
    def _sortino_ratio(returns: list[float]) -> float:
        if not returns:
            return 0.0
        mean = sum(returns) / len(returns)
        downside = [r for r in returns if r < 0]
        if not downside:
            return mean * 100 if mean > 0 else 0.0
        downside_std = math.sqrt(sum((r - mean) ** 2 for r in downside) / len(returns))
        return mean / downside_std if downside_std > 0 else 0.0

    @staticmethod
    def _build_equity_curve(trades: list[BacktestTrade], initial_capital: float) -> list[tuple[datetime, float]]:
        curve = [(datetime.min.replace(tzinfo=timezone.utc), initial_capital)]
        capital = initial_capital
        sorted_trades = sorted(trades, key=lambda t: t.entry_time or datetime.min.replace(tzinfo=timezone.utc))
        for t in sorted_trades:
            capital += float(t.net_profit)
            if t.entry_time:
                curve.append((t.entry_time, capital))
        return curve

    @staticmethod
    def _max_drawdown(equity_curve: list[tuple[datetime, float]]) -> float:
        if not equity_curve:
            return 0.0
        peak = equity_curve[0][1]
        max_dd = 0.0
        for _, value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0.0
            max_dd = max(max_dd, dd)
        return max_dd

    @staticmethod
    def _ulcer_index(equity_curve: list[tuple[datetime, float]]) -> float:
        if not equity_curve or len(equity_curve) < 2:
            return 0.0
        peak = equity_curve[0][1]
        squared_drawdowns = []
        for _, value in equity_curve:
            if value > peak:
                peak = value
            drawdown = ((peak - value) / peak * 100) ** 2 if peak > 0 else 0.0
            squared_drawdowns.append(drawdown)
        return math.sqrt(sum(squared_drawdowns) / len(squared_drawdowns))
