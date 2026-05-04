from __future__ import annotations

import uuid

import httpx
import pytest

from app.core.security import create_access_token
from app.main import app
from app.services.log_service import ESCALATION_MESSAGE


def _unique_email() -> str:
    return f"week7-{uuid.uuid4().hex[:10]}@example.com"


def _auth_headers(user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_structured_409() -> None:
    email = _unique_email()
    payload = {"email": email, "password": "password123", "name": "Week Seven"}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        first = await client.post("/api/v1/auth/register", json=payload)
        second = await client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == {
        "code": "EMAIL_ALREADY_EXISTS",
        "message": "An account with this email already exists.",
    }


@pytest.mark.asyncio
async def test_login_sets_refresh_cookie() -> None:
    email = _unique_email()
    register_payload = {"email": email, "password": "password123", "name": "Cookie Check"}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/v1/auth/register", json=register_payload)
        response = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})

    assert response.status_code == 200
    assert response.cookies.get("ra_refresh")
    assert "ra_refresh=" in response.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_refresh_accepts_cookie_and_rotates_refresh_session() -> None:
    email = _unique_email()
    register_payload = {"email": email, "password": "password123", "name": "Refresh Cookie"}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/v1/auth/register", json=register_payload)
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
        original_refresh = login.cookies.get("ra_refresh")
        refresh = await client.post("/api/v1/auth/refresh", cookies={"ra_refresh": original_refresh})
        rotated_refresh = refresh.cookies.get("ra_refresh")
        reuse = await client.post("/api/v1/auth/refresh", cookies={"ra_refresh": original_refresh})

    assert refresh.status_code == 200
    assert refresh.json()["access_token"]
    assert rotated_refresh
    assert "ra_refresh=" in refresh.headers.get("set-cookie", "")
    assert reuse.status_code == 401


@pytest.mark.asyncio
async def test_patch_symptoms_today_creates_log_when_missing() -> None:
    email = _unique_email()
    payload = {"email": email, "password": "password123", "name": "Symptom Create"}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        register = await client.post("/api/v1/auth/register", json=payload)
        user_id = register.json()["user"]["id"]
        response = await client.patch(
            "/api/v1/logs/symptoms/today",
            headers=_auth_headers(user_id),
            json={"pain_score": 4, "flare_level": "mild", "note": "initial"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["pain_score"] == 4
    assert body["flare_level"] == "mild"
    assert body["note"] == "initial"
    assert body["escalation_triggered"] is False


@pytest.mark.asyncio
async def test_patch_symptoms_today_updates_existing_log() -> None:
    email = _unique_email()
    payload = {"email": email, "password": "password123", "name": "Symptom Update"}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        register = await client.post("/api/v1/auth/register", json=payload)
        user_id = register.json()["user"]["id"]
        created = await client.patch(
            "/api/v1/logs/symptoms/today",
            headers=_auth_headers(user_id),
            json={"pain_score": 3, "fatigue_score": 2, "flare_level": "none"},
        )
        updated = await client.patch(
            "/api/v1/logs/symptoms/today",
            headers=_auth_headers(user_id),
            json={"pain_score": 6, "note": "adjusted"},
        )

    assert created.status_code == 200
    assert updated.status_code == 200
    body = updated.json()
    assert body["id"] == created.json()["id"]
    assert body["pain_score"] == 6
    assert body["fatigue_score"] == 2
    assert body["note"] == "adjusted"


@pytest.mark.asyncio
async def test_patch_symptoms_today_sets_escalation_when_pain_is_high() -> None:
    email = _unique_email()
    payload = {"email": email, "password": "password123", "name": "Symptom Escalation"}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        register = await client.post("/api/v1/auth/register", json=payload)
        user_id = register.json()["user"]["id"]
        response = await client.patch(
            "/api/v1/logs/symptoms/today",
            headers=_auth_headers(user_id),
            json={"pain_score": 9, "flare_level": "none"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["escalation_triggered"] is True
    assert body["escalation_message"] == ESCALATION_MESSAGE
