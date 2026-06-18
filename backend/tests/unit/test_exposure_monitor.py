from __future__ import annotations

from unittest.mock import MagicMock

from app.services.trading_safety.exposure_monitor import ExposureMonitor


def test_exposure_monitor_no_exposure():
    db = MagicMock()
    monitor = ExposureMonitor(db)
    monitor.exposure_limits = MagicMock()
    monitor.exposure_limits.get_all_for_user.return_value = []

    compliant, violations = monitor.check_user_exposure(
        user_id="user-123",
        symbol="BTCUSDT",
        proposed_quantity=1.0,
        proposed_price=50000.0,
    )

    assert compliant is True
    assert violations == []


def test_exposure_monitor_respects_limit():
    db = MagicMock()
    monitor = ExposureMonitor(db)

    mock_limit = MagicMock()
    mock_limit.current_exposure_percentage = 5.0
    mock_limit.max_exposure_percentage = 10.0
    mock_limit.asset_id = None
    mock_limit.exchange_id = "exchange-123"

    monitor.exposure_limits = MagicMock()
    monitor.exposure_limits.get_all_for_user.return_value = [mock_limit]

    compliant, violations = monitor.check_user_exposure(
        user_id="user-123",
        symbol="BTCUSDT",
        proposed_quantity=0.06,
        proposed_price=50000.0,
    )

    assert compliant is True


def test_exposure_monitor_blocks_over_limit():
    db = MagicMock()
    monitor = ExposureMonitor(db)

    mock_limit = MagicMock()
    mock_limit.current_exposure_percentage = 5.0
    mock_limit.max_exposure_percentage = 10.0
    mock_limit.asset_id = "btc"
    mock_limit.exchange_id = "exchange-123"

    monitor.exposure_limits = MagicMock()
    monitor.exposure_limits.get_all_for_user.return_value = [mock_limit]

    monitor._matches_asset = lambda symbol, asset_id: "btc" in symbol.lower()

    compliant, violations = monitor.check_user_exposure(
        user_id="user-123",
        symbol="BTCUSDT",
        proposed_quantity=1.0,
        proposed_price=50000.0,
    )

    assert compliant is False


def test_exposure_monitor_set_limit():
    db = MagicMock()
    monitor = ExposureMonitor(db)

    from app.database.models.trading_safety import ExposureLimit

    existing_limit = MagicMock(spec=ExposureLimit)
    existing_limit.id = "limit-123"
    existing_limit.current_exposure_percentage = 5.0

    monitor.exposure_limits = MagicMock()
    monitor.exposure_limits.get_for_user.return_value = existing_limit
    monitor.exposure_limits.db = db

    result = monitor.set_limit(
        user_id="user-123",
        scope="USER",
        max_exposure_percentage=15.0,
    )

    assert result is not None
