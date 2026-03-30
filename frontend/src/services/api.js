import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (username, password) => api.post('/auth/login', { username, password }),
  getMe: () => api.get('/auth/me'),
}

// Documents API
export const documentsAPI = {
  upload: (formData) => api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  list: (skip = 0, limit = 20) => api.get('/documents', { params: { skip, limit } }),
  get: (id) => api.get(`/documents/${id}`),
  delete: (id) => api.delete(`/documents/${id}`),
}

// Chat API
export const chatAPI = {
  createSession: (sessionName) => api.post('/chat/sessions', { session_name: sessionName }),
  listSessions: (skip = 0, limit = 20) => api.get('/chat/sessions', { params: { skip, limit } }),
  getSession: (sessionId) => api.get(`/chat/sessions/${sessionId}`),
  deleteSession: (sessionId) => api.delete(`/chat/sessions/${sessionId}`),
  query: (query) => api.post('/chat/query', query),
  queryStream: (query) => api.post('/chat/query-stream', query),
}

// Admin API
export const adminAPI = {
  listUsers: (skip = 0, limit = 50) => api.get('/admin/users', { params: { skip, limit } }),
  updateUserRole: (userId, role) => api.put(`/admin/users/${userId}/role`, { role }),
  getStats: () => api.get('/admin/stats'),
  clearCache: () => api.post('/admin/cache/clear'),
}

// Agent API
export const agentAPI = {
  listActions: () => api.get('/agents/actions'),
  executeAction: (actionName, parameters) => api.post(`/agents/actions/${actionName}`, parameters),
}

export default api
