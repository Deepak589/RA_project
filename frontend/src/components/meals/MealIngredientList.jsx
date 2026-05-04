export default function MealIngredientList({ ingredients = [] }) {
  if (!ingredients.length) return null;
  return (
    <ul className="space-y-2 text-sm text-gray-600">
      {ingredients.map((ingredient) => (
        <li key={`${ingredient.food_id}-${ingredient.portion_g}`} className="flex justify-between gap-3">
          <span>{ingredient.food_name || ingredient.name}</span>
          <span>{ingredient.portion_g}g</span>
        </li>
      ))}
    </ul>
  );
}
