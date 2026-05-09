import { useQuery } from "@tanstack/react-query";
import { getTodayDashboard, getWeeklyDashboard } from "../api/dashboard";

export function useTodayDashboard(dietOverride) {
  return useQuery({
    queryKey: ["dashboard", "today", dietOverride || null],
    queryFn: () => getTodayDashboard(dietOverride),
    refetchInterval: 300_000,
  });
}

export function useWeeklyDashboard() {
  return useQuery({ queryKey: ["dashboard", "weekly"], queryFn: getWeeklyDashboard });
}
