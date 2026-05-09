import { apiClient } from "./client";

export async function getTodayDashboard(dietOverride) {
  const params = dietOverride ? { diet_override: dietOverride } : undefined;
  const { data } = await apiClient.get("/api/v1/dashboard/today", { params });
  return data;
}

export async function getWeeklyDashboard() {
  const { data } = await apiClient.get("/api/v1/dashboard/weekly");
  return data;
}
