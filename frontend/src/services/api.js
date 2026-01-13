import axios from "axios";
import { API_BASE_URL } from "../constants/api";

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add a request interceptor to include the JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const authAPI = {
  login: (data) => api.post("/auth/login", data),
  register: (data) => api.post("/auth/register", data),
};

export const endpointAPI = {
  list: () => api.get("/endpoints/"),
  create: (data) => api.post("/endpoints/", data),
  get: (id) => api.get(`/endpoints/${id}`),
  update: (id, data) => api.put(`/endpoints/${id}`, data),
  delete: (id) => api.delete(`/endpoints/${id}`),
  getStats: (id) => api.get(`/stats/${id}`),
  getLogs: (id) => api.get(`/logs/${id}`),
};

export default api;
