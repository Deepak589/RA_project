import { useState } from "react";
import { Link } from "react-router-dom";
import AppLayout from "../components/layout/AppLayout.jsx";
import MealCard from "../components/meals/MealCard.jsx";
import FlareBanner from "../components/meals/FlareBanner.jsx";
import NutritionSummary from "../components/logs/NutritionSummary.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import EscalationBanner from "../components/ui/EscalationBanner.jsx";
import Spinner from "../components/ui/Spinner.jsx";
import { createFoodLog } from "../api/logs";
import { submitRecommendationFeedback } from "../api/recommendations";
import { useAuth } from "../hooks/useAuth.js";
import { useTodayDashboard } from "../hooks/useDashboard.js";
import { useProfile } from "../hooks/useProfile.js";
import { formatDate, greeting } from "../utils/formatters.js";

const DIET_OVERRIDE_KEY = "diet_override";

function readStoredOverride() {
  if (typeof window === "undefined") return null;
  const value = window.localStorage.getItem(DIET_OVERRIDE_KEY);
  return value === "vegetarian" || value === "non_vegetarian" ? value : null;
}

function hasRealDietPreference(flags) {
  if (!Array.isArray(flags) || flags.length === 0) return false;
  if (flags.length === 1 && flags[0] === "no_preference") return false;
  return flags.some((flag) => flag && flag !== "no_preference");
}

export default function DashboardPage() {
  const { user } = useAuth();
  const { profile } = useProfile();
  const dietaryFlags = profile.data?.preferences?.dietary_flags_jsonb || profile.data?.preferences?.dietary_flags || [];
  const showDietToggle = !hasRealDietPreference(dietaryFlags);
  const [dietOverride, setDietOverride] = useState(readStoredOverride);
  const activeOverride = showDietToggle ? dietOverride : null;
  const { data, isLoading, isError, refetch } = useTodayDashboard(activeOverride);
  const recommendation = data?.recommendation?.recommended_meal || data?.next_recommendation?.recommended_meal || data?.next_recommendation?.primary || data?.primary_recommendation;
  const recommendationId = data?.recommendation?.recommendation_log_id || data?.next_recommendation?.recommendation_log_id || data?.recommendation_log_id;

  function chooseDiet(value) {
    const next = dietOverride === value ? null : value;
    setDietOverride(next);
    if (typeof window !== "undefined") {
      if (next) window.localStorage.setItem(DIET_OVERRIDE_KEY, next);
      else window.localStorage.removeItem(DIET_OVERRIDE_KEY);
    }
  }

  async function acceptMeal(meal) {
    if (recommendationId) await submitRecommendationFeedback(recommendationId, { feedback: "accepted" });
    await createFoodLog({ log_source: "curated_recommendation", recommendation_meal_id: meal.id, meal_type: meal.meal_type || "lunch" });
    refetch();
  }

  if (isLoading) {
    return <AppLayout title="Dashboard"><div className="flex justify-center py-10"><Spinner size="lg" /></div></AppLayout>;
  }

  return (
    <AppLayout title="Dashboard">
      <section>
        <h2 className="text-xl font-semibold text-gray-800">{greeting()}, {user?.full_name || user?.name || "there"}</h2>
        <p className="text-gray-500">{formatDate()}</p>
      </section>
      {isError && <Card><p className="text-gray-600">Could not load dashboard. Pull to refresh.</p></Card>}
      <EscalationBanner message={data?.escalation_message} />
      <FlareBanner mode={data?.recommendation_mode || (data?.flare_active ? "flare_only" : "")} />
      <NutritionSummary nutrition={data?.nutrition_summary || data?.nutrition} />
      {showDietToggle && (
        <Card>
          <p className="mb-2 font-medium text-gray-700">Filter recommendations</p>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant={dietOverride === "vegetarian" ? "primary" : "secondary"}
              onClick={() => chooseDiet("vegetarian")}
            >
              Veg
            </Button>
            <Button
              variant={dietOverride === "non_vegetarian" ? "primary" : "secondary"}
              onClick={() => chooseDiet("non_vegetarian")}
            >
              Non-Veg
            </Button>
          </div>
        </Card>
      )}
      <MealCard meal={recommendation} explanation={data?.recommendation?.explanation || data?.next_recommendation?.explanation} onAccept={acceptMeal} onSkip={refetch} />
      <div className="grid gap-2">
        <Link to="/meals/log"><Button className="w-full" variant="secondary">+ Log a meal</Button></Link>
        <Link to="/custom-meal"><Button className="w-full" variant="dashed">Build meal</Button></Link>
        <Link to="/symptoms/log"><Button className="w-full" variant="secondary">+ Log symptoms</Button></Link>
        <Link to="/lifestyle/log"><Button className="w-full" variant="secondary">+ Log lifestyle</Button></Link>
      </div>
      {data?.symptom_snapshot || data?.today_symptoms ? (
        <Card>
          <h3 className="font-semibold text-gray-800">Today&apos;s symptoms</h3>
          <p className="mt-1 text-sm text-gray-600">Pain: {(data.symptom_snapshot || data.today_symptoms).pain_score}/10 | Fatigue: {(data.symptom_snapshot || data.today_symptoms).fatigue_score}/10</p>
        </Card>
      ) : null}
    </AppLayout>
  );
}
