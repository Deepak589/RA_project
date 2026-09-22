import { apiClient } from "./client";

const AUTH = "/api/v1/auth";

export async function login(email, password) {
  const { data } = await apiClient.post(`${AUTH}/login`, { email, password });
  return data;
}

export async function register(email, password, name) {
  const { data } = await apiClient.post(`${AUTH}/register`, { email, password, name });
  return data;
}

export async function logout() {
  const { data } = await apiClient.post(`${AUTH}/logout`);
  return data;
}

export async function refreshToken() {
  const { data } = await apiClient.post(`${AUTH}/refresh`, {});
  return data;
}

export async function getMe() {
  const { data } = await apiClient.get(`${AUTH}/me`);
  return data;
}

export async function updateMe(payload) {
  const { data } = await apiClient.put(`${AUTH}/me`, payload);
  return data;
}

export async function changePassword(currentPassword, newPassword) {
  const { data } = await apiClient.post(`${AUTH}/change-password`, {
    current_password: currentPassword,
    new_password: newPassword,
  });
  return data;
}
