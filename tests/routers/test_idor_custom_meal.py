from __future__ import annotations

import uuid

import httpx
import pytest

from app.core.security import create_access_token
from app.main import app


def _unique_email() -> str:
    return f"idor-{uuid.uuid4().hex[:10]}@example.com"


def _auth_headers(user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


@pytest.mark.asyncio
async def test_cross_user_custom_meal_returns_404() -> None:
    """User B cannot log a food_log using user A's custom_meal_id — must 404."""
    email_a = _unique_email()
    email_b = _unique_email()
    payload_a = {"email": email_a, "password": "password123", "name": "User A"}
    payload_b = {"email": email_b, "password": "password123", "name": "User B"}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        reg_a = await client.post("/api/v1/auth/register", json=payload_a)
        reg_b = await client.post("/api/v1/auth/register", json=payload_b)
        assert reg_a.status_code == 201
        assert reg_b.status_code == 201

        user_a_id = reg_a.json()["user"]["id"]
        user_b_id = reg_b.json()["user"]["id"]

        # User A creates a custom meal
        meal_resp = await client.post(
            "/api/v1/custom-meals",
            headers=_auth_headers(user_a_id),
            json={
                "name": "User A Secret Meal",
                "meal_type": "lunch",
                "ingredients": [],
            },
        )
        assert meal_resp.status_code in (200, 201), meal_resp.text
        custom_meal_id = meal_resp.json()["id"]

        # User B tries to log a food_log referencing user A's custom meal
        log_resp = await client.post(
            "/api/v1/logs/food",
            headers=_auth_headers(user_b_id),
            json={
                "log_source": "custom_meal",
                "custom_meal_id": custom_meal_id,
                "meal_type": "lunch",
                "portion_g": 100,
            },
        )

    assert log_resp.status_code == 404
