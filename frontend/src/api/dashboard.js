import { apiClient } from "./client";

export async function getTodayDashboard() {
  const { data } = await apiClient.get("/api/v1/dashboard/today");
  return data;
}

export async function getWeeklyDashboard() {
  const { data } = await apiClient.get("/api/v1/dashboard/weekly");
  return data;
}
