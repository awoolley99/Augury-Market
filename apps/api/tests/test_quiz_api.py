import pytest

from app.services.risk_quiz import QUIZ_QUESTIONS

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


async def test_get_quiz_returns_seven_questions(client):
    headers = await auth_headers(client)
    resp = await client.get("/api/v1/quiz", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 7


async def test_get_quiz_requires_auth(client):
    resp = await client.get("/api/v1/quiz")
    assert resp.status_code == 401


async def test_profile_404_before_quiz_taken(client):
    headers = await auth_headers(client)
    resp = await client.get("/api/v1/quiz/profile", headers=headers)
    assert resp.status_code == 404


async def test_submit_quiz_creates_profile(client):
    headers = await auth_headers(client)
    answers = {q.id: "A" for q in QUIZ_QUESTIONS}

    resp = await client.post("/api/v1/quiz/submit", json={"answers": answers}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["risk_level"] == "Conservative"
    assert body["risk_score"] == 7

    profile_resp = await client.get("/api/v1/quiz/profile", headers=headers)
    assert profile_resp.status_code == 200
    assert profile_resp.json()["risk_level"] == "Conservative"


async def test_resubmitting_quiz_overwrites_previous_profile(client):
    headers = await auth_headers(client)
    low_answers = {q.id: "A" for q in QUIZ_QUESTIONS}
    await client.post("/api/v1/quiz/submit", json={"answers": low_answers}, headers=headers)

    high_answers = {q.id: q.options[-1].letter for q in QUIZ_QUESTIONS}
    resp = await client.post("/api/v1/quiz/submit", json={"answers": high_answers}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["risk_level"] == "Moderately Aggressive"

    profile_resp = await client.get("/api/v1/quiz/profile", headers=headers)
    assert profile_resp.json()["risk_level"] == "Moderately Aggressive"


async def test_submit_quiz_with_invalid_answer_returns_400(client):
    headers = await auth_headers(client)
    answers = {q.id: "A" for q in QUIZ_QUESTIONS}
    answers["loss_reaction"] = "Z"

    resp = await client.post("/api/v1/quiz/submit", json={"answers": answers}, headers=headers)
    assert resp.status_code == 400


async def test_submit_quiz_missing_answers_returns_400(client):
    headers = await auth_headers(client)
    resp = await client.post(
        "/api/v1/quiz/submit", json={"answers": {"experience": "A"}}, headers=headers
    )
    assert resp.status_code == 400
