import Badge from "../ui/Badge.jsx";
import Button from "../ui/Button.jsx";
import Card from "../ui/Card.jsx";
import { number } from "../../utils/formatters.js";

export default function MealCard({
  meal,
  explanation,
  onAccept,
  onSkip,
  compact = false,
  className = "",
  acceptLabel = "Accept",
  skipLabel = "Skip",
}) {
  if (!meal) return null;
  return (
    <Card className={`space-y-3 ${className}`.trim()}>
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-3">
          <h2 className="text-base font-semibold text-gray-800">{meal.name}</h2>
          <Badge label={`Score ${number(meal.anti_inflammatory_score, 1)}`} variant="teal" />
        </div>
        <div className="flex flex-wrap gap-2">
          {meal.meal_type && <Badge label={meal.meal_type} />}
          {meal.is_flare_friendly && <Badge label="flare friendly" variant="orange" />}
          {meal.is_vegetarian && <Badge label="vegetarian" variant="green" />}
        </div>
      </div>
      {meal.ingredients?.length > 0 && (
        <div className="flex flex-wrap gap-x-2 gap-y-1 pt-1">
          {meal.ingredients.map((i, idx) => (
            <span key={idx} className="text-sm text-gray-600">
              {i.food_name}{" "}<span className="font-medium text-gray-800">{Number(i.portion_g)}g</span>
              {idx < meal.ingredients.length - 1 && <span className="text-gray-300 ml-1.5">·</span>}
            </span>
          ))}
        </div>
      )}
      <div className="grid grid-cols-3 gap-2 text-sm">
        <Stat label="Calories" value={number(meal.total_calories || meal.calories)} />
        <Stat label="Protein" value={`${number(meal.total_protein_g || meal.protein_g)}g`} />
        <Stat label="Fiber" value={`${number(meal.total_fiber_g || meal.fiber_g)}g`} />
      </div>
      {!compact && explanation && <p className="text-sm italic leading-6 text-gray-500">{explanation}</p>}
      {!compact && (onAccept || onSkip) && (
        <div className="grid grid-cols-2 gap-2">
          {onAccept && <Button onClick={() => onAccept(meal)}>{acceptLabel}</Button>}
          {onSkip && <Button variant="ghost" onClick={() => onSkip(meal)}>{skipLabel}</Button>}
        </div>
      )}
    </Card>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-xl bg-teal-50 p-2">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="font-semibold text-gray-800">{value}</div>
    </div>
  );
}
