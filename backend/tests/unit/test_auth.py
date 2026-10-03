from fastapi.testclient import TestClient


def test_register_creates_user_and_returns_token(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "alice@example.com",
            "full_name": "Alice Example",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "alice@example.com"
    assert body["user"]["full_name"] == "Alice Example"
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_returns_token_for_existing_user(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={
            "email": "bob@example.com",
            "full_name": "Bob Example",
            "password": "StrongPassword123!",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "bob@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "bob@example.com"
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_rejects_invalid_password(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={
            "email": "carol@example.com",
            "full_name": "Carol Example",
            "password": "StrongPassword123!",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "carol@example.com",
            "password": "WrongPassword!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_me_route_requires_valid_bearer_token(client: TestClient) -> None:
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401

    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "dave@example.com",
            "full_name": "Dave Example",
            "password": "StrongPassword123!",
        },
    )
    token = register_response.json()["access_token"]

    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "dave@example.com"
