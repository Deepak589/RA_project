from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import RecommendationFeedbackStatus

if TYPE_CHECKING:
    from app.models.food import Food
    from app.models.meal import Meal
    from app.models.user import User


feedback_status_enum = PGEnum(
    RecommendationFeedbackStatus,
    name="feedback_status",
    schema="intelligence",
    create_type=False,
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
)


class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"
    __table_args__ = (
        CheckConstraint(
            "recommended_for_meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name="valid_recommendation_meal_type",
        ),
        CheckConstraint(
            "(feedback_status <> 'replaced' OR num_nonnulls(replacement_food_id, replacement_meal_id) = 1)",
            name="replacement_target_required",
        ),
        Index("ix_intelligence_recommendation_logs_feedback_status", "feedback_status"),
        Index("ix_intelligence_recommendation_logs_user_id_shown_at", "user_id", "shown_at"),
        {"schema": "intelligence"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    meal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("static.meals.id", ondelete="SET NULL"), nullable=True)
    recommended_for_meal_type: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation_context_jsonb: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    explanation_text: Mapped[str] = mapped_column(Text, nullable=False)
    alternatives_jsonb: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    rules_applied_jsonb: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    rule_priority_applied: Mapped[str | None] = mapped_column(String(30), nullable=True)
    flare_mode_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    recommendation_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    daily_nutrition_context_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    shown_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    feedback_status: Mapped[RecommendationFeedbackStatus] = mapped_column(
        feedback_status_enum, nullable=False, server_default=text("'pending'")
    )
    feedback_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    replacement_food_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("static.foods.id", ondelete="SET NULL"), nullable=True
    )
    replacement_meal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("static.meals.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    user: Mapped["User"] = relationship(
        back_populates="recommendation_logs",
        foreign_keys=[user_id],
        primaryjoin="User.id==RecommendationLog.user_id",
    )
    recommended_meal: Mapped["Meal | None"] = relationship(
        back_populates="recommendation_logs",
        foreign_keys=[meal_id],
        primaryjoin="Meal.id==RecommendationLog.meal_id",
    )
    replacement_food: Mapped["Food | None"] = relationship(
        back_populates="replacement_recommendations",
        foreign_keys=[replacement_food_id],
        primaryjoin="Food.id==RecommendationLog.replacement_food_id",
    )
    replacement_meal: Mapped["Meal | None"] = relationship(
        back_populates="replacement_recommendation_logs",
        foreign_keys=[replacement_meal_id],
        primaryjoin="Meal.id==RecommendationLog.replacement_meal_id",
    )

    def __repr__(self) -> str:
        return (
            f"RecommendationLog(id={self.id!s}, user_id={self.user_id!s}, "
            f"feedback_status={self.feedback_status.value!r})"
        )
