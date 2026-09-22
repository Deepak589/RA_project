from __future__ import annotations

import logging
import random
from dataclasses import asdict, dataclass
from datetime import datetime, time, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import RecommendationFeedbackStatus
from app.models.food import MealItem
from app.models.log import LifestyleLog, SymptomLog
from app.models.meal import Meal, MealIngredient
from app.models.recommendation import RecommendationLog
from app.models.user import UserPreferences
from app.services.medication_filter import apply_medication_filter, get_user_medications
from app.services.nutrition_tracker import (
    DailyNutritionState,
    NutritionGaps,
    UserProfile,
    get_nutrition_gaps,
    get_todays_nutrition,
    nutrition_context_json,
)


@dataclass
class RecommendationResult:
    primary_recommendation: Meal
    alternatives: list[Meal]
    explanation: str
    rule_applied: str
    flare_mode_active: bool
    recommendation_mode: str
    nutrition_context: DailyNutritionState
    gaps: NutritionGaps
    recommendation_log_id: UUID | None = None

VARIETY_LOOKBACK_COUNT = 8
MIN_ALTERNATIVES = 3
MIN_ELIGIBLE_POOL_SIZE = 3
RECENT_DIVERSITY_LOOKBACK_COUNT = 3
VARIETY_PENALTY_TIERS = [
    (1, -2.0),
    (2, -4.0),
    (3, -6.0),
]


VALID_DIET_OVERRIDES = {"vegetarian", "non_vegetarian"}


