import axios from "axios";

export const api = axios.create({
  baseURL: "/api",
  timeout: 600_000,
});

api.interceptors.response.use(
  response => response,
  error => {
    console.error("[API]", error.response?.status, error.config?.url, error.message);
    return Promise.reject(error);
  },
);
