import axios from "axios";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  withCredentials: true,
});

let getToken = () => null;
let refreshAuth = null;
let logoutAuth = null;
let refreshPromise = null;

export function configureApiToken(getTokenFn) {
  getToken = typeof getTokenFn === "function" ? getTokenFn : () => null;
}

export function configureApiAuth(refreshFn, logoutFn) {
  refreshAuth = refreshFn || null;
  logoutAuth = logoutFn || null;
}

apiClient.interceptors.request.use((config) => {
  const accessToken = getToken();
  if (accessToken) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const isRefreshRequest = original?.url?.includes("/auth/refresh");
    const isLogoutRequest = original?.url?.includes("/auth/logout");
    if (error.response?.status === 401 && !original?._retried && !isRefreshRequest && !isLogoutRequest && refreshAuth) {
      original._retried = true;
      try {
        if (!refreshPromise) {
          refreshPromise = Promise.resolve(refreshAuth()).finally(() => {
            refreshPromise = null;
          });
        }
        await refreshPromise;
        const accessToken = getToken();
        if (accessToken) {
          original.headers = original.headers || {};
          original.headers.Authorization = `Bearer ${accessToken}`;
          return apiClient(original);
        }
      } catch {
        if (logoutAuth) {
          await logoutAuth();
        }
      }
    }
    if (error.response?.status === 401 && logoutAuth && !isRefreshRequest && !isLogoutRequest) {
      await logoutAuth();
    }
    return Promise.reject(error);
  },
);
