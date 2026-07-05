import pytest

pytestmark = pytest.mark.asyncio


async def register(client, email="alec@example.com", password="supersecret1"):
    return await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Alec Woolley"},
    )


async def test_register_creates_user(client):
    resp = await register(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alec@example.com"
    assert "hashed_password" not in body


async def test_register_duplicate_email_rejected(client):
    await register(client)
    resp = await register(client)
    assert resp.status_code == 400


async def test_login_success_returns_tokens(client):
    await register(client)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "alec@example.com", "password": "supersecret1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_wrong_password_rejected(client):
    await register(client)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "alec@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


async def test_me_requires_valid_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    await register(client)
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "alec@example.com", "password": "supersecret1"},
    )
    token = login_resp.json()["access_token"]

    me_resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "alec@example.com"


async def test_refresh_issues_new_access_token(client):
    await register(client)
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "alec@example.com", "password": "supersecret1"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()
