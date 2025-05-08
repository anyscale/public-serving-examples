import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

// Base API URL - using relative path so it works when served from Ray Serve
const API_BASE_URL = '/api/v1';

/**
 * Creates a configured axios instance for API requests
 * @param token Optional auth token
 * @returns Axios instance
 */
export const createApiClient = (token?: string | null): AxiosInstance => {
  const config: AxiosRequestConfig = {
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  if (token) {
    config.headers = {
      ...config.headers,
      Authorization: `Bearer ${token}`,
    };
  }

  const instance = axios.create(config);

  // Add request interceptor for logging or modifying requests
  instance.interceptors.request.use(
    (config) => {
      // You could add logging here
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Add response interceptor for handling errors globally
  instance.interceptors.response.use(
    (response) => {
      return response;
    },
    (error) => {
      // Handle common errors here (such as 401 Unauthorized)
      if (error.response && error.response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
      
      return Promise.reject(error);
    }
  );

  return instance;
};

/**
 * API Client for making NLP-related requests
 */
export const nlpApi = {
  // Sentiment Analysis
  analyzeSentiment: (client: AxiosInstance, text: string, language: string = 'en') => 
    client.post('/sentiment', { text, language }),
  
  // Entity Recognition
  recognizeEntities: (client: AxiosInstance, text: string, minConfidence: number = 0.5) => 
    client.post('/entities', { text, min_confidence: minConfidence }),
  
  // Text Classification
  classifyText: (client: AxiosInstance, text: string, labels: string[]) => 
    client.post('/classify', { text, labels }),
  
  // Health Check
  checkHealth: (client: AxiosInstance) => 
    client.get('/health'),
  
  // Get classification presets (if available)
  getClassificationPresets: (client: AxiosInstance, presetName?: string) => 
    client.get(`/classify/presets${presetName ? `/${presetName}` : ''}`),
  
  // Authentication
  authenticate: (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    return axios.post(`${API_BASE_URL}/token`, formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  
  // Get user profile
  getUserProfile: (client: AxiosInstance) => 
    client.get('/users/me'),
};

export default nlpApi; 