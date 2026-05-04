import { useQuery } from "@tanstack/react-query";
import { getTodayDashboard, getWeeklyDashboard } from "../api/dashboard";

export function useTodayDashboard() {
  return useQuery({ queryKey: ["dashboard", "today"], queryFn: getTodayDashboard, refetchInterval: 300_000 });
}

export function useWeeklyDashboard() {
  return useQuery({ queryKey: ["dashboard", "weekly"], queryFn: getWeeklyDashboard });
}
