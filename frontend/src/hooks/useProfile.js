import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { addMedication, getProfile, removeMedication, updatePreferences } from "../api/profile";

export function useProfile() {
  const queryClient = useQueryClient();
  return {
    profile: useQuery({ queryKey: ["profile"], queryFn: getProfile }),
    updatePreferences: useMutation({ mutationFn: updatePreferences, onSuccess: () => queryClient.invalidateQueries({ queryKey: ["profile"] }) }),
    addMedication: useMutation({ mutationFn: addMedication, onSuccess: () => queryClient.invalidateQueries({ queryKey: ["profile"] }) }),
    removeMedication: useMutation({ mutationFn: removeMedication, onSuccess: () => queryClient.invalidateQueries({ queryKey: ["profile"] }) }),
  };
}
