from __future__ import annotations

from enum import Enum


class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    ANY = "any"


class FlareLevel(str, Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class RecommendationFeedbackStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    SKIPPED = "skipped"
    REPLACED = "replaced"


class AccountDeletionStatus(str, Enum):
    PENDING = "pending"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class MissingIngredientStatus(str, Enum):
    MISSING_COMPLETELY = "missing_completely"
    USER_ENTERED = "user_entered"
    UNDER_REVIEW = "under_review"
    ADDED = "added"
    REJECTED = "rejected"
