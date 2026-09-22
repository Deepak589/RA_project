import { useState, useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import AppLayout from "../components/layout/AppLayout.jsx";
import MealCard from "../components/meals/MealCard.jsx";
import FlareBanner from "../components/meals/FlareBanner.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import Spinner from "../components/ui/Spinner.jsx";
import { createFoodLog } from "../api/logs.js";
import { apiClient } from "../api/client.js";
import { useRecommendation } from "../hooks/useRecommendation.js";
import { currentMealType } from "../utils/formatters.js";

const mealTypes = ["breakfast", "lunch", "dinner", "snack"];

export default function RecommendationPage() {
  const [mealType, setMealType] = useState(currentMealType());
  const queryClient = useQueryClient();
  const { data, isLoading, refetch, feedback } = useRecommendation(mealType);
  const primaryMeal = data?.recommended_meal || data?.primary;
  const alternatives = data?.alternatives || [];
  const showFallback = !primaryMeal;

  // Search state
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchMode, setSearchMode] = useState(false); // true after user types
  const debounceRef = useRef(null);

  useEffect(() => {
    if (query.trim().length < 2) {
      setSearchResults([]);
      setSearchMode(false);
      return;
    }
    setSearchMode(true);
    setSearchLoading(true);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const { data: res } = await apiClient.get("/api/v1/meals", {
          params: { q: query.trim(), meal_type: mealType, limit: 8 },
        });
        setSearchResults(res.items || []);
      } catch {
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [query, mealType]);

  async function accept(meal) {
    if (data?.recommendation_log_id) {
      await feedback.mutateAsync({
        recommendationId: data.recommendation_log_id,
        payload: { feedback: "accepted" },
      });
    }
    await createFoodLog({
      log_source: "curated_recommendation",
      recommendation_meal_id: meal.id,
      meal_type: mealType,
    });
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["food-logs", "today"] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard", "today"] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard", "weekly"] }),
    ]);
    setQuery("");
    setSearchMode(false);
    refetch();
  }

  async function skip() {
    if (data?.recommendation_log_id) {
      await feedback.mutateAsync({
        recommendationId: data.recommendation_log_id,
        payload: { feedback: "skipped" },
      });
    }
    await queryClient.invalidateQueries({ queryKey: ["recommendation", "next"] });
    await refetch();
  }

  return (
    <AppLayout title="Recommendations">
      {/* Meal type tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {mealTypes.map((type) => (
          <Button
            key={type}
            size="sm"
            variant={mealType === type ? "primary" : "secondary"}
            onClick={() => { setMealType(type); setQuery(""); setSearchMode(false); }}
          >
            {type}
          </Button>
        ))}
      </div>

      {/* Search bar */}
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search meals e.g. chicken, salmon…"
          className="w-full rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-800 placeholder-gray-400 focus:border-teal-400 focus:outline-none focus:ring-1 focus:ring-teal-400"
        />
        {query && (
          <button
            type="button"
            onClick={() => { setQuery(""); setSearchMode(false); setSearchResults([]); }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-lg leading-none"
          >
            ×
          </button>
        )}
      </div>

      <FlareBanner mode={data?.recommendation_mode} />

      {/* Search results mode */}
      {searchMode ? (
        <section className="space-y-3">
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">
            Search results for &quot;{query}&quot;
          </p>
          {searchLoading ? (
            <div className="flex justify-center py-6"><Spinner /></div>
          ) : searchResults.length === 0 ? (
            <Card>
              <p className="text-sm text-gray-500">No meals found. Try a different word.</p>
            </Card>
          ) : (
            searchResults.map((meal) => (
              <MealCard
                key={meal.id}
                meal={meal}
                onAccept={accept}
                acceptLabel="Log this meal"
                className="border border-teal-100"
              />
            ))
          )}
          {/* Nutrition note from rules still shown below search results */}
          {data?.explanation && (
            <Card className="bg-amber-50 border-amber-200">
              <p className="text-xs font-medium text-amber-700 uppercase tracking-wide mb-1">Today&apos;s nutrition note</p>
              <p className="text-sm text-amber-800">{data.explanation}</p>
            </Card>
          )}
        </section>
      ) : (
        /* Default recommendation mode */
        <>
          {isLoading ? (
            <div className="flex justify-center py-10"><Spinner /></div>
          ) : showFallback ? (
            <Card className="space-y-3">
              <p className="text-sm text-gray-600">Nothing to show right now — tap refresh.</p>
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
          <p className="text-xs text-gray-400">{modeText(data?.recommendation_mode)}</p>
          {alternatives.length > 0 && (
            <section className="space-y-2">
              <h2 className="font-semibold text-gray-800">Alternatives</h2>
              <div className="space-y-3">
                {alternatives.map((meal) => (
                  <MealCard key={meal.id} meal={meal} compact />
                ))}
              </div>
            </section>
          )}
        </>
      )}

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
