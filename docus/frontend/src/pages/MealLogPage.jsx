import { useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import AppLayout from "../components/layout/AppLayout.jsx";
import FoodLogItem from "../components/logs/FoodLogItem.jsx";
import FoodSearch from "../components/FoodSearch.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import Input from "../components/ui/Input.jsx";
import Select from "../components/ui/Select.jsx";
import { useState } from "react";
import { useFoodLogs } from "../hooks/useLogs.js";
import { number } from "../utils/formatters.js";

export default function MealLogPage() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState(null);
  const [portion, setPortion] = useState(100);
  const [mealType, setMealType] = useState("lunch");
  const { logs, create, remove } = useFoodLogs();

  async function logFood() {
    if (!selected) return;
    await create.mutateAsync({
      log_source: "manual_log",
      food_id: selected.id,
      portion_g: Number(portion),
      meal_type: mealType,
    });
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
          {selected.display_note && (
            <p className="text-sm text-gray-500">{selected.display_note}</p>
          )}
          <Input
            label="Portion size (grams)"
            type="number"
            value={portion}
            onChange={(e) => setPortion(e.target.value)}
          />
          <Select
            label="Meal type"
            value={mealType}
            onChange={(e) => setMealType(e.target.value)}
            options={["breakfast", "lunch", "dinner", "snack"]}
          />
          <p className="text-sm text-gray-600">
            At {portion}g: {number((selected.calories || 0) * portion / 100)} kcal,{" "}
            {number((selected.protein_g || 0) * portion / 100)}g protein
          </p>
          <Button className="w-full" loading={create.isPending} onClick={logFood}>
            Log this food
          </Button>
        </Card>
      )}

      <section className="space-y-2 mt-4">
        <h2 className="font-semibold text-gray-800">Today's logs</h2>
        {!logs.data?.items?.length ? (
          <Card>
            <p className="text-sm text-gray-500">Nothing logged yet today.</p>
          </Card>
        ) : null}
        {(logs.data?.items || []).map((log) => (
          <FoodLogItem key={log.id} log={log} onDelete={(id) => remove.mutate(id)} />
        ))}
      </section>
    </AppLayout>
  );
}
