import pytest

pytestmark = pytest.mark.asyncio


async def auth_headers(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "alec@example.com", "password": "supersecret1"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "alec@example.com", "password": "supersecret1"},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_status_before_connecting(client):
    headers = await auth_headers(client)
    resp = await client.get("/api/v1/brokerage/status", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["connected"] is False


async def test_connect_returns_a_url(client):
    headers = await auth_headers(client)
    resp = await client.post("/api/v1/brokerage/connect", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["connect_url"]


async def test_portfolio_404_before_connecting(client):
    headers = await auth_headers(client)
    resp = await client.get("/api/v1/brokerage/portfolio", headers=headers)
    assert resp.status_code == 404


async def test_full_connect_and_portfolio_flow(client):
    headers = await auth_headers(client)
    await client.post("/api/v1/brokerage/connect", headers=headers)

    portfolio_resp = await client.get("/api/v1/brokerage/portfolio", headers=headers)
    assert portfolio_resp.status_code == 200
    body = portfolio_resp.json()
    assert body["total_value"] > 0
    assert len(body["holdings"]) >= 2
    assert body["connected_accounts"]

    status_resp = await client.get("/api/v1/brokerage/status", headers=headers)
    assert status_resp.json()["connected"] is True


async def test_disconnect_then_portfolio_404s_again(client):
    headers = await auth_headers(client)
    await client.post("/api/v1/brokerage/connect", headers=headers)
    await client.get("/api/v1/brokerage/portfolio", headers=headers)

    disconnect_resp = await client.delete("/api/v1/brokerage/connection", headers=headers)
    assert disconnect_resp.status_code == 204

    portfolio_resp = await client.get("/api/v1/brokerage/portfolio", headers=headers)
    assert portfolio_resp.status_code == 404


async def test_brokerage_endpoints_require_auth(client):
    assert (await client.get("/api/v1/brokerage/status")).status_code == 401
    assert (await client.post("/api/v1/brokerage/connect")).status_code == 401
    assert (await client.get("/api/v1/brokerage/portfolio")).status_code == 401


async def test_connect_with_missing_encryption_key_returns_clean_503(client, monkeypatch):
    """
    Regression test: a missing BROKERAGE_TOKEN_ENCRYPTION_KEY used to
    produce an unhandled 500 (plain-text 'Internal Server Error', not
    JSON) -- reproduced for real against a running server before this fix,
    not just theorized. This is exactly the scenario a fresh `git pull`
    without an updated local .env hits, since .env is gitignored and never
    picks up new variables added to .env.example. Must now come back as a
    clean, actionable 503 instead.
    """
    from app.core import crypto
    from app.core.config import settings

    headers = await auth_headers(client)

    monkeypatch.setattr(settings, "BROKERAGE_TOKEN_ENCRYPTION_KEY", None)
    crypto._fernet.cache_clear()
    try:
        resp = await client.post("/api/v1/brokerage/connect", headers=headers)
        assert resp.status_code == 503
        assert "BROKERAGE_TOKEN_ENCRYPTION_KEY" in resp.json()["detail"]
    finally:
        crypto._fernet.cache_clear()


async def test_two_users_have_independent_connections(client):
    headers_a = await auth_headers(client)

    await client.post(
        "/api/v1/auth/register",
        json={"email": "otheruser@example.com", "password": "supersecret1"},
    )
    login_b = await client.post(
        "/api/v1/auth/login",
        json={"email": "otheruser@example.com", "password": "supersecret1"},
    )
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    await client.post("/api/v1/brokerage/connect", headers=headers_a)
    # User B never connected -- should still 404, not see user A's data.
    resp = await client.get("/api/v1/brokerage/portfolio", headers=headers_b)
    assert resp.status_code == 404
