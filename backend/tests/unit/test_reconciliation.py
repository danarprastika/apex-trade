from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.services.trading_safety.order_reconciliation import OrderReconciliationService
from app.services.trading_safety.position_reconciliation import PositionReconciliationService


@pytest.mark.asyncio
async def test_order_reconciliation_no_discrepancy():
    db = MagicMock()
    order_repo = MagicMock()

    from app.database.models.trading import Order
    mock_order = MagicMock(spec=Order)
    mock_order.id = "order-123"
    mock_order.exchange_order_id = "ex-order-456"
    mock_order.status = "FILLED"
    mock_order.filled_quantity = 1.0

    order_repo.get.return_value = mock_order
    db.add = MagicMock()
    db.commit = MagicMock()

    service = OrderReconciliationService(db)
    service.orders = order_repo

    context = MagicMock()
    context.exchange_id = "exchange-123"
    context.user_id = "user-456"

    adapter = MagicMock()
    adapter.fetch_order.return_value = MagicMock(status="FILLED", filled_quantity=1.0)

    result = await service.reconcile_order("order-123", adapter, context)

    assert result["discrepancies_found"] is False


@pytest.mark.asyncio
async def test_order_reconciliation_detects_status_discrepancy():
    db = MagicMock()
    order_repo = MagicMock()

    from app.database.models.trading import Order
    mock_order = MagicMock(spec=Order)
    mock_order.id = "order-123"
    mock_order.exchange_order_id = "ex-order-456"
    mock_order.status = "NEW"
    mock_order.filled_quantity = 0.0

    order_repo.get.return_value = mock_order
    db.add = MagicMock()
    db.commit = MagicMock()

    service = OrderReconciliationService(db)
    service.orders = order_repo

    context = MagicMock()
    context.exchange_id = "exchange-123"
    context.user_id = "user-456"

    adapter = MagicMock()
    adapter.fetch_order.return_value = MagicMock(status="FILLED", filled_quantity=1.0)

    result = await service.reconcile_order("order-123", adapter, context)

    assert result["discrepancies_found"] is True


@pytest.mark.asyncio
async def test_position_reconciliation_no_discrepancy():
    db = MagicMock()
    position_repo = MagicMock()

    from app.database.models.trading import Position
    mock_position = MagicMock(spec=Position)
    mock_position.id = "position-123"
    mock_position.quantity = 1.0
    mock_position.entry_price = 50000.0
    mock_position.symbol = "BTCUSDT"

    position_repo.get.return_value = mock_position
    db.add = MagicMock()
    db.commit = MagicMock()

    service = PositionReconciliationService(db)
    service.positions = position_repo

    context = MagicMock()
    context.exchange_id = "exchange-123"
    context.user_id = "user-456"

    adapter = MagicMock()
    adapter.fetch_positions.return_value = [
        MagicMock(quantity=1.0, entry_price=50000.0, source_symbol="BTCUSDT")
    ]

    result = await service.reconcile_position("position-123", adapter, context)

    assert result["discrepancies_found"] is False


@pytest.mark.asyncio
async def test_position_reconciliation_detects_quantity_discrepancy():
    db = MagicMock()
    position_repo = MagicMock()

    from app.database.models.trading import Position
    mock_position = MagicMock(spec=Position)
    mock_position.id = "position-123"
    mock_position.quantity = 1.0
    mock_position.entry_price = 50000.0
    mock_position.symbol = "BTCUSDT"

    position_repo.get.return_value = mock_position
    db.add = MagicMock()
    db.commit = MagicMock()

    service = PositionReconciliationService(db)
    service.positions = position_repo

    context = MagicMock()
    context.exchange_id = "exchange-123"
    context.user_id = "user-456"

    adapter = MagicMock()
    adapter.fetch_positions.return_value = [
        MagicMock(quantity=0.5, entry_price=50000.0, source_symbol="BTCUSDT")
    ]

    result = await service.reconcile_position("position-123", adapter, context)

    assert result["discrepancies_found"] is True
