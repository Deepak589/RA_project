import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import AppLayout from "../components/layout/AppLayout.jsx";
import MealCard from "../components/meals/MealCard.jsx";
import FlareBanner from "../components/meals/FlareBanner.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import Spinner from "../components/ui/Spinner.jsx";
import { createFoodLog } from "../api/logs";
import { useRecommendation } from "../hooks/useRecommendation.js";
import { currentMealType } from "../utils/formatters.js";

const mealTypes = ["breakfast", "lunch", "dinner", "snack"];

export default function RecommendationPage() {
  const [mealType, setMealType] = useState(currentMealType());
  const queryClient = useQueryClient();
  const { data, isLoading, refetch, feedback } = useRecommendation(mealType);
  const primaryMeal = data?.recommended_meal || data?.primary;
  const alternatives = data?.alternatives || [];
  const showFallback = !primaryMeal || alternatives.length === 0;

  async function accept(meal) {
    await feedback.mutateAsync({ recommendationId: data.recommendation_log_id, payload: { feedback: "accepted" } });
    await createFoodLog({ log_source: "curated_recommendation", recommendation_meal_id: meal.id, meal_type: mealType });
    refetch();
  }

  async function skip() {
    if (data?.recommendation_log_id) {
      await feedback.mutateAsync({ recommendationId: data.recommendation_log_id, payload: { feedback: "skipped" } });
    }
    await queryClient.invalidateQueries({ queryKey: ["recommendation", "next"] });
    await refetch();
  }

  return (
    <AppLayout title="Recommendations">
      <div className="flex gap-2 overflow-x-auto">
        {mealTypes.map((type) => <Button key={type} size="sm" variant={mealType === type ? "primary" : "secondary"} onClick={() => setMealType(type)}>{type}</Button>)}
      </div>
      <FlareBanner mode={data?.recommendation_mode} />
      {isLoading ? (
        <div className="flex justify-center py-10"><Spinner /></div>
      ) : showFallback ? (
        <Card className="space-y-3">
          <p className="text-sm text-gray-600">We&apos;ve shown you everything for now — tap refresh to see meals again</p>
          <Button onClick={() => refetch()}>Refresh</Button>
        </Card>
      ) : (
        <MealCard
          meal={primaryMeal}
          explanation={data?.explanation}
          onAccept={accept}
          onSkip={skip}
          acceptLabel="Looks good"
          skipLabel="Show another"
          className="border border-sky-200 bg-sky-50/40"
        />
      )}
      <p className="text-sm text-gray-500">{modeText(data?.recommendation_mode)}</p>
      <section className="space-y-2">
        <h2 className="font-semibold text-gray-800">Alternatives</h2>
        <div className="space-y-3">
          {!showFallback ? alternatives.map((meal) => <MealCard key={meal.id} meal={meal} compact />) : null}
        </div>
      </section>
      <Link to="/custom-meal">
        <Button className="w-full" variant="dashed">Build my own meal</Button>
      </Link>
    </AppLayout>
  );
}

function modeText(mode) {
  if (mode === "mixed") return "Gentle + nutritious options";
  if (mode === "flare_only") return "Gentle meals for today";
  return "Balanced nutrition meals";
}
