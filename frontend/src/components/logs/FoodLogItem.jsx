import { useQuery } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { getMealById } from "../../api/meals";
import Button from "../ui/Button.jsx";
import Card from "../ui/Card.jsx";
import { formatTime, number } from "../../utils/formatters.js";

export default function FoodLogItem({ log, onDelete }) {
  const mealId = log.meal_id || log.recommendation_meal_id;
  const { data: meal } = useQuery({
    queryKey: ["meals", mealId],
    queryFn: () => getMealById(mealId),
    enabled: !!mealId,
    staleTime: Infinity,
  });

  const displayName = log.custom_food_name || meal?.name || log.food?.name || "Food log";
  const ingredients = meal?.ingredients || [];

  return (
    <Card className="flex items-center justify-between gap-3">
      <div className="min-w-0">
        <h3 className="font-medium text-gray-800">{displayName}</h3>
        {ingredients.length > 0 && (
          <p className="text-sm text-gray-600 truncate">
            {ingredients.map((i) => `${i.food_name} ${Number(i.portion_g)}g`).join(" · ")}
          </p>
        )}
        <p className="text-sm text-gray-500">
          {log.meal_type} · {formatTime(log.logged_at)}
        </p>
        <p className="text-sm text-gray-600">{number(log.display_calories)} kcal · {number(log.display_protein_g)}g protein</p>
      </div>
      {onDelete && (
        <Button variant="ghost" onClick={() => onDelete(log.id)} aria-label="Delete food log">
          <Trash2 className="h-4 w-4" />
        </Button>
      )}
    </Card>
  );
}
