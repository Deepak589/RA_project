from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_current_user_id
from app.db.session import get_db_session
from app.schemas.user import (
    UserMedicationCreateRequest,
    UserMedicationResponse,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserProfileResponse,
    UserResponse,
)
from app.services.profile_service import add_medication, get_full_profile, remove_medication, update_preferences

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.get("", response_model=UserProfileResponse)
async def get_profile(
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> UserProfileResponse:
    user, preferences, medications = await get_full_profile(db, UUID(user_id))
    return UserProfileResponse(user=UserResponse.model_validate(user), preferences=preferences, medications=medications)


@router.put("/preferences", response_model=UserPreferencesResponse)
async def put_preferences(
    data: UserPreferencesUpdate,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> UserPreferencesResponse:
    return await update_preferences(db, UUID(user_id), data)


@router.post("/medications", response_model=UserMedicationResponse, status_code=201)
async def post_medication(
    data: UserMedicationCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> UserMedicationResponse:
    return await add_medication(db, UUID(user_id), data)


@router.delete("/medications/{medication_id}")
async def delete_medication(
    medication_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> dict[str, str]:
    await remove_medication(db, UUID(user_id), medication_id)
    return {"status": "removed"}
