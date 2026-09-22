import { useQuery } from "@tanstack/react-query";
import { getTodayDashboard, getWeeklyDashboard } from "../api/dashboard";

export function useTodayDashboard(dietOverride, mealType) {
  return useQuery({
    queryKey: ["dashboard", "today", dietOverride || null, mealType || null],
    queryFn: () => getTodayDashboard(dietOverride, mealType),
    refetchInterval: 300_000,
  });
}

export function useWeeklyDashboard() {
  return useQuery({ queryKey: ["dashboard", "weekly"], queryFn: getWeeklyDashboard });
}
