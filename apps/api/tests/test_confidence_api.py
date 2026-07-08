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


async def test_confidence_scans_on_demand_without_prior_scan(client):
    headers = await auth_headers(client)
    resp = await client.get("/api/v1/confidence/NVDA", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["ticker"] == "NVDA"


async def test_confidence_for_ticker_after_scan(client):
    headers = await auth_headers(client)
    await client.post("/api/v1/scanner/run", headers=headers)

    resp = await client.get("/api/v1/confidence/NVDA", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ticker"] == "NVDA"
    assert 0 <= body["total_score"] <= 10
    assert body["recommendation"] in {
        "Strong Buy Candidate", "Buy Candidate", "Watch / Hold", "Avoid",
    }
    assert len(body["dimensions"]) == 6
    assert sum(d["weight"] for d in body["dimensions"]) == 100


async def test_confidence_list_filtered_by_tickers(client):
    headers = await auth_headers(client)
    await client.post("/api/v1/scanner/run", headers=headers)

    resp = await client.get("/api/v1/confidence?tickers=NVDA,AAPL", headers=headers)
    assert resp.status_code == 200
    tickers = {r["ticker"] for r in resp.json()}
    assert tickers == {"NVDA", "AAPL"}


async def test_confidence_requires_auth(client):
    resp = await client.get("/api/v1/confidence/NVDA")
    assert resp.status_code == 401
