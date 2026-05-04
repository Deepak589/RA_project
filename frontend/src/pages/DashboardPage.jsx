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
import { formatDate, greeting } from "../utils/formatters.js";

export default function DashboardPage() {
  const { user } = useAuth();
  const { data, isLoading, isError, refetch } = useTodayDashboard();
  const recommendation = data?.recommendation?.recommended_meal || data?.next_recommendation?.recommended_meal || data?.next_recommendation?.primary || data?.primary_recommendation;
  const recommendationId = data?.recommendation?.recommendation_log_id || data?.next_recommendation?.recommendation_log_id || data?.recommendation_log_id;

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
