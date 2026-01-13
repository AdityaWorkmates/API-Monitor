import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const getEndpoints = () => api.get('/endpoints/');
export const getEndpoint = (id) => api.get(`/endpoints/${id}`);
export const createEndpoint = (data) => api.post('/endpoints/', data);
export const updateEndpoint = (id, data) => api.put(`/endpoints/${id}`, data);
export const deleteEndpoint = (id) => api.delete(`/endpoints/${id}`);
export const getEndpointStats = (id) => api.get(`/stats/${id}`);
export const getEndpointLogs = (id) => api.get(`/logs/${id}`);

export default api;
