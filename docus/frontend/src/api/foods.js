import { apiClient } from "./client";

export async function searchFoods({ q = "", category = "", limit = 20, offset = 0 }) {
  const { data } = await apiClient.get("/api/v1/foods/search", {
    params: { q, category: category === "All" ? "" : category, limit, offset },
  });
  return data;
}

export async function getFoodCategories() {
  const { data } = await apiClient.get("/api/v1/foods/categories");
  return data;
}

export async function getFood(foodId) {
  const { data } = await apiClient.get(`/api/v1/foods/${foodId}`);
  return data;
}
