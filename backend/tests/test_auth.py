from fastapi.testclient import TestClient


def test_login_returns_bearer_token(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["role"] == "admin"
    assert body["access_token"]


def test_login_rejects_invalid_password(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "wrong"},
    )

    assert response.status_code == 401
