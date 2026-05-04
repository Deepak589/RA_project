import clsx from "clsx";
import { number } from "../../utils/formatters.js";

export default function NutritionSummary({ nutrition }) {
  if (!nutrition) return null;
  const stats = [
    ["Calories", `${number(nutrition.calories_consumed)} / 1800`, false],
    ["Protein", `${number(nutrition.protein_consumed)}g`, nutrition.is_protein_low],
    ["Fiber", `${number(nutrition.fiber_consumed)}g`, nutrition.is_fiber_low],
    ["Omega-3", `${number(nutrition.omega3_consumed, 1)}g`, nutrition.is_omega3_low],
    ["Sugar", nutrition.sugar_consumed ? `${number(nutrition.sugar_consumed)}g` : "tracked", nutrition.is_sugar_over],
  ];
  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      {stats.map(([label, value, alert]) => (
        <div key={label} className="min-w-28 rounded-xl border border-gray-100 bg-white p-3 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span className={clsx("h-2 w-2 rounded-full", alert ? "bg-orange-500" : "bg-teal-500")} />
            {label}
          </div>
          <div className={clsx("mt-1 font-semibold", alert ? "text-orange-800" : "text-gray-800")}>{value}</div>
        </div>
      ))}
    </div>
  );
}
