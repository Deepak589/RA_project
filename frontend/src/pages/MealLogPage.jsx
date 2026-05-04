import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import AppLayout from "../components/layout/AppLayout.jsx";
import FoodLogItem from "../components/logs/FoodLogItem.jsx";
import FoodSearch from "../components/FoodSearch.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import Input from "../components/ui/Input.jsx";
import Select from "../components/ui/Select.jsx";
import { getCustomMeals } from "../api/meals";
import { useFoodLogs } from "../hooks/useLogs.js";
import { number } from "../utils/formatters.js";

export default function MealLogPage() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState(null);
  const [portion, setPortion] = useState(100);
  const [mealType, setMealType] = useState("lunch");
  const [loggingCustomId, setLoggingCustomId] = useState(null);
  const [showSavedMeals, setShowSavedMeals] = useState(true);
  const [loggedMealName, setLoggedMealName] = useState(null);
  const { logs, create, remove } = useFoodLogs();
  const customMeals = useQuery({ queryKey: ["custom-meals"], queryFn: getCustomMeals });

  async function logCustomMeal(meal) {
    setLoggingCustomId(meal.id);
    try {
      await create.mutateAsync({ log_source: "custom_meal", custom_meal_id: meal.id, meal_type: meal.meal_type || mealType, portion_g: 1 });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["food-logs", "today"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard", "today"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard", "weekly"] }),
      ]);
      setShowSavedMeals(false);
      setLoggedMealName(meal.name);
    } finally {
      setLoggingCustomId(null);
    }
  }

  async function logFood() {
    if (!selected) return;
    await create.mutateAsync({ log_source: "manual_log", food_id: selected.id, portion_g: Number(portion), meal_type: mealType });
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["food-logs", "today"] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard", "today"] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard", "weekly"] }),
    ]);
    setSelected(null);
    setPortion(100);
  }

  return (
    <AppLayout title="Log Meal">
      <div className="space-y-3">
        <FoodSearch onSelect={setSelected} />
        <Link to="/custom-meal">
          <Button className="w-full" variant="dashed">Build my own meal</Button>
        </Link>
      </div>
      {selected && (
        <Card className="sticky bottom-24 z-20 space-y-3 border-teal-100">
          <h2 className="font-semibold text-gray-800">{selected.name}</h2>
          {selected.display_note && <p className="text-sm text-gray-500">{selected.display_note}</p>}
          <Input label="Portion size (grams)" type="number" value={portion} onChange={(e) => setPortion(e.target.value)} />
          <Select label="Meal type" value={mealType} onChange={(e) => setMealType(e.target.value)} options={["breakfast", "lunch", "dinner", "snack"]} />
          <p className="text-sm text-gray-600">At {portion}g: {number((selected.calories || 0) * portion / 100)} kcal, {number((selected.protein_g || 0) * portion / 100)}g protein</p>
          <Button className="w-full" loading={create.isPending} onClick={logFood}>Log this food</Button>
        </Card>
      )}
      {loggedMealName ? (
        <Card className="space-y-2">
          <p className="text-sm font-medium text-teal-700">✓ {loggedMealName} logged</p>
          <Button variant="ghost" className="w-full" onClick={() => { setLoggedMealName(null); setShowSavedMeals(true); }}>+ Add another meal</Button>
        </Card>
      ) : showSavedMeals && customMeals.data?.items?.length > 0 ? (
        <section className="space-y-2">
          <h2 className="font-semibold text-gray-800">My saved meals</h2>
          {customMeals.data.items.map((meal) => (
            <Card key={meal.id} className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="font-medium truncate">{meal.name}</p>
                <p className="text-sm text-gray-500">{number(meal.total_calories || 0)} kcal · {number(meal.total_protein_g || 0)}g protein</p>
              </div>
              <Button size="sm" loading={loggingCustomId === meal.id} onClick={() => logCustomMeal(meal)}>Log this</Button>
            </Card>
          ))}
        </section>
      ) : null}
      <section className="space-y-2">
        <h2 className="font-semibold text-gray-800">Today&apos;s logs</h2>
        {!logs.data?.items?.length ? <Card><p className="text-sm text-gray-500">Your food logs for today will show up here right away.</p></Card> : null}
        {(logs.data?.items || []).map((log) => <FoodLogItem key={log.id} log={log} onDelete={(id) => remove.mutate(id)} />)}
      </section>
    </AppLayout>
  );
}
