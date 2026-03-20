def test_health_returns_service_readiness(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "router-p",
        "status": "ready",
        "environment": "development",
    }


def test_health_does_not_require_auth(client):
    response = client.get("/health")

    assert response.status_code == 200
