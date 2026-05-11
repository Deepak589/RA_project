from __future__ import annotations

from uuid import UUID

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.security import create_access_token
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.meal import Meal


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token('test-user-id')}"}


@pytest_asyncio.fixture
async def valid_meal_id() -> UUID:
    async with AsyncSessionLocal() as db:
        meal_id = await db.scalar(select(Meal.id).limit(1))
    assert meal_id is not None
    return meal_id


@pytest.mark.asyncio
async def test_get_meals_returns_200(auth_headers: dict[str, str]) -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/meals", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["total"] >= 100


@pytest.mark.asyncio
async def test_get_meals_filters_breakfast(auth_headers: dict[str, str]) -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/meals?meal_type=breakfast", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 20
    assert {item["meal_type"] for item in body["items"]} == {"breakfast"}


@pytest.mark.asyncio
async def test_get_meals_filters_flare_friendly(auth_headers: dict[str, str]) -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/meals?is_flare_friendly=true", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 15
    assert all(item["is_flare_friendly"] for item in body["items"])


@pytest.mark.asyncio
async def test_get_valid_meal_returns_200(auth_headers: dict[str, str], valid_meal_id: UUID) -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/api/v1/meals/{valid_meal_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == str(valid_meal_id)


@pytest.mark.asyncio
async def test_get_invalid_meal_returns_404(auth_headers: dict[str, str]) -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/meals/00000000-0000-0000-0000-000000000000", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_flare_safe_returns_200(auth_headers: dict[str, str]) -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/meals/flare-safe", headers=auth_headers)

    assert response.status_code == 200
    assert all(item["is_flare_friendly"] for item in response.json())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/meals",
        "/api/v1/meals?meal_type=breakfast",
        "/api/v1/meals/flare-safe",
        "/api/v1/meals/by-tag/vegetarian",
        "/api/v1/meals/00000000-0000-0000-0000-000000000000",
    ],
)
async def test_all_meal_endpoints_return_401_without_auth(path: str) -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(path)

    assert response.status_code == 401
