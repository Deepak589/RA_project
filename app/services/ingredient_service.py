from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import Food
from app.models.log import MissingIngredient
from app.models.enums import MissingIngredientStatus
from app.schemas.ingredient import IngredientSearchResult, MissingIngredientCreate, MissingIngredientResponse


SUBMITTED_VALUE_FIELDS = (
    "submitted_calories",
    "submitted_protein_g",
    "submitted_carbs_g",
    "submitted_fat_g",
    "submitted_fiber_g",
    "submitted_sugar_g",
    "submitted_sodium_mg",
)


def _has_submitted_values(data: MissingIngredientCreate) -> bool:
    return any(getattr(data, field) is not None for field in SUBMITTED_VALUE_FIELDS)


async def search_or_flag_ingredient(
    db: AsyncSession,
    user_id: UUID,
    ingredient_name: str,
    submitted_values: MissingIngredientCreate | None = None,
) -> IngredientSearchResult:
    matches = list(
        await db.scalars(
            select(Food).where(Food.name.ilike(f"%{ingredient_name.strip()}%")).order_by(Food.name).limit(5)
        )
    )
    if matches:
        return IngredientSearchResult(found=True, matches=matches, suggestion_message=None)
    data = submitted_values or MissingIngredientCreate(ingredient_name=ingredient_name)
    record = await create_missing_ingredient(db, user_id, data)
    return IngredientSearchResult(
        found=False,
        matches=[],
        missing_record=record,
        suggestion_message=(
            f"{ingredient_name} excluded from score - not in database yet. We have noted it for review."
        ),
    )


async def create_missing_ingredient(db: AsyncSession, user_id: UUID, data: MissingIngredientCreate) -> MissingIngredientResponse:
    name = data.ingredient_name.strip()
    existing = await db.scalar(
        select(MissingIngredient).where(
            func.lower(MissingIngredient.ingredient_name) == name.lower(),
            MissingIngredient.status.notin_([MissingIngredientStatus.ADDED.value, MissingIngredientStatus.REJECTED.value]),
        )
    )
    if existing is not None:
        existing.reported_count += 1
        existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
        await db.refresh(existing)
        return MissingIngredientResponse.model_validate(existing)

    status = MissingIngredientStatus.USER_ENTERED.value if _has_submitted_values(data) else MissingIngredientStatus.MISSING_COMPLETELY.value
    values = data.model_dump()
    values.pop("ingredient_name", None)
    record = MissingIngredient(user_id=user_id, ingredient_name=name, status=status, **values)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return MissingIngredientResponse.model_validate(record)


async def get_missing_ingredients(
    db: AsyncSession,
    status_filter: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[MissingIngredientResponse], int]:
    statement = select(MissingIngredient)
    if status_filter:
        statement = statement.where(MissingIngredient.status == status_filter)
    total = int(await db.scalar(select(func.count()).select_from(statement.subquery())) or 0)
    result = await db.scalars(
        statement.order_by(
            MissingIngredient.reported_count.desc(),
            case((MissingIngredient.status == MissingIngredientStatus.USER_ENTERED.value, 0), else_=1),
            MissingIngredient.created_at.asc(),
        )
        .limit(limit)
        .offset(offset)
    )
    return [MissingIngredientResponse.model_validate(item) for item in result], total


async def update_missing_ingredient(
    db: AsyncSession,
    ingredient_id: UUID,
    status: str,
    admin_notes: str | None,
    food_id: UUID | None,
    reviewed_by: str,
) -> MissingIngredientResponse | None:
    record = await db.get(MissingIngredient, ingredient_id)
    if record is None:
        return None
    record.status = status
    record.admin_notes = admin_notes
    record.food_id = food_id
    record.reviewed_by = reviewed_by
    record.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    record.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(record)
    return MissingIngredientResponse.model_validate(record)
