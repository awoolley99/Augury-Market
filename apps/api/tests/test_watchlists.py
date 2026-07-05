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


async def test_create_and_list_watchlist(client):
    headers = await auth_headers(client)

    create_resp = await client.post(
        "/api/v1/watchlists", json={"name": "AI Leaders"}, headers=headers
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["name"] == "AI Leaders"

    list_resp = await client.get("/api/v1/watchlists", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


async def test_duplicate_watchlist_name_rejected(client):
    headers = await auth_headers(client)
    await client.post("/api/v1/watchlists", json={"name": "AI Leaders"}, headers=headers)
    resp = await client.post("/api/v1/watchlists", json={"name": "AI Leaders"}, headers=headers)
    assert resp.status_code == 400


async def test_add_and_remove_ticker(client):
    headers = await auth_headers(client)
    watchlist = (
        await client.post("/api/v1/watchlists", json={"name": "AI Leaders"}, headers=headers)
    ).json()

    add_resp = await client.post(
        f"/api/v1/watchlists/{watchlist['id']}/items",
        json={"ticker": "nvda"},
        headers=headers,
    )
    assert add_resp.status_code == 201
    assert add_resp.json()["ticker"] == "NVDA"  # normalized uppercase

    item_id = add_resp.json()["id"]
    remove_resp = await client.delete(
        f"/api/v1/watchlists/{watchlist['id']}/items/{item_id}", headers=headers
    )
    assert remove_resp.status_code == 204


async def test_cannot_access_other_users_watchlist(client):
    headers = await auth_headers(client)
    watchlist = (
        await client.post("/api/v1/watchlists", json={"name": "AI Leaders"}, headers=headers)
    ).json()

    # Second user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "someone_else@example.com", "password": "supersecret1"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "someone_else@example.com", "password": "supersecret1"},
    )
    other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    resp = await client.delete(
        f"/api/v1/watchlists/{watchlist['id']}", headers=other_headers
    )
    assert resp.status_code == 404
