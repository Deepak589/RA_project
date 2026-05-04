import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import AppLayout from "../components/layout/AppLayout.jsx";
import FoodSearch from "../components/FoodSearch.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import Input from "../components/ui/Input.jsx";
import Select from "../components/ui/Select.jsx";
import { apiClient } from "../api/client";
import { getTodayFoodLogs } from "../api/logs";
import { getCustomMeals, getMealById } from "../api/meals";
import { currentMealType, formatTime, number } from "../utils/formatters.js";

function CustomMealLogItem({ log, customMeal }) {
  const mealId = log.meal_id || log.recommendation_meal_id;
  const { data: meal } = useQuery({
    queryKey: ["meals", mealId],
    queryFn: () => getMealById(mealId),
    enabled: !!mealId && !customMeal,
    staleTime: Infinity,
  });

  const displayMeal = customMeal || meal;
  const displayName = log.custom_food_name || displayMeal?.name || "Food log";
  const ingredients = displayMeal?.ingredients || [];

  return (
    <Card className="space-y-2">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-medium text-gray-800">{displayName}</h3>
          <p className="text-sm text-gray-500">
            {log.meal_type} · {formatTime(log.logged_at)}
          </p>
        </div>
        <p className="shrink-0 text-sm font-medium text-gray-700">
          {number(log.display_calories)} kcal · {number(log.display_protein_g)}g protein
        </p>
      </div>
      {ingredients.length ? (
        <p className="text-sm text-gray-600">
          {ingredients.map((ingredient) => `${ingredient.food_name} ${number(ingredient.portion_g)}g`).join(" · ")}
        </p>
      ) : null}
    </Card>
  );
}

export default function CustomMealPage() {
  const queryClient = useQueryClient();
  const messageTimeoutRef = useRef(null);
  const [basket, setBasket] = useState([]);
  const [name, setName] = useState("");
  const [mealType, setMealType] = useState(currentMealType());
  const [savedMessage, setSavedMessage] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [recentMeals, setRecentMeals] = useState({});

  const logs = useQuery({ queryKey: ["food-logs", "today"], queryFn: getTodayFoodLogs });
  const customMeals = useQuery({ queryKey: ["custom-meals"], queryFn: getCustomMeals });

  const customMealsById = useMemo(() => {
    const queryMeals = (customMeals.data?.items || []).reduce((accumulator, meal) => {
      accumulator[meal.id] = meal;
      return accumulator;
    }, {});
    return { ...queryMeals, ...recentMeals };
  }, [customMeals.data?.items, recentMeals]);

  useEffect(() => () => {
    if (messageTimeoutRef.current) {
      window.clearTimeout(messageTimeoutRef.current);
    }
  }, []);

  const saveMeal = useMutation({
    mutationFn: async () => {
      const ingredients = basket.map((item) => ({
        food_id: item.foodId,
        grams: Number(item.grams),
      }));

      const { data: meal } = await apiClient.post("/api/v1/custom-meals", {
        name: name.trim(),
        ingredients,
      });

      await apiClient.post("/api/v1/logs/food", {
        custom_meal_id: meal.id,
        meal_type: mealType,
        log_source: "custom_meal",
      });

      return meal;
    },
    onSuccess: async (meal) => {
      setRecentMeals((current) => ({ ...current, [meal.id]: meal }));
      setBasket([]);
      setName("");
      setErrorMessage("");
      setSavedMessage(true);
      if (messageTimeoutRef.current) {
        window.clearTimeout(messageTimeoutRef.current);
      }
      messageTimeoutRef.current = window.setTimeout(() => {
        setSavedMessage(false);
      }, 3000);
      await queryClient.invalidateQueries({ queryKey: ["food-logs", "today"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard", "today"] });
    },
    onError: () => {
      setSavedMessage(false);
      setErrorMessage("Could not save this custom meal right now.");
    },
  });

  function addFoodToBasket(food) {
    setBasket((current) => [
      ...current,
      {
        id: `${food.id}-${crypto.randomUUID()}`,
        foodId: food.id,
        foodName: food.name,
        grams: 100,
      },
    ]);
    setErrorMessage("");
  }

  function updateBasketItem(itemId, grams) {
    setBasket((current) =>
      current.map((item) => (item.id === itemId ? { ...item, grams } : item)),
    );
  }

  function removeBasketItem(itemId) {
    setBasket((current) => current.filter((item) => item.id !== itemId));
  }

  async function handleSave() {
    if (!name.trim() || !basket.length || saveMeal.isPending) {
      return;
    }
    await saveMeal.mutateAsync();
  }

  return (
    <AppLayout title="Custom Meal" back>
      <div className="space-y-4">
        <Card className="space-y-3">
          <FoodSearch onSelect={addFoodToBasket} clearAfterSelect />
        </Card>

        <Card className="space-y-3">
          <h2 className="font-semibold text-gray-800">Basket</h2>
          {!basket.length ? <p className="text-sm text-gray-500">Select foods to build your custom meal.</p> : null}
          {basket.map((item) => (
            <div key={item.id} className="flex items-center gap-3">
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-gray-800">{item.foodName}</p>
              </div>
              <Input
                type="number"
                min="1"
                value={item.grams}
                onChange={(event) => updateBasketItem(item.id, event.target.value)}
                className="w-28"
              />
              <button
                type="button"
                className="rounded-full px-2 py-1 text-lg leading-none text-gray-500 transition hover:bg-gray-100 hover:text-gray-800"
                onClick={() => removeBasketItem(item.id)}
                aria-label={`Remove ${item.foodName}`}
              >
                ×
              </button>
            </div>
          ))}

          <div className="border-t border-gray-100 pt-3">
            <div className="space-y-3">
              <Input
                label="Meal name"
                value={name}
                onChange={(event) => {
                  setName(event.target.value);
                  setErrorMessage("");
                }}
                required
              />
              <Select
                label="Meal type"
                value={mealType}
                onChange={(event) => setMealType(event.target.value)}
                options={["breakfast", "lunch", "dinner", "snack"]}
              />
              <Button
                className="w-full"
                disabled={!basket.length || !name.trim()}
                loading={saveMeal.isPending}
                onClick={handleSave}
              >
                Save
              </Button>
            </div>
          </div>
        </Card>

        {savedMessage ? (
          <Card>
            <p className="text-sm font-medium text-teal-700">✓ Saved to meal log</p>
          </Card>
        ) : null}
        {errorMessage ? (
          <Card>
            <p className="text-sm font-medium text-rose-700">{errorMessage}</p>
          </Card>
        ) : null}

        <section className="space-y-2">
          <h2 className="font-semibold text-gray-800">Today&apos;s logs</h2>
          {!logs.data?.items?.length ? (
            <Card>
              <p className="text-sm text-gray-500">Saved custom meals will show up here in your meal log.</p>
            </Card>
          ) : null}
          {(logs.data?.items || []).map((log) => (
            <CustomMealLogItem
              key={log.id}
              log={log}
              customMeal={log.custom_meal_id ? customMealsById[log.custom_meal_id] : null}
            />
          ))}
        </section>
      </div>
    </AppLayout>
  );
}
