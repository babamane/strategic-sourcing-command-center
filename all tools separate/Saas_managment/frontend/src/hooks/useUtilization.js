import { useQuery } from "@tanstack/react-query";
import { getUtilization } from "../api/endpoints.js";

export function useUtilization(vendor) {
  return useQuery({
    queryKey: ["utilization", vendor],
    queryFn: () => getUtilization(vendor),
    staleTime: 60_000,
  });
}
