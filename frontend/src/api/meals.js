import { apiClient } from "./client";

export async function calculateCustomMeal(payload) {
  const { data } = await apiClient.post("/api/v1/meals/custom/calculate", payload);
  return data;
}

export async function createCustomMeal(payload) {
  const { data } = await apiClient.post("/api/v1/meals/custom", payload);
  return data;
}

export async function getCustomMeals(params = {}) {
  const { data } = await apiClient.get("/api/v1/meals/custom", { params });
  return data;
}

export async function getMealById(mealId) {
  const { data } = await apiClient.get(`/api/v1/meals/${mealId}`);
  return data;
}