async def get_next_meal_recommendation(
    db: AsyncSession,
    user_id: UUID,
    meal_type: str,
    flare_active: bool = False,
    limit: int = 5,
    diet_override: str | None = None,
) -> RecommendationResult:
    candidates = await _load_candidate_meals(db, meal_type)
    if not candidates:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No candidate meals found")

    preferences = await _load_preferences(db, user_id)
    logs: list[str] = []
    candidates = _apply_safety_filter(candidates, preferences, logs)
    if not candidates:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No meals remain after allergy filtering")

    medications = await get_user_medications(db, user_id)
    medication_result = apply_medication_filter(candidates, medications)
    candidates = medication_result.filtered_meals
    logs.extend(medication_result.applied_rules)

    dominant_rule = "score"
    if medication_result.applied_rules and medication_result.applied_rules[0].startswith("[VERIFY") is False:
        dominant_rule = "medication"

    if flare_active:
        recommendation_mode = "flare_only"
        logs.append("[QUERY: flare_active=true → flare_only mode]")
    else:
        recommendation_mode = await get_recommendation_mode(db, user_id)

    # Lifestyle override — poor sleep or high stress escalates mode toward flare_only
    lifestyle = await get_todays_lifestyle(db, user_id)
    if lifestyle is not None and recommendation_mode == "normal":
        sleep_low = lifestyle.sleep_hours is not None and lifestyle.sleep_hours < 6
        stress_high = lifestyle.stress_level is not None and lifestyle.stress_level >= 7
        if sleep_low and stress_high:
            recommendation_mode = "flare_only"
            logs.append("[LIFESTYLE: poor sleep + high stress → flare_only mode]")
        elif sleep_low or stress_high:
            recommendation_mode = "mixed"
            logs.append("[LIFESTYLE: poor sleep or high stress → mixed mode]")
    elif lifestyle is not None and recommendation_mode == "mixed":
        sleep_low = lifestyle.sleep_hours is not None and lifestyle.sleep_hours < 5
        stress_high = lifestyle.stress_level is not None and lifestyle.stress_level >= 8
        if sleep_low or stress_high:
            recommendation_mode = "flare_only"
            logs.append("[LIFESTYLE: severe sleep/stress on top of symptom mixed → flare_only mode]")

    # medication_taken=False — log only, do not change scoring (clinical boundary)
    if lifestyle is not None and lifestyle.medication_taken is False:
        logs.append("[LIFESTYLE: medication not taken today — no score change, clinician boundary]")

    explanation_prefix = ""
    if recommendation_mode == "flare_only":
        dominant_rule = "flare"
        flare_candidates = [meal for meal in candidates if meal.is_flare_friendly]
        if flare_candidates:
            candidates = flare_candidates
        else:
            logs.append("[DESIGN DECISION: no flare-friendly meals remained after allergy, medication, and preference filters; fallback to full pool]")
        explanation_prefix = "You reported pain today. These meals are gentle, easy to prepare, and anti-inflammatory. "
    elif recommendation_mode == "mixed":
        dominant_rule = "flare"
        lifestyle_note = ""
        if lifestyle is not None:
            if lifestyle.sleep_hours is not None and lifestyle.sleep_hours < 6:
                lifestyle_note = " Your sleep was short today."
            elif lifestyle.stress_level is not None and lifestyle.stress_level >= 7:
                lifestyle_note = " Your stress level was high today."
        explanation_prefix = (
            f"You reported some discomfort today.{lifestyle_note} "
            "We have prioritised gentle meals while keeping your nutrition balanced. "
        )

    nutrition_context = await get_todays_nutrition(db, user_id)
    gaps = get_nutrition_gaps(nutrition_context, UserProfile())
    if _apply_nutrition_boosts(candidates, gaps):
        dominant_rule = "nutrition" if dominant_rule == "score" else dominant_rule

    effective_override = diet_override if diet_override in VALID_DIET_OVERRIDES else None
    if _apply_preferences(candidates, preferences, effective_override):
        dominant_rule = "preference" if dominant_rule == "score" else dominant_rule
    if effective_override:
        logs.append(f"[PREFERENCE OVERRIDE: diet_override={effective_override}]")

    recent_logs = await _load_recent_recommendation_logs(db, user_id, meal_type, VARIETY_LOOKBACK_COUNT)
    variety_result = _apply_variety_penalty(candidates, recent_logs)
    if variety_result == "variety_pool_reset":
        dominant_rule = "variety_pool_reset"
        logs.append("[VARIETY: candidate pool below 3 after recent-window penalty; reset variety scoring for this meal type]")
    elif variety_result == "variety_pool_reset_partial":
        dominant_rule = "variety_pool_reset"
        logs.append("[VARIETY: partial reset — repeat offenders penalized]")
    elif variety_result == "variety":
        dominant_rule = "variety" if dominant_rule == "score" else dominant_rule

    candidates = _final_rank(candidates, recommendation_mode)
    desired_count = max(limit, MIN_ALTERNATIVES + 1)
    top = candidates[:desired_count]
    if not top:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No recommendations available")

    primary = top[0]
    alternatives = top[1:desired_count]
    alternatives = _ensure_minimum_alternatives(primary, alternatives, candidates, desired_count - 1)
    alternatives = _apply_diversity_guard(primary, alternatives, candidates, recent_logs, preferences, desired_count - 1)
    explanation = explanation_prefix + _build_explanation(primary, dominant_rule, recommendation_mode == "flare_only", gaps)
    log = RecommendationLog(
        user_id=user_id,
        meal_id=primary.id,
        recommended_for_meal_type=meal_type,
        recommendation_context_jsonb={
            "meal_type": meal_type,
            "medications": medications,
            "logs": logs,
            "lifestyle": {
                "sleep_hours": float(lifestyle.sleep_hours) if lifestyle and lifestyle.sleep_hours is not None else None,
                "stress_level": int(lifestyle.stress_level) if lifestyle and lifestyle.stress_level is not None else None,
                "medication_taken": lifestyle.medication_taken if lifestyle else None,
            } if lifestyle else None,
        },
        explanation_text=explanation,
        alternatives_jsonb=[{"meal_id": str(meal.id), "name": meal.name} for meal in alternatives],
        rules_applied_jsonb=[{"rule": item} for item in logs],
        rule_priority_applied=dominant_rule,
        flare_mode_active=recommendation_mode == "flare_only",
        recommendation_mode=recommendation_mode,
        daily_nutrition_context_json=nutrition_context_json(nutrition_context),
        feedback_status=RecommendationFeedbackStatus.PENDING,
        shown_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    return RecommendationResult(
        primary_recommendation=primary,
        alternatives=alternatives,
        explanation=explanation,
        rule_applied=dominant_rule,
        flare_mode_active=recommendation_mode == "flare_only",
        recommendation_mode=recommendation_mode,
        nutrition_context=nutrition_context,
        gaps=gaps,
        recommendation_log_id=log.id,
    )


async def get_recommendation_mode(db: AsyncSession, user_id: UUID) -> str:
    today = datetime.now(timezone.utc).date()
    start = datetime.combine(today, time.min)
    end = start + timedelta(days=1)
    symptom = await db.scalar(
        select(SymptomLog)
        .where(SymptomLog.user_id == user_id, SymptomLog.logged_at >= start, SymptomLog.logged_at < end)
        .order_by(SymptomLog.logged_at.desc())
    )
    if symptom is None:
        return "normal"

    flare_level = getattr(symptom.flare_level, "value", symptom.flare_level)
    if symptom.pain_score >= 6 or flare_level in {"moderate", "severe"}:
        return "flare_only"
    if symptom.pain_score >= 4 or flare_level == "mild":
        return "mixed"
    return "normal"


async def get_todays_lifestyle(db: AsyncSession, user_id: UUID) -> LifestyleLog | None:
    today = datetime.now(timezone.utc).date()
    return await db.scalar(
        select(LifestyleLog).where(LifestyleLog.user_id == user_id, LifestyleLog.log_date == today)
    )


async def _load_candidate_meals(db: AsyncSession, meal_type: str) -> list[Meal]:
    result = await db.scalars(
        select(Meal)
        .where(Meal.is_curated.is_(True), Meal.meal_type == meal_type)
        .options(
            selectinload(Meal.ingredients).selectinload(MealIngredient.food),
            selectinload(Meal.meal_items).selectinload(MealItem.food),
        )
    )
    return list(result)


async def _load_preferences(db: AsyncSession, user_id: UUID) -> UserPreferences | None:
    return await db.scalar(select(UserPreferences).where(UserPreferences.user_id == user_id))


def _apply_safety_filter(meals: list[Meal], preferences: UserPreferences | None, logs: list[str]) -> list[Meal]:
    allergens = [item.lower() for item in (getattr(preferences, "allergies_jsonb", None) or [])]
    if not allergens:
        return meals
    kept: list[Meal] = []
    for meal in meals:
        names = [meal.name.lower()]
        names.extend((getattr(ingredient.food, "name", "") or "").lower() for ingredient in meal.ingredients)
        matched = next((allergen for allergen in allergens if any(allergen in name for name in names)), None)
        if matched:
            logs.append(f"[SAFETY: removed {meal.name} due to allergy {matched}]")
            continue
        kept.append(meal)
    return kept


def _sort_for_flare(meals: list[Meal]) -> list[Meal]:
    return sorted(meals, key=lambda meal: (not meal.is_flare_friendly, -_score(meal), meal.name))


def _apply_nutrition_boosts(meals: list[Meal], gaps: NutritionGaps) -> bool:
    applied = False
    for meal in meals:
        if gaps.is_protein_low and _number(meal, "total_protein_g", "protein_g") >= 25:
            _bump(meal, 1.0)
            applied = True
        if gaps.is_fiber_low and _number(meal, "total_fiber_g", "fiber_g") >= 8:
            _bump(meal, 1.0)
            applied = True
        if gaps.is_omega3_low and _number(meal, "total_omega3_g") >= 0.5:
            _bump(meal, 1.5)
            applied = True
        if gaps.is_sugar_over:
            if _number(meal, "total_sugar_g", "sugar_g") <= 5:
                _bump(meal, 1.0)
                applied = True
            if _number(meal, "total_sugar_g", "sugar_g") >= 15:
                _bump(meal, -2.0)
                applied = True
        if gaps.is_sodium_over:
            if _number(meal, "total_sodium_mg", "sodium_mg") <= 300:
                _bump(meal, 1.0)
                applied = True
            if _number(meal, "total_sodium_mg", "sodium_mg") >= 600:
                _bump(meal, -1.5)
                applied = True
    return applied


def _apply_preferences(
    meals: list[Meal],
    preferences: UserPreferences | None,
    diet_override: str | None = None,
) -> bool:
    flags = [flag.lower() for flag in (getattr(preferences, "dietary_flags_jsonb", None) or [])]
    goals = [flag.lower() for flag in (getattr(preferences, "goal_flags_jsonb", None) or [])]
    changed = False
    active_dietary_flags = [flag for flag in flags if flag not in {"no_preference"}]
    has_real_preference = bool(active_dietary_flags)
    if diet_override in VALID_DIET_OVERRIDES and not has_real_preference:
        active_dietary_flags = [diet_override]
        has_real_preference = True
    if has_real_preference:
        original_count = len(meals)
        filtered = [meal for meal in meals if _meal_matches_dietary_flags(meal, active_dietary_flags)]
        override_drove_filter = diet_override in VALID_DIET_OVERRIDES and not [f for f in flags if f != "no_preference"]
        if not filtered and override_drove_filter:
            logging.getLogger(__name__).warning(
                "[PREFERENCE OVERRIDE: no %s meals for this meal type — fallback to full pool]",
                diet_override,
            )
        else:
            meals[:] = filtered
        changed = len(meals) != original_count
    for meal in meals:
        if meal.cuisine_type and meal.cuisine_type.lower() in flags:
            _bump(meal, 0.5)
            changed = True
        if ("budget_friendly" in goals or "budget_friendly" in flags) and "budget_friendly" in (meal.tags or []):
            _bump(meal, 0.5)
            changed = True
    return changed


async def _load_recent_recommendation_logs(
    db: AsyncSession,
    user_id: UUID,
    meal_type: str,
    limit: int,
) -> list[RecommendationLog]:
    result = await db.scalars(
        select(RecommendationLog)
        .where(
            RecommendationLog.user_id == user_id,
            RecommendationLog.recommended_for_meal_type == meal_type,
        )
        .options(selectinload(RecommendationLog.recommended_meal))
        .order_by(RecommendationLog.shown_at.desc())
        .limit(limit)
    )
    return list(result)


def _apply_variety_penalty(meals: list[Meal], recent_logs: list[RecommendationLog]) -> str | None:
    recent_ids = [str(log.meal_id) for log in recent_logs if log.meal_id is not None]
    if not recent_ids:
        return None

    base_scores = {str(meal.id): _score(meal) for meal in meals}
    for meal in meals:
        setattr(meal, "adjusted_score", apply_variety_penalty(base_scores[str(meal.id)], str(meal.id), recent_ids))

    eligible_pool = [meal for meal in meals if str(meal.id) not in recent_ids]
    if len(eligible_pool) < MIN_ELIGIBLE_POOL_SIZE:
        repeat_offenders = {mid for mid in recent_ids if recent_ids.count(mid) >= 2}
        for meal in meals:
            mid = str(meal.id)
            if mid in repeat_offenders:
                continue
            setattr(meal, "adjusted_score", base_scores[mid])
        return "variety_pool_reset_partial"

    return "variety"


def apply_variety_penalty(score: float, meal_id: str, recent_ids: list[str]) -> float:
    count = recent_ids.count(meal_id)
    penalty = 0.0
    for threshold, tier_penalty in VARIETY_PENALTY_TIERS:
        if count >= threshold:
            penalty = tier_penalty
    return max(0.0, score + penalty)


def _final_rank(meals: list[Meal], recommendation_mode: str) -> list[Meal]:
    def shuffled(items: list[Meal]) -> list[Meal]:
        ranked = list(items)
        random.shuffle(ranked)
        return ranked

    def shuffle_by_priority(items: list[Meal]) -> list[Meal]:
        buckets: dict[float, list[Meal]] = {}
        for meal in items:
            buckets.setdefault(_priority_delta(meal), []).append(meal)

        ranked: list[Meal] = []
        for priority in sorted(buckets.keys(), reverse=True):
            ranked.extend(shuffled(buckets[priority]))
        return ranked

    if recommendation_mode == "flare_only":
        flare_meals = [meal for meal in meals if meal.is_flare_friendly]
        other_meals = [meal for meal in meals if not meal.is_flare_friendly]
        return shuffle_by_priority(flare_meals) + shuffle_by_priority(other_meals)
    if recommendation_mode == "mixed":
        flare_meals = [meal for meal in meals if meal.is_flare_friendly]
        normal_meals = [meal for meal in meals if not meal.is_flare_friendly]
        return shuffle_by_priority(flare_meals) + shuffle_by_priority(normal_meals)
    return shuffle_by_priority(meals)


def _ensure_minimum_alternatives(
    primary: Meal,
    alternatives: list[Meal],
    ranked_meals: list[Meal],
    minimum_count: int,
) -> list[Meal]:
    selected_ids = {str(primary.id), *(str(meal.id) for meal in alternatives)}
    filled = list(alternatives)
    for meal in ranked_meals:
        meal_id = str(meal.id)
        if meal_id in selected_ids:
            continue
        filled.append(meal)
        selected_ids.add(meal_id)
        if len(filled) >= minimum_count:
            break
    return filled


def _apply_diversity_guard(
    primary: Meal,
    alternatives: list[Meal],
    ranked_meals: list[Meal],
    recent_logs: list[RecommendationLog],
    preferences: UserPreferences | None,
    desired_count: int,
) -> list[Meal]:
    flags = {flag.lower() for flag in (getattr(preferences, "dietary_flags_jsonb", None) or [])}
    if flags.intersection({"vegetarian", "vegan"}):
        return alternatives

    last_three = recent_logs[:RECENT_DIVERSITY_LOOKBACK_COUNT]
    if len(last_three) < RECENT_DIVERSITY_LOOKBACK_COUNT:
        return alternatives
    if not all(log.recommended_meal and log.recommended_meal.is_vegetarian for log in last_three):
        return alternatives
    if any(not meal.is_vegetarian for meal in alternatives):
        return alternatives

    selected_ids = {str(primary.id), *(str(meal.id) for meal in alternatives)}
    non_vegetarian = next(
        (
            meal for meal in ranked_meals
            if not meal.is_vegetarian and str(meal.id) not in selected_ids
        ),
        None,
    )
    if non_vegetarian is None:
        return alternatives

    diversified = [non_vegetarian, *alternatives]
    deduped: list[Meal] = []
    seen_ids: set[str] = set()
    for meal in diversified:
        meal_id = str(meal.id)
        if meal_id in seen_ids:
            continue
        deduped.append(meal)
        seen_ids.add(meal_id)
        if len(deduped) >= desired_count:
            break
    return deduped


def _build_explanation(meal: Meal, rule: str, flare_active: bool, gaps: NutritionGaps) -> str:
    reasons: list[str] = []
    if flare_active and meal.is_flare_friendly:
        reasons.append("you are in flare mode, and this meal is gentle, low effort, and anti-inflammatory")
    if gaps.is_omega3_low and _number(meal, "total_omega3_g") >= 0.5:
        reasons.append(f"your omega-3 intake today is low and this meal provides {float(meal.total_omega3_g or 0):.1f}g")
    elif gaps.is_protein_low and _number(meal, "total_protein_g", "protein_g") >= 25:
        reasons.append(f"your protein intake today is low and this meal provides {float(meal.total_protein_g or 0):.0f}g")
    elif gaps.is_fiber_low and _number(meal, "total_fiber_g", "fiber_g") >= 8:
        reasons.append(f"your fiber intake today is low and this meal provides {float(meal.total_fiber_g or 0):.0f}g")
    if not reasons:
        reasons.append("it ranks highly for anti-inflammatory nutrition and may help support your daily goals")
    return f"{meal.name} recommended because: {', and '.join(reasons)}. Dominant rule: {rule}."


def _score(meal: Meal) -> float:
    return float(getattr(meal, "adjusted_score", meal.anti_inflammatory_score or 0))


def _priority_delta(meal: Meal) -> float:
    if not hasattr(meal, "adjusted_score"):
        return 0.0
    return round(float(getattr(meal, "adjusted_score", 0.0)) - float(meal.anti_inflammatory_score or 0), 1)


def _bump(meal: Meal, delta: float) -> None:
    setattr(meal, "adjusted_score", max(0.0, min(10.0, _score(meal) + delta)))


def _number(meal: Meal, *names: str) -> float:
    for name in names:
        value = getattr(meal, name, None)
        if value is not None:
            return float(value)
    return 0.0


def _meal_matches_dietary_flags(meal: Meal, flags: list[str]) -> bool:
    tags = {tag.lower() for tag in (meal.dietary_tags_jsonb or [])}
    tags.update(tag.lower() for tag in (meal.tags or []))
    if meal.is_vegetarian:
        tags.add("vegetarian")
    if "vegan" in tags:
        tags.add("vegetarian")

    flag_requirements = {
        "vegetarian": {"vegetarian", "vegan"},
        "pescatarian": {"pescatarian", "vegetarian", "vegan"},
        "vegan": {"vegan"},
        "gluten_free": {"gluten_free"},
        "dairy_free": {"dairy_free", "vegan"},
        "low_sodium": {"low_sodium"},
    }
    for flag in flags:
        if flag == "non_vegetarian":
            if meal.is_vegetarian or tags.intersection({"vegetarian", "vegan"}):
                return False
            continue
        if flag in flag_requirements and not tags.intersection(flag_requirements[flag]):
            return False
    return True


def result_context(result: RecommendationResult) -> dict[str, object]:
    return {
        "primary_id": str(result.primary_recommendation.id),
        "alternative_ids": [str(meal.id) for meal in result.alternatives],
        "rule_applied": result.rule_applied,
        "flare_mode_active": result.flare_mode_active,
        "recommendation_mode": result.recommendation_mode,
        "nutrition_context": asdict(result.nutrition_context),
        "gaps": asdict(result.gaps),
        "recommendation_log_id": str(result.recommendation_log_id) if result.recommendation_log_id else None,
    }
