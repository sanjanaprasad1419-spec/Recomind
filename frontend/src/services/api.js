import axios from 'axios';

// Base Axios instance configured for Django REST Framework integration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor placeholder
api.interceptors.request.use(
  (config) => {
    // Add auth headers or dynamic config here in the future
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor placeholder
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle central errors here
    return Promise.reject(error);
  }
);

export default api;
