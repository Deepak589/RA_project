from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import FlareLevel, MissingIngredientStatus

if TYPE_CHECKING:
    from app.models.food import Food
    from app.models.meal import CustomMeal, Meal
    from app.models.user import User


flare_level_enum = PGEnum(
    FlareLevel,
    name="flare_level",
    schema="tracking",
    create_type=False,
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
)


class FoodLog(Base):
    __tablename__ = "food_logs"
    __table_args__ = (
        CheckConstraint("meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')", name="valid_food_log_meal_type"),
        CheckConstraint("(portion_g IS NULL OR portion_g > 0)", name="portion_positive"),
        CheckConstraint("num_nonnulls(food_id, meal_id, custom_food_name) = 1", name="single_log_source"),
        Index("ix_tracking_food_logs_user_id_logged_at", "user_id", "logged_at"),
        Index("ix_tracking_food_logs_logged_at", "logged_at"),
        {"schema": "tracking"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    food_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("static.foods.id", ondelete="SET NULL"), nullable=True)
    meal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("static.meals.id", ondelete="SET NULL"), nullable=True)
    custom_food_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    meal_type: Mapped[str] = mapped_column(Text, nullable=False)
    portion_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    portion_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    log_source: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'manual_log'"))
    raw_portion_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    cooking_state_at_log: Mapped[str | None] = mapped_column(String(20), nullable=True)
    conversion_factor_at_log: Mapped[Decimal | None] = mapped_column(Numeric(5, 3), nullable=True)
    display_calories: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    display_protein_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    recommendation_meal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("static.meals.id", ondelete="SET NULL"), nullable=True
    )
    custom_meal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tracking.custom_meals.id", ondelete="SET NULL"), nullable=True
    )
    logged_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    user: Mapped["User"] = relationship(back_populates="food_logs", foreign_keys=[user_id], primaryjoin="User.id==FoodLog.user_id")
    food: Mapped["Food | None"] = relationship(back_populates="food_logs", foreign_keys=[food_id], primaryjoin="Food.id==FoodLog.food_id")
    meal: Mapped["Meal | None"] = relationship(back_populates="food_logs", foreign_keys=[meal_id], primaryjoin="Meal.id==FoodLog.meal_id")
    recommendation_meal: Mapped["Meal | None"] = relationship(foreign_keys=[recommendation_meal_id])
    custom_meal: Mapped["CustomMeal | None"] = relationship(foreign_keys=[custom_meal_id])

    def __repr__(self) -> str:
        return f"FoodLog(id={self.id!s}, user_id={self.user_id!s}, meal_type={self.meal_type!r})"


class SymptomLog(Base):
    __tablename__ = "symptom_logs"
    __table_args__ = (
        CheckConstraint("pain_score BETWEEN 0 AND 10", name="pain_score_range"),
        CheckConstraint("fatigue_score BETWEEN 0 AND 10", name="fatigue_score_range"),
        CheckConstraint("stiffness_score BETWEEN 0 AND 10", name="stiffness_score_range"),
        CheckConstraint("swelling_score BETWEEN 0 AND 10", name="swelling_score_range"),
        Index("ix_tracking_symptom_logs_user_id_logged_at", "user_id", "logged_at"),
        Index("ix_tracking_symptom_logs_logged_at", "logged_at"),
        {"schema": "tracking"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    pain_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    fatigue_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    stiffness_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    swelling_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    flare_level: Mapped[FlareLevel] = mapped_column(flare_level_enum, nullable=False, server_default=text("'none'"))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalation_triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    stiffness_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mobility_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    energy_level: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    sleep_quality: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    mood_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))

    user: Mapped["User"] = relationship(back_populates="symptom_logs", foreign_keys=[user_id], primaryjoin="User.id==SymptomLog.user_id")

    def __repr__(self) -> str:
        return f"SymptomLog(id={self.id!s}, user_id={self.user_id!s}, pain_score={self.pain_score})"


class LifestyleLog(Base):
    __tablename__ = "lifestyle_logs"
    __table_args__ = (
        CheckConstraint("(sleep_hours IS NULL OR (sleep_hours >= 0 AND sleep_hours <= 24))", name="sleep_hours_range"),
        CheckConstraint("(steps IS NULL OR steps >= 0)", name="steps_non_negative"),
        CheckConstraint("(water_ml IS NULL OR water_ml >= 0)", name="water_non_negative"),
        CheckConstraint("(stress_level IS NULL OR stress_level BETWEEN 0 AND 10)", name="stress_range"),
        Index("ix_tracking_lifestyle_logs_user_id_log_date", "user_id", "log_date"),
        UniqueConstraint("user_id", "log_date", name="uq_tracking_lifestyle_logs_user_log_date"),
        {"schema": "tracking"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    sleep_hours: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    water_ml: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stress_level: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    exercise_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    exercise_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    smoking: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    alcohol: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    medication_taken: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    user: Mapped["User"] = relationship(back_populates="lifestyle_logs", foreign_keys=[user_id], primaryjoin="User.id==LifestyleLog.user_id")

    def __repr__(self) -> str:
        return f"LifestyleLog(id={self.id!s}, user_id={self.user_id!s}, log_date={self.log_date!s})"


class MissingIngredient(Base):
    __tablename__ = "missing_ingredients"
    __table_args__ = (
        CheckConstraint(
            "status IN ('missing_completely', 'user_entered', 'under_review', 'added', 'rejected')",
            name="ck_tracking_missing_ingredients_status",
        ),
        CheckConstraint("char_length(trim(ingredient_name)) > 0", name="ck_tracking_missing_ingredients_name_not_blank"),
        CheckConstraint("reported_count > 0", name="ck_tracking_missing_ingredients_reported_count_positive"),
        Index("ux_tracking_missing_ingredients_name_lower", text("LOWER(ingredient_name)"), unique=True),
        Index("ix_tracking_missing_ingredients_status", "status"),
        Index("ix_tracking_missing_ingredients_reported_count", "reported_count"),
        {"schema": "tracking"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    ingredient_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=MissingIngredientStatus.MISSING_COMPLETELY.value, server_default=text("'missing_completely'"))
    submitted_calories: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    submitted_protein_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    submitted_carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    submitted_fat_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    submitted_fiber_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    submitted_sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    submitted_sodium_mg: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    submitted_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    food_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("static.foods.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )
