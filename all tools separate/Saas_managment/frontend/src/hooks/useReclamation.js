import { useQuery } from "@tanstack/react-query";
import { getReclamation } from "../api/endpoints.js";

export function useReclamation(vendor, department, minScore = 0.3) {
  return useQuery({
    queryKey: ["reclamation", vendor, department, minScore],
    queryFn: () => getReclamation(vendor, department, minScore),
    staleTime: 60_000,
  });
}
