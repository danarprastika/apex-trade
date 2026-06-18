

def test_health_endpoint(e2e_client):
    response = e2e_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_auth_flow_register(e2e_client, e2e_db_session):
    import app.api.deps as deps
    import app.database.session as session_module
    deps.SessionLocal = e2e_db_session
    session_module.SessionLocal = e2e_db_session

    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "securepassword123"
    }

    response = e2e_client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"


def test_auth_flow_login(e2e_client, e2e_db_session):
    import app.api.deps as deps
    import app.database.session as session_module
    deps.SessionLocal = e2e_db_session
    session_module.SessionLocal = e2e_db_session

    user_data = {
        "username": "loginuser",
        "email": "loginuser@example.com",
        "password": "loginpassword123"
    }

    e2e_client.post("/api/v1/auth/register", json=user_data)

    login_response = e2e_client.post(
        "/api/v1/auth/login",
        json={"username": "loginuser", "password": "loginpassword123"}
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


def test_users_me_endpoint(e2e_client, e2e_db_session):
    import app.api.deps as deps
    import app.database.session as session_module
    deps.SessionLocal = e2e_db_session
    session_module.SessionLocal = e2e_db_session

    user_data = {
        "username": "meuser",
        "email": "meuser@example.com",
        "password": "mepassword123"
    }

    e2e_client.post("/api/v1/auth/register", json=user_data)
    login_response = e2e_client.post(
        "/api/v1/auth/login",
        json={"username": "meuser", "password": "mepassword123"}
    )
    access_token = login_response.json()["access_token"]

    response = e2e_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "meuser"


def test_exchanges_list(e2e_client, e2e_db_session):
    import app.api.deps as deps
    import app.database.session as session_module
    deps.SessionLocal = e2e_db_session
    session_module.SessionLocal = e2e_db_session

    response = e2e_client.get("/api/v1/exchanges/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_portfolio_flow(e2e_client, e2e_db_session):
    import app.api.deps as deps
    import app.database.session as session_module
    deps.SessionLocal = e2e_db_session
    session_module.SessionLocal = e2e_db_session

    user_data = {
        "username": "portfolio_user",
        "email": "portfolio_user@example.com",
        "password": "portfoliopassword123"
    }
    e2e_client.post("/api/v1/auth/register", json=user_data)
    login_response = e2e_client.post(
        "/api/v1/auth/login",
        json={"username": "portfolio_user", "password": "portfoliopassword123"}
    )
    access_token = login_response.json()["access_token"]

    response = e2e_client.get(
        "/api/v1/portfolio/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200


def test_paper_trading_flow(e2e_client, e2e_db_session):
    import app.api.deps as deps
    import app.database.session as session_module
    deps.SessionLocal = e2e_db_session
    session_module.SessionLocal = e2e_db_session

    user_data = {
        "username": "papertrader",
        "email": "papertrader@example.com",
        "password": "papertraderpassword123"
    }
    e2e_client.post("/api/v1/auth/register", json=user_data)
    login_response = e2e_client.post(
        "/api/v1/auth/login",
        json={"username": "papertrader", "password": "papertraderpassword123"}
    )
    access_token = login_response.json()["access_token"]

    paper_order_data = {
        "market_pair_id": "BTCUSDT",
        "strategy_id": "scalping",
        "side": "BUY",
        "quantity": 0.001,
        "price": 50000.0
    }

    response = e2e_client.post(
        "/api/v1/trading/paper-orders",
        json=paper_order_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201


def test_risk_evaluation_flow(e2e_client, e2e_db_session):
    import app.api.deps as deps
    import app.database.session as session_module
    deps.SessionLocal = e2e_db_session
    session_module.SessionLocal = e2e_db_session

    user_data = {
        "username": "riskuser",
        "email": "riskuser@example.com",
        "password": "riskpassword123"
    }
    e2e_client.post("/api/v1/auth/register", json=user_data)
    login_response = e2e_client.post(
        "/api/v1/auth/login",
        json={"username": "riskuser", "password": "riskpassword123"}
    )
    access_token = login_response.json()["access_token"]

    response = e2e_client.post(
        "/api/v1/risk/validate?risk_score=50&requested_position_size=100",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "allowed" in data
    assert "veto_reasons" in data
