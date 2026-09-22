from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.recommendation import RecommendationLog
from app.models.user import User
from app.services.rule_engine import (
    VARIETY_PENALTY_TIERS,
    apply_variety_penalty,
    get_next_meal_recommendation,
)


def test_penalty_tiers_match_spec() -> None:
    assert VARIETY_PENALTY_TIERS == [(1, -2.0), (2, -4.0), (3, -6.0)]


def test_no_penalty_with_empty_recent_list() -> None:
    assert apply_variety_penalty(8.0, "meal-a", []) == 8.0


def test_penalty_tier_1_one_recent_rec() -> None:
    assert apply_variety_penalty(8.0, "meal-a", ["meal-a"]) == 6.0


def test_penalty_tier_2_two_recent_recs() -> None:
    assert apply_variety_penalty(8.0, "meal-a", ["meal-a", "meal-a"]) == 4.0


def test_penalty_tier_3_three_or_more_recent_recs() -> None:
    assert apply_variety_penalty(8.0, "meal-a", ["meal-a", "meal-a", "meal-a"]) == 2.0


def test_penalty_does_not_apply_to_different_meal() -> None:
    assert apply_variety_penalty(8.0, "meal-b", ["meal-a", "meal-a", "meal-a"]) == 8.0


def test_penalty_never_goes_below_zero() -> None:
    # 4.0 - 6.0 = -2.0 → clamped to 0.0
    assert apply_variety_penalty(4.0, "meal-a", ["meal-a", "meal-a", "meal-a"]) == 0.0


@pytest.mark.asyncio
async def test_variety_penalty_demotes_repeated_meal() -> None:
    """Meal recommended 3+ times recently must not be top recommendation."""
    async with AsyncSessionLocal() as db:
        user = (await db.scalars(select(User).limit(1))).first()
        if user is None:
            pytest.skip("No users in database")

        # Get first recommendation — also writes 1 RecommendationLog for the top meal
        rec1 = await get_next_meal_recommendation(db, user.id, meal_type="dinner")
        top_meal_id = rec1.primary_recommendation.id
        log1_id = rec1.recommendation_log_id

        # Seed 2 more logs to bring the total to 3 (≥3 tier → -6.0 penalty)
        seeded_ids: list = []
        for _ in range(2):
            entry = RecommendationLog(
                user_id=user.id,
                meal_id=top_meal_id,
                recommended_for_meal_type="dinner",
                shown_at=datetime.now(timezone.utc).replace(tzinfo=None),
                feedback_status="pending",
                recommendation_context_jsonb={},
                explanation_text="seeded by test_variety_penalty",
            )
            db.add(entry)
            await db.flush()
            seeded_ids.append(entry.id)
        await db.commit()

        log2_id = None
        try:
            rec2 = await get_next_meal_recommendation(db, user.id, meal_type="dinner")
            log2_id = rec2.recommendation_log_id
            assert rec2.primary_recommendation.id != top_meal_id, (
                f"Variety penalty failed — same meal {top_meal_id} recommended after 3 recent recs"
            )
        finally:
            for eid in [*seeded_ids, log1_id, log2_id]:
                if eid is None:
                    continue
                obj = await db.get(RecommendationLog, eid)
                if obj:
                    await db.delete(obj)
            await db.commit()
