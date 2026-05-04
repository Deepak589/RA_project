from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, Numeric, SmallInteger, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.log import FoodLog
    from app.models.meal import CustomMealIngredient, Meal, MealIngredient
    from app.models.recommendation import RecommendationLog


class Food(Base):
    __tablename__ = "foods"
    __table_args__ = (
        CheckConstraint("char_length(trim(name)) > 0", name="food_name_not_blank"),
        CheckConstraint("(serving_size_g IS NULL OR serving_size_g >= 0)", name="serving_size_non_negative"),
        CheckConstraint("(calories IS NULL OR calories >= 0)", name="calories_non_negative"),
        CheckConstraint("(protein_g IS NULL OR protein_g >= 0)", name="protein_non_negative"),
        CheckConstraint("(carbs_g IS NULL OR carbs_g >= 0)", name="carbs_non_negative"),
        CheckConstraint("(fat_g IS NULL OR fat_g >= 0)", name="fat_non_negative"),
        CheckConstraint("saturated_fat_g >= 0", name="saturated_fat_non_negative"),
        CheckConstraint("(fiber_g IS NULL OR fiber_g >= 0)", name="fiber_non_negative"),
        CheckConstraint("(sugar_g IS NULL OR sugar_g >= 0)", name="sugar_non_negative"),
        CheckConstraint("(sodium_mg IS NULL OR sodium_mg >= 0)", name="sodium_non_negative"),
        CheckConstraint("(omega3_g IS NULL OR omega3_g >= 0)", name="omega3_non_negative"),
        CheckConstraint("calcium_mg >= 0", name="calcium_non_negative"),
        CheckConstraint("vitamin_d_ug >= 0", name="vitamin_d_non_negative"),
        CheckConstraint(
            "(anti_inflammatory_score >= 0 AND anti_inflammatory_score <= 10)",
            name="food_ai_score_between_0_10",
        ),
        Index("ux_static_foods_external_source_external_id", "external_source", "external_id", unique=True),
        Index("ix_static_foods_name_lower", text("LOWER(name)")),
        {"schema": "static"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    external_source: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'usda'"))
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    brand_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(Text, nullable=True)
    serving_size_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    calories: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    fat_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    saturated_fat_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, server_default=text("0"))
    fiber_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    sodium_mg: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    omega3_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    calcium_mg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default=text("0"))
    vitamin_d_ug: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, server_default=text("0"))
    anti_inflammatory_score: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False, server_default=text("0"))
    ingredients_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    dietary_tags_jsonb: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    metadata_jsonb: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    cooking_state: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'unspecified'"))
    conversion_factor: Mapped[Decimal] = mapped_column(Numeric(5, 3), nullable=False, server_default=text("1.0"))
    display_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_flag: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'usda_verified'"))
    manual_override: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    needs_review: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    meal_items: Mapped[list["MealItem"]] = relationship(back_populates="food")
    meal_ingredients: Mapped[list["MealIngredient"]] = relationship(back_populates="food")
    custom_meal_ingredients: Mapped[list["CustomMealIngredient"]] = relationship(back_populates="food")
    food_logs: Mapped[list["FoodLog"]] = relationship(back_populates="food")
    replacement_recommendations: Mapped[list["RecommendationLog"]] = relationship(
        back_populates="replacement_food",
        foreign_keys="RecommendationLog.replacement_food_id",
    )

    def __repr__(self) -> str:
        return f"Food(id={self.id!s}, external_id={self.external_id!r}, name={self.name!r})"


class MealItem(Base):
    __tablename__ = "meal_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("grams > 0", name="grams_positive"),
        CheckConstraint("char_length(trim(unit)) > 0", name="unit_not_blank"),
        Index("ix_static_meal_items_meal_id", "meal_id"),
        Index("ix_static_meal_items_food_id", "food_id"),
        Index("ux_static_meal_items_meal_id_sort_order", "meal_id", "sort_order", unique=True),
        {"schema": "static"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    meal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("static.meals.id", ondelete="CASCADE"), nullable=False)
    food_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("static.foods.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    grams: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))

    meal: Mapped["Meal"] = relationship(back_populates="meal_items", foreign_keys=[meal_id], primaryjoin="Meal.id==MealItem.meal_id")
    food: Mapped[Food] = relationship(back_populates="meal_items", foreign_keys=[food_id], primaryjoin="Food.id==MealItem.food_id")

    def __repr__(self) -> str:
        return f"MealItem(id={self.id!s}, meal_id={self.meal_id!s}, food_id={self.food_id!s})"
