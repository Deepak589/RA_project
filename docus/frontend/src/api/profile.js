import { apiClient } from "./client";

export async function getProfile() {
  const { data } = await apiClient.get("/api/v1/profile");
  return data;
}

export async function updatePreferences(payload) {
  const { data } = await apiClient.put("/api/v1/profile/preferences", payload);
  return data;
}

export async function addMedication(payload) {
  const { data } = await apiClient.post("/api/v1/profile/medications", payload);
  return data;
}

export async function removeMedication(id) {
  const { data } = await apiClient.delete(`/api/v1/profile/medications/${id}`);
  return data;
}
