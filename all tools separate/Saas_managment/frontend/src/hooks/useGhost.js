import { useQuery } from "@tanstack/react-query";
import { getGhostDetail, getGhostSummary } from "../api/endpoints.js";

export function useGhostSummary(vendor, department) {
  return useQuery({
    queryKey: ["ghost", "summary", vendor, department],
    queryFn: () => getGhostSummary(vendor, department),
    staleTime: 60_000,
  });
}

export function useGhostDetail(vendor, department) {
  return useQuery({
    queryKey: ["ghost", "detail", vendor, department],
    queryFn: () => getGhostDetail(vendor, department),
    staleTime: 60_000,
  });
}
