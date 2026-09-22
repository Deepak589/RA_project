from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import AccountDeletionStatus

if TYPE_CHECKING:
    from app.models.log import FoodLog, LifestyleLog, SymptomLog
    from app.models.meal import CustomMeal
    from app.models.recommendation import RecommendationLog


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("char_length(trim(email)) > 3", name="email_length"),
        CheckConstraint("char_length(trim(full_name)) > 0", name="full_name_not_blank"),
        CheckConstraint("char_length(trim(timezone)) > 0", name="timezone_not_blank"),
        Index("ix_core_users_email_lower", text("LOWER(email)"), unique=True),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    email: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    timezone: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'UTC'"))
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'user'"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)

    preferences: Mapped["UserPreferences | None"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    medications: Mapped[list["UserMedication"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    authentication_sessions: Mapped[list["AuthenticationSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    account_deletion_requests: Mapped[list["AccountDeletionRequest"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    food_logs: Mapped[list["FoodLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    symptom_logs: Mapped[list["SymptomLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    lifestyle_logs: Mapped[list["LifestyleLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    recommendation_logs: Mapped[list["RecommendationLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    custom_meals: Mapped[list["CustomMeal"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"User(id={self.id!s}, email={self.email!r})"


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    __table_args__ = (
        CheckConstraint(
            "((disclaimer_accepted = FALSE AND disclaimer_accepted_at IS NULL) OR "
            "(disclaimer_accepted = TRUE AND disclaimer_accepted_at IS NOT NULL))",
            name="disclaimer_acceptance_consistent",
        ),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="References core.users.id",
    )
    allergies_jsonb: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    dietary_flags_jsonb: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    disliked_foods_jsonb: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    goal_flags_jsonb: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    disclaimer_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    disclaimer_accepted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    user: Mapped[User] = relationship(back_populates="preferences", foreign_keys=[user_id], primaryjoin="User.id==UserPreferences.user_id")

    def __repr__(self) -> str:
        return f"UserPreferences(id={self.id!s}, user_id={self.user_id!s})"


class UserMedication(Base):
    __tablename__ = "user_medications"
    __table_args__ = (
        CheckConstraint("char_length(trim(medication_name)) > 0", name="medication_name_not_blank"),
        Index("ix_core_user_medications_user_id", "user_id"),
        Index("ix_core_user_medications_user_id_is_active", "user_id", "is_active"),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    medication_name: Mapped[str] = mapped_column(Text, nullable=False)
    schedule_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    user: Mapped[User] = relationship(back_populates="medications", foreign_keys=[user_id], primaryjoin="User.id==UserMedication.user_id")

    def __repr__(self) -> str:
        return f"UserMedication(id={self.id!s}, user_id={self.user_id!s}, medication_name={self.medication_name!r})"


class AuthenticationSession(Base):
    __tablename__ = "authentication_sessions"
    __table_args__ = (
        CheckConstraint("expires_at > issued_at", name="expires_after_issue"),
        Index("ix_core_authentication_sessions_refresh_token_hash", "refresh_token_hash", unique=True),
        Index("ix_core_authentication_sessions_user_id", "user_id"),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))

    user: Mapped[User] = relationship(
        back_populates="authentication_sessions",
        foreign_keys=[user_id],
        primaryjoin="User.id==AuthenticationSession.user_id",
    )

    def __repr__(self) -> str:
        return f"AuthenticationSession(id={self.id!s}, user_id={self.user_id!s})"


class AccountDeletionRequest(Base):
    __tablename__ = "account_deletion_requests"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'cancelled', 'completed')", name="valid_status"),
        CheckConstraint("scheduled_for >= requested_at", name="scheduled_after_request"),
        CheckConstraint("(processed_at IS NULL OR processed_at >= requested_at)", name="processed_after_request"),
        Index("ix_core_account_deletion_requests_user_id", "user_id"),
        Index(
            "ux_core_account_deletion_requests_user_pending",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=AccountDeletionStatus.PENDING.value, server_default=text("'pending'"))
    requested_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    scheduled_for: Mapped[datetime] = mapped_column(nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    user: Mapped[User] = relationship(
        back_populates="account_deletion_requests",
        foreign_keys=[user_id],
        primaryjoin="User.id==AccountDeletionRequest.user_id",
    )

    def __repr__(self) -> str:
        return f"AccountDeletionRequest(id={self.id!s}, user_id={self.user_id!s}, status={self.status!r})"
