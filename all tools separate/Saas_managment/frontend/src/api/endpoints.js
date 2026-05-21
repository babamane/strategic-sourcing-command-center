import { api } from "./client.js";

export function buildParams(vendor, department) {
  const params = {};
  if (vendor && vendor !== "All") params.vendor = vendor;
  if (department && department !== "All") params.department = department;
  return params;
}

export const getHealth = () => api.get("/health").then(r => r.data);
export const refreshPipeline = () => api.post("/v1/pipeline/refresh").then(r => r.data);
export const getLastPipelineRun = () => api.get("/v1/pipeline/last-run").then(r => r.data);
export const getGhostSummary = (vendor, department) =>
  api.get("/ghost/summary", { params: buildParams(vendor, department) }).then(r => r.data);
export const getGhostDetail = (vendor, department) =>
  api.get("/ghost/detail", { params: buildParams(vendor, department) }).then(r => r.data);
export const getReclamation = (vendor, department, minScore = 0.3) =>
  api.get("/reclamation", { params: { ...buildParams(vendor, department), min_score: minScore } }).then(r => r.data);
export const getUtilization = vendor =>
  api.get("/utilization", { params: buildParams(vendor, null) }).then(r => r.data);
export const getRenewal = vendor =>
  api.get("/renewal-pressure", { params: buildParams(vendor, null) }).then(r => r.data);
export const getTrueUp = vendor =>
  api.get("/trueup/exposure", { params: buildParams(vendor, null) }).then(r => r.data);
export const getTrueUpBreakdown = (vendor, sku, seatType) => {
  const params = { ...buildParams(vendor, null) };
  if (sku && sku !== "All") params.sku = sku;
  if (seatType && seatType !== "All") params.seat_type = seatType;
  return api.get("/trueup/breakdown", { params }).then(r => r.data);
};
export const getForecast = (vendor, department, months = 12) =>
  api.get("/forecast/demand", { params: { ...buildParams(vendor, department), months } }).then(r => r.data);
export const getActiveDemandSeries = vendor =>
  api.get("/forecast/active-demand-series", { params: buildParams(vendor, null) }).then(r => r.data);
