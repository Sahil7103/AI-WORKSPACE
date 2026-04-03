import axios from 'axios'

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').trim()

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

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

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (username, password) => api.post('/auth/login', { username, password }),
  getMe: () => api.get('/auth/me'),
}

export const documentsAPI = {
  upload: (formData, options = {}) =>
    api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      ...options,
    }),
  list: (skip = 0, limit = 20) => api.get('/documents', { params: { skip, limit } }),
  get: (id) => api.get(`/documents/${id}`),
  delete: (id) => api.delete(`/documents/${id}`),
}

export const chatAPI = {
  createSession: (sessionName) =>
    api.post('/chat/sessions', null, { params: { session_name: sessionName } }),
  listSessions: (skip = 0, limit = 20) =>
    api.get('/chat/sessions', { params: { skip, limit } }),
  getSession: (sessionId) => api.get(`/chat/sessions/${sessionId}`),
  deleteSession: (sessionId) => api.delete(`/chat/sessions/${sessionId}`),
  renameSession: (sessionId, newName) => 
    api.put(`/chat/sessions/${sessionId}/rename`, null, { params: { session_name: newName } }),
  query: (query) => api.post('/chat/query', query),
  queryStream: async (query, { onToken, onDone } = {}) => {
    const token = localStorage.getItem('auth_token')
    const response = await fetch(`${API_BASE_URL}/chat/query-stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(query),
    })

    if (response.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
      throw new Error('Unauthorized')
    }

    if (!response.ok || !response.body) {
      throw new Error('Streaming request failed')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullText = ''
    let donePayload = null

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop() || ''

      for (const eventBlock of events) {
        const dataLines = eventBlock
          .split('\n')
          .filter((line) => line.startsWith('data: '))

        for (const line of dataLines) {
          const payload = JSON.parse(line.slice(6))
          if (payload.token) {
            fullText += payload.token
            onToken?.(payload.token, fullText)
          }
          if (payload.done) {
            donePayload = payload
            onDone?.(payload, fullText)
          }
        }
      }
    }

    return {
      response: fullText.trim(),
      ...donePayload,
    }
  },
}

export const adminAPI = {
  listUsers: (skip = 0, limit = 50) => api.get('/admin/users', { params: { skip, limit } }),
  updateUserRole: (userId, role) =>
    api.put(`/admin/users/${userId}/role`, null, { params: { role } }),
  getStats: () => api.get('/admin/stats'),
  clearCache: () => api.post('/admin/cache/clear'),
}

export const agentAPI = {
  listActions: () => api.get('/agents/actions'),
  executeAction: (actionName, parameters) =>
    api.post(`/agents/actions/${actionName}`, parameters),
}

export default api
