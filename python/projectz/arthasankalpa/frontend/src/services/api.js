/**
 * api.js - Axios REST client.
 * All requests proxy through Vite to http://127.0.0.1:8000
 */
import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail || err.message || "Network error";
    return Promise.reject(new Error(msg));
  }
);

export const profileApi = {
  create:      (data)   => api.post("/profile", data),
  get:         (userId) => api.get(`/profile/${userId}`),
  analyzeRisk: (userId) => api.post(`/profile/${userId}/risk-analysis`),
};

export const fundsApi = {
  search:          (params)       => api.get("/funds/search", { params }),
  compare:         (schemeCodes)  => api.post("/funds/compare", schemeCodes),
  recommendations: (userId, topN) => api.get(`/funds/recommendations/${userId}`, { params: { top_n: topN || 10 } }),
};

export const budgetApi = {
  analyze: (data) => api.post("/budget/analyze", data),
};

export default api;