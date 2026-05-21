import { useQuery } from "@tanstack/react-query";
import { getActiveDemandSeries, getForecast } from "../api/endpoints.js";

export function useForecast(vendor, department, months = 12) {
  return useQuery({
    queryKey: ["forecast", vendor, department, months],
    queryFn: () => getForecast(vendor, department, months),
    staleTime: 60_000,
  });
}

export function useActiveDemandSeries(vendor) {
  return useQuery({
    queryKey: ["active-demand-series", vendor],
    queryFn: () => getActiveDemandSeries(vendor),
    staleTime: 60_000,
  });
}
