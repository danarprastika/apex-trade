from datetime import UTC, datetime

from sqlalchemy import select

from app.database.models.exchange import ExchangeAccount
from app.database.models.trading import Order, Position
from app.tasks.celery_app import celery_app


@celery_app.task(name="tasks.workers.reconcile_positions")
def reconcile_positions(user_id: str | None = None):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings
    from app.database.models.exchange import ExchangeAccount
    from app.integrations.exchanges.registry import ExchangeAdapterRegistry

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()

    try:
        query = select(Position).where(Position.status == "OPEN")
        if user_id:
            query = query.where(Position.exchange_account_id.in_(
                select(ExchangeAccount.id).where(ExchangeAccount.user_id == user_id)
            ))

        open_positions = list(db.scalars(query).all())
        reconciled_count = 0
        discrepancy_count = 0

        for position in open_positions:
            account = db.get(ExchangeAccount, position.exchange_account_id)
            if not account:
                continue

            exchange = account.exchange
            if not exchange:
                continue

            adapter = ExchangeAdapterRegistry.get_adapter(exchange.exchange_type)
            if not adapter:
                continue

            class MockContext:
                user_id: str = account.user_id
                exchange_id: str = exchange.id

            from app.services.trading_safety.position_reconciliation import (
                PositionReconciliationService,
            )
            service = PositionReconciliationService(db)
            try:
                result = service.reconcile_position(position.id, adapter, MockContext())
                reconciled_count += 1
                if result.get("discrepancies_found"):
                    discrepancy_count += 1
            except Exception:
                pass

        return {
            "reconciled_count": reconciled_count,
            "discrepancy_count": discrepancy_count,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    finally:
        db.close()


@celery_app.task(name="tasks.workers.reconcile_orders")
def reconcile_orders(order_ids: list[str] | None = None):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings
    from app.integrations.exchanges.registry import ExchangeAdapterRegistry

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()

    try:
        query = select(Order).where(Order.status.in_(["FILLED", "PARTIALLY_FILLED"]))
        if order_ids:
            query = query.where(Order.id.in_(order_ids))

        orders = list(db.scalars(query).all())
        reconciled_count = 0
        discrepancy_count = 0

        for order in orders:
            account = db.get(ExchangeAccount, order.exchange_account_id)
            if not account:
                continue

            exchange = account.exchange
            if not exchange:
                continue

            adapter = ExchangeAdapterRegistry.get_adapter(exchange.exchange_type)
            if not adapter:
                continue

            class MockContext:
                user_id: str = account.user_id
                exchange_id: str = exchange.id

            from app.services.trading_safety.order_reconciliation import OrderReconciliationService
            service = OrderReconciliationService(db)
            try:
                result = service.reconcile_order(order.id, adapter, MockContext())
                reconciled_count += 1
                if result.get("discrepancies_found"):
                    discrepancy_count += 1
            except Exception:
                pass

        return {
            "reconciled_count": reconciled_count,
            "discrepancy_count": discrepancy_count,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    finally:
        db.close()
