from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, UserMedication, UserPreferences
from app.schemas.user import UserMedicationCreateRequest, UserPreferencesUpdate


async def get_full_profile(db: AsyncSession, user_id: UUID) -> tuple[User, UserPreferences, list[UserMedication]]:
    user = await db.scalar(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.preferences), selectinload(User.medications))
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    preferences = user.preferences
    if preferences is None:
        preferences = UserPreferences(user_id=user_id)
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)
    return user, preferences, list(user.medications)


async def update_preferences(db: AsyncSession, user_id: UUID, data: UserPreferencesUpdate) -> UserPreferences:
    _, preferences, _ = await get_full_profile(db, user_id)
    if data.dietary_flags is not None:
        preferences.dietary_flags_jsonb = data.dietary_flags
    if data.allergies is not None:
        preferences.allergies_jsonb = data.allergies
    if data.goals is not None:
        preferences.goal_flags_jsonb = data.goals
    if data.cuisine_preferences is not None:
        preferences.disliked_foods_jsonb = data.cuisine_preferences
    if data.budget_friendly is not None:
        goals = set(preferences.goal_flags_jsonb or [])
        if data.budget_friendly:
            goals.add("budget_friendly")
        else:
            goals.discard("budget_friendly")
        preferences.goal_flags_jsonb = sorted(goals)
    await db.commit()
    await db.refresh(preferences)
    return preferences


async def add_medication(db: AsyncSession, user_id: UUID, data: UserMedicationCreateRequest) -> UserMedication:
    parts = [part for part in (data.dosage, data.frequency) if part]
    medication = UserMedication(user_id=user_id, medication_name=data.medication_name, schedule_note=", ".join(parts) or None)
    db.add(medication)
    await db.commit()
    await db.refresh(medication)
    return medication


async def remove_medication(db: AsyncSession, user_id: UUID, medication_id: UUID) -> None:
    medication = await db.get(UserMedication, medication_id)
    if medication is None or medication.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    await db.delete(medication)
    await db.commit()
