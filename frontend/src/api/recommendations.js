import { apiClient } from "./client";

export async function getNextRecommendation(mealType) {
  const { data } = await apiClient.get("/api/v1/recommendations/next", {
    params: { meal_type: mealType },
  });
  return data;
}

export async function submitRecommendationFeedback(recommendationId, payload) {
  const { data } = await apiClient.post(`/api/v1/recommendations/${recommendationId}/feedback`, payload);
  return data;
}
