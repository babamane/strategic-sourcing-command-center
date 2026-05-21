import { useQuery } from "@tanstack/react-query";
import { getRenewal } from "../api/endpoints.js";

export function useRenewal(vendor) {
  return useQuery({
    queryKey: ["renewal", vendor],
    queryFn: () => getRenewal(vendor),
    staleTime: 60_000,
  });
}
