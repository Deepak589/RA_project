import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createFoodLog,
  createLifestyleLog,
  createSymptomLog,
  deleteFoodLog,
  getTodayFoodLogs,
  getTodayLifestyle,
  getTodaySymptoms,
  updateTodaySymptoms,
} from "../api/logs";

export function useFoodLogs() {
  const queryClient = useQueryClient();
  return {
    logs: useQuery({ queryKey: ["food-logs", "today"], queryFn: getTodayFoodLogs }),
    create: useMutation({
      mutationFn: createFoodLog,
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["food-logs", "today"] });
        queryClient.invalidateQueries({ queryKey: ["dashboard", "today"] });
        queryClient.invalidateQueries({ queryKey: ["dashboard", "weekly"] });
      },
    }),
    remove: useMutation({
      mutationFn: deleteFoodLog,
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["food-logs", "today"] });
        queryClient.invalidateQueries({ queryKey: ["dashboard", "today"] });
        queryClient.invalidateQueries({ queryKey: ["dashboard", "weekly"] });
      },
    }),
  };
}

export function useSymptoms() {
  const queryClient = useQueryClient();
  return {
    today: useQuery({ queryKey: ["logs", "symptoms", "today"], queryFn: getTodaySymptoms }),
    save: useMutation({
      mutationFn: ({ hasExistingLog, payload }) => (hasExistingLog ? updateTodaySymptoms(payload) : createSymptomLog(payload)),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["logs", "symptoms", "today"] });
        queryClient.invalidateQueries({ queryKey: ["dashboard", "today"] });
        queryClient.invalidateQueries({ queryKey: ["dashboard", "weekly"] });
      },
    }),
  };
}

export function useLifestyle() {
  const queryClient = useQueryClient();
  return {
    today: useQuery({ queryKey: ["logs", "lifestyle", "today"], queryFn: getTodayLifestyle }),
    save: useMutation({
      mutationFn: createLifestyleLog,
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["logs", "lifestyle", "today"] });
        queryClient.invalidateQueries({ queryKey: ["dashboard", "today"] });
        queryClient.invalidateQueries({ queryKey: ["dashboard", "weekly"] });
      },
    }),
  };
}
