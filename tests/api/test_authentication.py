def test_root_rejects_requests_without_api_key(client):
    response = client.get("/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_root_rejects_requests_with_wrong_api_key(client):
    response = client.get("/", headers={"Authorization": "Bearer wrong-key"})

    assert response.status_code == 401


def test_root_accepts_requests_with_valid_api_key(client, auth_headers):
    response = client.get("/", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"service": "router-p", "status": "booted"}
