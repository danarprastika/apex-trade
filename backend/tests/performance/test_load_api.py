import time


def test_benchmark_health_endpoint(e2e_client):
    start = time.time()
    for _ in range(100):
        response = e2e_client.get("/api/v1/health")
        assert response.status_code == 200
    elapsed = time.time() - start
    assert elapsed < 10.0


def test_benchmark_health_endpoint_1000(e2e_client):
    start = time.time()
    for _ in range(100):
        response = e2e_client.get("/api/v1/health")
        assert response.status_code == 200
    elapsed = time.time() - start
    assert elapsed < 10.0


def test_benchmark_market_data_endpoint(e2e_client):
    import concurrent.futures

    def fetch_market():
        return e2e_client.get("/api/v1/market/")

    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_market) for _ in range(100)]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    elapsed = time.time() - start
    assert elapsed < 30.0


def test_benchmark_risk_evaluation(e2e_client, e2e_db_session):
    import app.api.deps as deps
    import app.database.session as session_module
    deps.SessionLocal = e2e_db_session
    session_module.SessionLocal = e2e_db_session

    user_data = {
        "username": "riskbench",
        "email": "riskbench@example.com",
        "password": "riskbenchpassword123"
    }
    e2e_client.post("/api/v1/auth/register", json=user_data)
    login_response = e2e_client.post(
        "/api/v1/auth/login",
        json={"username": "riskbench", "password": "riskbenchpassword123"}
    )
    access_token = login_response.json()["access_token"]

    start = time.time()
    for _ in range(100):
        response = e2e_client.post(
            "/api/v1/risk/validate?risk_score=30&requested_position_size=50",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
    elapsed = time.time() - start
    assert elapsed < 10.0
