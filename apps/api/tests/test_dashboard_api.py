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


async def test_briefing_requires_auth(client):
    resp = await client.get("/api/v1/dashboard/briefing")
    assert resp.status_code == 401


async def test_briefing_before_scan_has_neutral_defaults(client):
    headers = await auth_headers(client)
    resp = await client.get("/api/v1/dashboard/briefing", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["market_overview"]["tickers_scanned"] == 0
    assert body["top_opportunities"] == []


async def test_briefing_after_scan_and_watchlist(client):
    headers = await auth_headers(client)
    await client.post("/api/v1/scanner/run", headers=headers)

    watchlist = (
        await client.post("/api/v1/watchlists", json={"name": "AI Leaders"}, headers=headers)
    ).json()
    await client.post(
        f"/api/v1/watchlists/{watchlist['id']}/items", json={"ticker": "NVDA"}, headers=headers
    )

    resp = await client.get("/api/v1/dashboard/briefing", headers=headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["market_overview"]["tickers_scanned"] > 0
    assert len(body["top_opportunities"]) > 0
    assert any(item["ticker"] == "NVDA" for item in body["watchlist_summary"])
    nvda_item = next(i for i in body["watchlist_summary"] if i["ticker"] == "NVDA")
    assert nvda_item["confidence_score"] is not None
