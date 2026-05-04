from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.food import Food, MealItem
    from app.models.log import FoodLog
    from app.models.recommendation import RecommendationLog
    from app.models.user import User


class Meal(Base):
    __tablename__ = "meals"
    __table_args__ = (
        CheckConstraint("meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'flare_day', 'any')", name="valid_meal_type"),
        CheckConstraint("(prep_time_minutes IS NULL OR prep_time_minutes >= 0)", name="prep_time_non_negative"),
        CheckConstraint("(anti_inflammatory_score >= 0 AND anti_inflammatory_score <= 10)", name="score_between_0_10"),
        Index("ix_static_meals_meal_type", "meal_type"),
        Index("ix_static_meals_is_curated", "is_curated"),
        Index("ix_static_meals_name_lower", text("LOWER(name)")),
        {"schema": "static"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    cuisine_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prep_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    effort_level: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'medium'"))
    serving_size_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_calories: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    total_protein_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    total_carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    total_fat_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    total_fiber_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    total_sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    total_sodium_mg: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    total_omega3_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    anti_inflammatory_score: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False, server_default=text("0"))
    is_vegetarian: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    is_flare_friendly: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    calories: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    fiber_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    sodium_mg: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    is_curated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    dietary_tags_jsonb: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    reason_tags_jsonb: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    ingredients: Mapped[list["MealIngredient"]] = relationship(back_populates="meal", cascade="all, delete-orphan")
    meal_items: Mapped[list["MealItem"]] = relationship(back_populates="meal", cascade="all, delete-orphan")
    food_logs: Mapped[list["FoodLog"]] = relationship(back_populates="meal", foreign_keys="FoodLog.meal_id")
    recommendation_logs: Mapped[list["RecommendationLog"]] = relationship(
        back_populates="recommended_meal",
        foreign_keys="RecommendationLog.meal_id",
    )
    replacement_recommendation_logs: Mapped[list["RecommendationLog"]] = relationship(
        back_populates="replacement_meal",
        foreign_keys="RecommendationLog.replacement_meal_id",
    )

    def __repr__(self) -> str:
        return f"Meal(id={self.id!s}, name={self.name!r}, meal_type={self.meal_type!r})"


class MealIngredient(Base):
    __tablename__ = "meal_ingredients"
    __table_args__ = (
        CheckConstraint("portion_g > 0", name="ck_static_meal_ingredients_portion_positive"),
        CheckConstraint("cooking_state IN ('raw', 'cooked', 'ready_to_eat', 'unspecified')", name="ck_static_meal_ingredients_cooking_state"),
        Index("ix_static_meal_ingredients_meal_id", "meal_id"),
        Index("ix_static_meal_ingredients_food_id", "food_id"),
        {"schema": "static"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    meal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("static.meals.id", ondelete="CASCADE"), nullable=False)
    food_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("static.foods.id", ondelete="RESTRICT"), nullable=False)
    portion_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    cooking_state: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'cooked'"))
    display_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))

    meal: Mapped["Meal"] = relationship(back_populates="ingredients")
    food: Mapped["Food"] = relationship(back_populates="meal_ingredients")

    def __repr__(self) -> str:
        return f"MealIngredient(id={self.id!s}, meal_id={self.meal_id!s}, food_id={self.food_id!s})"


class CustomMeal(Base):
    __tablename__ = "custom_meals"
    __table_args__ = (
        CheckConstraint("meal_type IS NULL OR meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'flare_day')", name="ck_tracking_custom_meals_meal_type"),
        CheckConstraint("anti_inflammatory_score IS NULL OR (anti_inflammatory_score >= 0 AND anti_inflammatory_score <= 10)", name="ck_tracking_custom_meals_score"),
        Index("ix_tracking_custom_meals_user_id", "user_id"),
        {"schema": "tracking"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    meal_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    total_calories: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    total_protein_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    total_carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    total_fat_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    total_fiber_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    total_sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    total_sodium_mg: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    total_omega3_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    anti_inflammatory_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    is_vegetarian: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    is_flare_friendly: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    user: Mapped["User"] = relationship(back_populates="custom_meals")
    ingredients: Mapped[list["CustomMealIngredient"]] = relationship(back_populates="custom_meal", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"CustomMeal(id={self.id!s}, user_id={self.user_id!s}, name={self.name!r})"


class CustomMealIngredient(Base):
    __tablename__ = "custom_meal_ingredients"
    __table_args__ = (
        CheckConstraint("portion_g IS NULL OR portion_g > 0", name="ck_tracking_custom_meal_ingredients_portion_positive"),
        Index("ix_tracking_custom_meal_ingredients_custom_meal_id", "custom_meal_id"),
        Index("ix_tracking_custom_meal_ingredients_food_id", "food_id"),
        {"schema": "tracking"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    custom_meal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tracking.custom_meals.id", ondelete="CASCADE"), nullable=False)
    food_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("static.foods.id", ondelete="RESTRICT"), nullable=False)
    portion_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    cooking_state: Mapped[str | None] = mapped_column(String(20), nullable=True)
    display_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))

    custom_meal: Mapped["CustomMeal"] = relationship(back_populates="ingredients")
    food: Mapped["Food"] = relationship(back_populates="custom_meal_ingredients")

    def __repr__(self) -> str:
        return f"CustomMealIngredient(id={self.id!s}, custom_meal_id={self.custom_meal_id!s})"
