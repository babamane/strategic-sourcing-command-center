import { useQuery } from "@tanstack/react-query";
import { getTrueUp, getTrueUpBreakdown } from "../api/endpoints.js";

export function useTrueUp(vendor) {
  return useQuery({
    queryKey: ["trueup", vendor],
    queryFn: () => getTrueUp(vendor),
    staleTime: 60_000,
  });
}

export function useTrueUpBreakdown(vendor, sku = "All", seatType = "All") {
  return useQuery({
    queryKey: ["trueup", "breakdown", vendor, sku, seatType],
    queryFn: () => getTrueUpBreakdown(vendor, sku, seatType),
    staleTime: 60_000,
  });
}
