import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getNextRecommendation, submitRecommendationFeedback } from "../api/recommendations";

export function useRecommendation(mealType) {
  const queryClient = useQueryClient();
  const recommendation = useQuery({
    queryKey: ["recommendation", "next", mealType],
    queryFn: () => getNextRecommendation(mealType),
    enabled: Boolean(mealType),
  });
  const feedback = useMutation({
    mutationFn: ({ recommendationId, payload }) => submitRecommendationFeedback(recommendationId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendation", "next"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
  return { ...recommendation, feedback };
}
