import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post('/auth/login', { email, password }),
  register: (email: string, password: string, fullName: string) =>
    apiClient.post('/auth/register', { email, password, full_name: fullName }),
  refreshToken: (refreshToken: string) =>
    apiClient.post('/auth/refresh', { refresh_token: refreshToken }),
  getMe: () => apiClient.get('/auth/me'),
}

// Studies API
export const studiesApi = {
  list: (params?: { page?: number; pageSize?: number; status?: string; search?: string }) =>
    apiClient.get('/studies', { params }),
  get: (id: string) => apiClient.get(`/studies/${id}`),
  create: (data: any) => apiClient.post('/studies', data),
  update: (id: string, data: any) => apiClient.patch(`/studies/${id}`, data),
  delete: (id: string) => apiClient.delete(`/studies/${id}`),
  start: (id: string) => apiClient.post(`/studies/${id}/start`),
  complete: (id: string) => apiClient.post(`/studies/${id}/complete`),
  addMember: (id: string, userId: string, role: string) =>
    apiClient.post(`/studies/${id}/members`, { user_id: userId, role }),
  removeMember: (id: string, userId: string) =>
    apiClient.delete(`/studies/${id}/members/${userId}`),
}

// Nodes API
export const nodesApi = {
  list: (studyId: string, params?: { page?: number; pageSize?: number }) =>
    apiClient.get(`/studies/${studyId}/nodes`, { params }),
  get: (id: string) => apiClient.get(`/nodes/${id}`),
  create: (studyId: string, data: any) =>
    apiClient.post(`/studies/${studyId}/nodes`, data),
  update: (id: string, data: any) => apiClient.patch(`/nodes/${id}`, data),
  delete: (id: string) => apiClient.delete(`/nodes/${id}`),
}

// Deviations API
export const deviationsApi = {
  list: (nodeId: string, params?: { page?: number; pageSize?: number; status?: string }) =>
    apiClient.get(`/nodes/${nodeId}/deviations`, { params }),
  get: (id: string) => apiClient.get(`/deviations/${id}`),
  create: (nodeId: string, data: any) =>
    apiClient.post(`/nodes/${nodeId}/deviations`, data),
  update: (id: string, data: any) =>
    apiClient.patch(`/deviations/${id}`, data),
  delete: (id: string) => apiClient.delete(`/deviations/${id}`),
  // Causes
  addCause: (deviationId: string, data: any) =>
    apiClient.post(`/deviations/${deviationId}/causes`, data),
  getCauses: (deviationId: string) =>
    apiClient.get(`/deviations/${deviationId}/causes`),
  // Consequences
  addConsequence: (deviationId: string, data: any) =>
    apiClient.post(`/deviations/${deviationId}/consequences`, data),
  getConsequences: (deviationId: string) =>
    apiClient.get(`/deviations/${deviationId}/consequences`),
  // Safeguards
  addSafeguard: (deviationId: string, data: any) =>
    apiClient.post(`/deviations/${deviationId}/safeguards`, data),
  getSafeguards: (deviationId: string) =>
    apiClient.get(`/deviations/${deviationId}/safeguards`),
}

// Actions/Recommendations API
export const actionsApi = {
  list: (params?: { studyId?: string; status?: string; priority?: string }) =>
    apiClient.get('/actions', { params }),
  get: (id: string) => apiClient.get(`/actions/${id}`),
  create: (data: any) => apiClient.post('/actions', data),
  update: (id: string, data: any) => apiClient.patch(`/actions/${id}`, data),
  verify: (id: string, data: any) => apiClient.post(`/actions/${id}/verify`, data),
  getHistory: (id: string) => apiClient.get(`/actions/${id}/history`),
  getOverdue: () => apiClient.get('/actions/overdue'),
  getSummary: (studyId: string) => apiClient.get(`/actions/study/${studyId}/summary`),
}

// Reports API
export const reportsApi = {
  generatePDF: (studyId: string, params?: { includeSafeguards?: boolean; includeActions?: boolean }) =>
    apiClient.post(`/reports/generate/${studyId}/pdf`, null, { params }),
  generateExcel: (studyId: string) =>
    apiClient.post(`/reports/generate/${studyId}/excel`),
  download: (documentId: string) =>
    apiClient.get(`/reports/download/${documentId}`, { responseType: 'blob' }),
}

// Risk Matrix API
export const riskMatrixApi = {
  list: (studyType?: string) => apiClient.get('/risk-matrices', { params: { study_type: studyType } }),
  get: (id: string) => apiClient.get(`/risk-matrices/${id}`),
  getDefault: () => apiClient.get('/risk-matrices/default'),
  calculateRisk: (severity: number, likelihood: string, matrixId?: string) =>
    apiClient.get('/risk-matrices/calculate', { params: { severity, likelihood, matrix_id: matrixId } }),
}

// Guideword Libraries API
export const guidewordsApi = {
  list: (studyType?: string) =>
    apiClient.get('/guideword-libraries', { params: { study_type: studyType } }),
  get: (id: string) => apiClient.get(`/guideword-libraries/${id}`),
  getGuidewords: (libraryId: string) =>
    apiClient.get(`/guideword-libraries/${libraryId}/guidewords`),
}

// LLM API
export const llmApi = {
  generateSuggestions: (deviationId: string, suggestionType: string, context?: string) =>
    apiClient.post(`/llm/suggest/${deviationId}`, null, {
      params: { suggestion_type: suggestionType, context },
    }),
  acceptSuggestion: (_deviationId: string, suggestionId: string) =>
    apiClient.post(`/llm/suggestions/${suggestionId}/accept`),
  rejectSuggestion: (_deviationId: string, suggestionId: string) =>
    apiClient.post(`/llm/suggestions/${suggestionId}/reject`),
}

// Knowledge Base API
export const knowledgeApi = {
  search: (query: string, params?: { studyId?: string; limit?: number }) =>
    apiClient.post('/knowledge/search', { query, ...params }),
  ingestDocument: (documentId: string) =>
    apiClient.post(`/knowledge/ingest/${documentId}`),
}

// Users API
export const usersApi = {
  list: (params?: { page?: number; pageSize?: number; search?: string }) =>
    apiClient.get('/users', { params }),
  get: (id: string) => apiClient.get(`/users/${id}`),
  update: (id: string, data: any) => apiClient.patch(`/users/${id}`, data),
}