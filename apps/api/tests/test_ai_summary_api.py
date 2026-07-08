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


async def test_summary_scans_on_demand_without_prior_scan(client):
    headers = await auth_headers(client)
    resp = await client.get("/api/v1/summary/NVDA", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["ticker"] == "NVDA"


async def test_summary_generated_after_scan(client):
    headers = await auth_headers(client)
    await client.post("/api/v1/scanner/run", headers=headers)

    resp = await client.get("/api/v1/summary/NVDA", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ticker"] == "NVDA"
    assert body["provider"] == "StubAISummaryProvider"
    assert len(body["why_it_ranked"]) > 0
    assert body["catalyst_strength"] in {"Low", "Moderate", "High"}


async def test_summary_is_cached_across_requests(client):
    headers = await auth_headers(client)
    await client.post("/api/v1/scanner/run", headers=headers)

    first = await client.get("/api/v1/summary/NVDA", headers=headers)
    second = await client.get("/api/v1/summary/NVDA", headers=headers)
    assert first.json()["created_at"] == second.json()["created_at"]


async def test_summary_requires_auth(client):
    resp = await client.get("/api/v1/summary/NVDA")
    assert resp.status_code == 401
