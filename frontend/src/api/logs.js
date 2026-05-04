import { apiClient } from "./client";

export async function createFoodLog(payload) {
  const { data } = await apiClient.post("/api/v1/logs/food", payload);
  return data;
}

export async function getTodayFoodLogs() {
  const { data } = await apiClient.get("/api/v1/logs/food/today");
  return data;
}

export async function deleteFoodLog(logId) {
  const { data } = await apiClient.delete(`/api/v1/logs/food/${logId}`);
  return data;
}

export async function createSymptomLog(payload) {
  const { data } = await apiClient.post("/api/v1/logs/symptoms", payload);
  return data;
}

export async function updateTodaySymptoms(payload) {
  const { data } = await apiClient.patch("/api/v1/logs/symptoms/today", payload);
  return data;
}

export async function getTodaySymptoms() {
  const { data } = await apiClient.get("/api/v1/logs/symptoms/today");
  return data;
}

export async function createLifestyleLog(payload) {
  const { data } = await apiClient.post("/api/v1/logs/lifestyle", payload);
  return data;
}

export async function getTodayLifestyle() {
  const { data } = await apiClient.get("/api/v1/logs/lifestyle/today");
  return data;
}
