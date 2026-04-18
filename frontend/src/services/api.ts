import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

const api: AxiosInstance = axios.create({
  baseURL: 'http://localhost:8000/api/',
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor: attach Bearer token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle 401 → refresh token
let isRefreshing = false
let failedQueue: Array<{ resolve: (v: unknown) => void; reject: (e: unknown) => void }> = []

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest: AxiosRequestConfig & { _retry?: boolean } = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers = {
              ...originalRequest.headers,
              Authorization: `Bearer ${token}`,
            }
            return api(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const { data } = await axios.post('http://localhost:8000/api/auth/token/refresh/', {
          refresh: refreshToken,
        })
        const newAccess = data.access
        localStorage.setItem('access_token', newAccess)
        api.defaults.headers.common.Authorization = `Bearer ${newAccess}`
        processQueue(null, newAccess)
        originalRequest.headers = {
          ...originalRequest.headers,
          Authorization: `Bearer ${newAccess}`,
        }
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  },
)

// ─── Auth API ───────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login/', { email, password }),
  register: (data: Record<string, unknown>) =>
    api.post('/auth/register/', data),
  getProfile: () =>
    api.get('/auth/profile/'),
  updateProfile: (data: Record<string, unknown>) =>
    api.patch('/auth/profile/', data),
  changePassword: (data: Record<string, unknown>) =>
    api.post('/auth/change-password/', data),
  createStaff: (data: Record<string, unknown>) =>
    api.post('/auth/staff/', data),
  listStaff: () =>
    api.get('/auth/staff/'),
  updateStaff: (id: number | string, data: Record<string, unknown>) =>
    api.patch(`/auth/staff/${id}/`, data),
  deleteStaff: (id: number | string) =>
    api.delete(`/auth/staff/${id}/`),
}

// ─── Application API ─────────────────────────────────────────────────────────
export const applicationApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/applications/', { params }),
  get: (id: number | string) =>
    api.get(`/applications/${id}/`),
  create: (data: FormData | Record<string, unknown>) =>
    api.post('/applications/', data, {
      headers: data instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : {},
    }),
  update: (id: number | string, data: Record<string, unknown>) =>
    api.patch(`/applications/${id}/`, data),
  submit: (id: number | string) =>
    api.post(`/applications/${id}/submit/`),
  requestPayment: (id: number | string) =>
    api.post(`/applications/${id}/request-payment/`),
  withdraw: (id: number | string) =>
    api.post(`/applications/${id}/withdraw/`),
  committeeReview: (id: number | string, data: Record<string, unknown>) =>
    api.post(`/applications/${id}/committee-review/`, data),
  chairmanApproval: (id: number | string, data: Record<string, unknown>) =>
    api.post(`/applications/${id}/chairman-approval/`, data),
  issueCertificate: (id: number | string, formData: FormData) =>
    api.post(`/applications/${id}/issue-certificate/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  updateCompletion: (id: number | string, data: Record<string, unknown>) =>
    api.patch(`/applications/${id}/completion/`, data),
  renew: (id: number | string) =>
    api.post(`/applications/${id}/renew/`),
  resubmitDocuments: (id: number | string) =>
    api.post(`/applications/${id}/resubmit-documents/`),
  getHistory: (id: number | string) =>
    api.get(`/applications/${id}/history/`),
}

// ─── Document API ────────────────────────────────────────────────────────────
export const documentApi = {
  list: (applicationId: number | string) =>
    api.get('/documents/', { params: { application: applicationId } }),
  upload: (formData: FormData) =>
    api.post('/documents/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  delete: (id: number | string) =>
    api.delete(`/documents/${id}/`),
  verify: (id: number | string, data: Record<string, unknown>) =>
    api.post(`/documents/${id}/verify/`, data),
  reject: (id: number | string, data: Record<string, unknown>) =>
    api.post(`/documents/${id}/reject/`, data),
}

// ─── Payment API ─────────────────────────────────────────────────────────────
export const paymentApi = {
  listForApplication: (appId: number | string) =>
    api.get(`/payments/applications/${appId}/payments/`),
  getBreakdown: (stage: string, streetTypeId?: number | string) =>
    api.get('/payments/fees/breakdown/', { params: { stage, street_type: streetTypeId } }),
  submitPayment: (paymentId: number | string, data: FormData | Record<string, unknown>) =>
    api.post(`/payments/${paymentId}/submit/`, data, {
      headers:
        data instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : {},
    }),
  confirmPayment: (paymentId: number | string, data: Record<string, unknown>) =>
    api.post(`/payments/${paymentId}/confirm/`, data),
  listFeeConfig: () =>
    api.get('/payments/fees/config/'),
  createFeeConfig: (data: Record<string, unknown>) =>
    api.post('/payments/fees/config/', data),
  updateFeeConfig: (id: number | string, data: Record<string, unknown>) =>
    api.patch(`/payments/fees/config/${id}/`, data),
  deleteFeeConfig: (id: number | string) =>
    api.delete(`/payments/fees/config/${id}/`),
  getStats: () =>
    api.get('/payments/stats/'),
}

// ─── Notification API ────────────────────────────────────────────────────────
export const notificationApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/notifications/', { params }),
  markRead: (id: number | string) =>
    api.post(`/notifications/${id}/mark_read/`),
  markAllRead: () =>
    api.post('/notifications/mark_all_read/'),
  unreadCount: () =>
    api.get('/notifications/unread_count/'),
}

// ─── Config API ──────────────────────────────────────────────────────────────
export const configApi = {
  listStreetTypes: () =>
    api.get('/config/street-types/'),
  createStreetType: (data: Record<string, unknown>) =>
    api.post('/config/street-types/', data),
  updateStreetType: (id: number | string, data: Record<string, unknown>) =>
    api.patch(`/config/street-types/${id}/`, data),
  getBuildingSurveys: () =>
    api.get('/config/building-surveys/'),
  getRenewalSettings: () =>
    api.get('/config/renewal-settings/'),
  updateRenewalSettings: (data: Record<string, unknown>) =>
    api.patch('/config/renewal-settings/', data),
}

export default api
