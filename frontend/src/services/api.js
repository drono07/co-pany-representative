import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth service
export const authService = {
  login: (email, password) => 
    api.post('/auth/login', { email, password }).then(res => res.data),
  
  register: (email, password, name) => 
    api.post('/auth/register', { email, password, name }).then(res => res.data),
  
  verifyToken: (token) => 
    api.get('/auth/me', { 
      headers: { Authorization: `Bearer ${token}` } 
    }).then(res => res.data),
};

// Application service
export const applicationService = {
  getApplications: () => 
    api.get('/applications').then(res => res.data),
  
  createApplication: (data) => 
    api.post('/applications', data).then(res => res.data),
  
  updateApplication: (id, data) => 
    api.put(`/applications/${id}`, data).then(res => res.data),
  
  partialUpdateApplication: (id, data) => 
    api.patch(`/applications/${id}`, data).then(res => res.data),
  
  deleteApplication: (id) => 
    api.delete(`/applications/${id}`).then(res => res.data),
  
  getApplication: (id) => 
    api.get(`/applications/${id}`).then(res => res.data),
};

// Analysis service
export const analysisService = {
  startAnalysis: (appId) => 
    api.post(`/applications/${appId}/runs`).then(res => res.data),
  
  getAnalysisRuns: (appId, limit = 10) => 
    api.get(`/applications/${appId}/runs?limit=${limit}`).then(res => res.data),
  
  getAllAnalysisRuns: (limit = 50) => 
    api.get(`/runs?limit=${limit}`).then(res => res.data),
  
  getAllRuns: (limit = 50) => 
    api.get('/dashboard').then(res => res.data.recent_runs || []),
  
  getAnalysisRun: (runId) => 
    api.get(`/runs/${runId}`).then(res => res.data),
  
  deleteAnalysisRun: (runId) => 
    api.delete(`/runs/${runId}`).then(res => res.data),
  
  getTaskStatus: (taskId) => 
    api.get(`/tasks/${taskId}/status`).then(res => res.data),
  
  // Content Analysis methods
  runContentAnalysis: (runId) => 
    api.post(`/runs/${runId}/content-analysis`).then(res => res.data),
  
  getContentAnalysisStatus: (runId, taskId) => 
    api.get(`/runs/${runId}/content-analysis/${taskId}`).then(res => res.data),
  
  getContentComparison: (runId, previousRunId) => 
    api.get(`/runs/${runId}/content-comparison/${previousRunId}`).then(res => res.data),
  
  // Enhanced link analysis methods
  getParentChildRelationships: (runId) => 
    api.get(`/runs/${runId}/parent-child-relationships`).then(res => res.data),
  
  getPageSourceCode: (runId, pageUrl) => 
    api.get(`/runs/${runId}/source-code?page_url=${encodeURIComponent(pageUrl)}`).then(res => res.data),
  
  getBrokenLinkDetails: (runId, brokenUrl) => 
    api.get(`/runs/${runId}/broken-links/details?broken_url=${encodeURIComponent(brokenUrl)}`).then(res => res.data),
};

// Schedule service
export const scheduleService = {
  createSchedule: (appId, data) => 
    api.post(`/applications/${appId}/schedules`, data).then(res => res.data),
  
  getSchedules: (appId) => 
    api.get(`/applications/${appId}/schedules`).then(res => res.data),
};

// Dashboard service
export const dashboardService = {
  getStats: () => 
    api.get('/dashboard').then(res => res.data),
  
  getWorkerStats: () => 
    api.get('/tasks/workers/stats').then(res => res.data),
};

// Health service
export const healthService = {
  checkHealth: () => 
    api.get('/health').then(res => res.data),
};

export default api;
