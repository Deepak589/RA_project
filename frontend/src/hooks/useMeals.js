import { useMutation, useQueryClient } from "@tanstack/react-query";
import { calculateCustomMeal, createCustomMeal } from "../api/meals";

export function useCustomMealBuilder() {
  const queryClient = useQueryClient();
  return {
    calculate: useMutation({ mutationFn: calculateCustomMeal }),
    create: useMutation({ mutationFn: createCustomMeal, onSuccess: () => queryClient.invalidateQueries({ queryKey: ["custom-meals"] }) }),
  };
}
