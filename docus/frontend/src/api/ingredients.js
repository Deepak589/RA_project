import { apiClient } from "./client";

export async function searchIngredient(ingredientName) {
  const { data } = await apiClient.post("/api/v1/ingredients/search", {
    ingredient_name: ingredientName,
  });
  return data;
}

export async function createMissingIngredient(payload) {
  const { data } = await apiClient.post("/api/v1/ingredients/missing", payload);
  return data;
}
