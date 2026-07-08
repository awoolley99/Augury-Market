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


async def test_scanner_run_requires_auth(client):
    resp = await client.post("/api/v1/scanner/run")
    assert resp.status_code == 401


async def test_scanner_run_and_list_evidence(client):
    headers = await auth_headers(client)

    run_resp = await client.post("/api/v1/scanner/run", headers=headers)
    assert run_resp.status_code == 200
    body = run_resp.json()
    assert body["processed_count"] > 0
    assert body["failed_count"] == 0

    list_resp = await client.get("/api/v1/scanner/evidence", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == body["processed_count"]


async def test_get_evidence_for_specific_ticker(client):
    headers = await auth_headers(client)
    await client.post("/api/v1/scanner/run", headers=headers)

    resp = await client.get("/api/v1/scanner/evidence/NVDA", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["ticker"] == "NVDA"


async def test_get_evidence_scans_on_demand_before_any_universe_scan(client):
    """
    A ticker's evidence is generated on first request, not gated behind an
    explicit /scanner/run -- this is what makes any watchlist ticker work
    regardless of whether it's in the pre-scanned sample universe.
    """
    headers = await auth_headers(client)
    resp = await client.get("/api/v1/scanner/evidence/NVDA", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["ticker"] == "NVDA"


async def test_evidence_list_scans_ticker_outside_sample_universe_on_demand(client):
    """
    Regression test for the reported bug: watchlist tickers outside
    UniverseLoader's curated sample (e.g. ZBRA, which isn't in it) used to
    never show up in the Market Snapshot because /scanner/evidence only
    ever returned pre-scanned tickers. Now any requested ticker gets
    scanned on demand.
    """
    headers = await auth_headers(client)
    resp = await client.get("/api/v1/scanner/evidence?tickers=ZBRA", headers=headers)
    assert resp.status_code == 200
    tickers = {p["ticker"] for p in resp.json()}
    assert tickers == {"ZBRA"}


async def test_evidence_filtered_by_watchlist_tickers(client):
    headers = await auth_headers(client)
    await client.post("/api/v1/scanner/run", headers=headers)

    resp = await client.get("/api/v1/scanner/evidence?tickers=NVDA,AAPL", headers=headers)
    assert resp.status_code == 200
    tickers = {p["ticker"] for p in resp.json()}
    assert tickers == {"NVDA", "AAPL"}
