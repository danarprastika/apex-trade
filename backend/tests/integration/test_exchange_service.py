

def test_exchange_service_list_exchanges(integration_db_session):
    from app.services.exchange_service import ExchangeService

    service = ExchangeService(integration_db_session)
    exchanges = service.list_exchanges()
    assert isinstance(exchanges, list)


def test_exchange_service_create_and_get_exchange(integration_db_session):
    from app.services.exchange_service import ExchangeService

    service = ExchangeService(integration_db_session)

    exchange = service.create_exchange("TestExchange", "binance", "ACTIVE")
    assert exchange.name == "TestExchange"
    assert exchange.exchange_type == "binance"


def test_exchange_service_create_account(integration_db_session):
    from app.database.models.exchange import Exchange
    from app.database.models.identity import User
    from app.services.exchange_service import ExchangeService

    user = User(username="accountuser", email="account@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
    integration_db_session.add(user)
    integration_db_session.flush()

    exchange = Exchange(name="TestExchange", exchange_type="binance", status="ACTIVE")
    integration_db_session.add(exchange)
    integration_db_session.flush()

    service = ExchangeService(integration_db_session)

    account = service.create_account(
        user_id=user.id,
        exchange_id=exchange.id,
        api_key="test-api-key",
        api_secret="test-api-secret",
        is_testnet=True,
    )
    assert account is not None
    assert account.user_id == user.id
