import { apiClient } from "./client";

export async function getTodayDashboard(dietOverride, mealType) {
  const params = {};
  if (dietOverride) params.diet_override = dietOverride;
  if (mealType) params.meal_type = mealType;
  const { data } = await apiClient.get("/api/v1/dashboard/today", { params: Object.keys(params).length ? params : undefined });
  return data;
}

export async function getWeeklyDashboard(weekOffset = 0) {
  const params = weekOffset !== 0 ? { week_offset: weekOffset } : undefined;
  const { data } = await apiClient.get("/api/v1/dashboard/weekly", { params });
  return data;
}
