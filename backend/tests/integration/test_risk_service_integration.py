

def test_risk_service_create_profile(integration_db_session):
    from app.database.models.identity import User
    from app.services.risk_service import RiskService

    user = User(username="risktest", email="risktest@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
    integration_db_session.add(user)
    integration_db_session.flush()

    service = RiskService(integration_db_session)

    profile = service.create_profile(
        user_id=user.id,
        max_risk_per_trade=2.0,
        max_daily_loss=3.0,
        max_drawdown=10.0,
        max_open_positions=5,
    )
    assert profile is not None
    assert profile.user_id == user.id
    assert profile.max_risk_per_trade == 2.0


def test_risk_service_evaluate_low_risk(integration_db_session):
    from app.database.models.identity import User
    from app.database.models.portfolio import Portfolio
    from app.services.risk_service import RiskService

    user = User(username="risklow", email="risklow@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
    integration_db_session.add(user)
    integration_db_session.flush()

    service = RiskService(integration_db_session)
    service.create_profile(user_id=user.id, max_risk_per_trade=10.0, max_daily_loss=5.0, max_drawdown=20.0, max_open_positions=5)
    portfolio = Portfolio(user_id=user.id, total_value=10000.0, cash_balance=10000.0, risk_score=0)
    integration_db_session.add(portfolio)
    integration_db_session.commit()

    decision = service.evaluate(user.id, risk_score=10, requested_position_size=100)
    assert decision.allowed is True


def test_risk_service_evaluate_high_risk(integration_db_session):
    from app.database.models.identity import User
    from app.database.models.portfolio import Portfolio
    from app.services.risk_service import RiskService

    user = User(username="riskhigh", email="riskhigh@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
    integration_db_session.add(user)
    integration_db_session.flush()

    service = RiskService(integration_db_session)
    service.create_profile(user_id=user.id, max_risk_per_trade=2.0, max_daily_loss=3.0, max_drawdown=10.0, max_open_positions=1)
    portfolio = Portfolio(user_id=user.id, total_value=1000.0, cash_balance=1000.0, risk_score=0)
    integration_db_session.add(portfolio)
    integration_db_session.commit()

    decision = service.evaluate(user_id=user.id, risk_score=90, requested_position_size=500)
    assert decision.allowed is False
    assert len(decision.veto_reasons) > 0
