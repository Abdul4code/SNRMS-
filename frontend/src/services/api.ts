import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/',
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
        const { data } = await axios.post(
          (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/') + 'auth/token/refresh/', {
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
  requestVerification: (email: string) => api.post('/auth/request-verification/', { email }),
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
  repository: (id: number | string) => api.get(`/applications/${id}/repository/`),
  releaseCertificate: (id: number | string, released: boolean) => api.post(`/applications/${id}/certificate-release/`, { released }),
  list: (params?: Record<string, unknown>) =>
    api.get('/applications/', { params }),
  get: (id: number | string) =>
    api.get(`/applications/${id}/`),
  create: (data: FormData | Record<string, unknown>) =>
    api.post('/applications/', data, {
      headers: data instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : {},
    }),
  checkDuplicate: (data: Record<string, unknown>) =>
    api.post('/applications/check-duplicate/', data),
  streetAvailability: (lat: number | string, lng: number | string) =>
    api.get('/applications/street-availability/', { params: { lat, lng } }),
  getRegistry: (params?: Record<string, unknown>) =>
    api.get('/applications/registry/', { params }),
  audit: (params: Record<string, unknown>) => api.get('/applications/audit/', { params }),
  setRoyaltyExemption: (id: string, exempt: boolean) =>
    api.post(`/applications/${id}/royalty-exemption/`, { exempt }),
  setSignboard: (id: string, data: Record<string, unknown>) =>
    api.post(`/applications/${id}/signboard/`, data),
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
  adminUpload: (formData: FormData) =>
    api.post('/documents/admin-upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

// ─── Payment API ─────────────────────────────────────────────────────────────
export const paymentApi = {
  pendingConfirmation: () => api.get('/payments/pending-confirmation/'),
  confirm: (paymentId: string, data: Record<string, unknown>) =>
    api.post(`/payments/${paymentId}/confirm/`, data),
  listForApplication: (appId: number | string) =>
    api.get(`/payments/applications/${appId}/payments/`),
  getBreakdown: (stage: string, streetTypeId?: number | string) =>
    api.get('/payments/fees/breakdown/', { params: { stage, street_type: streetTypeId } }),
  submitPayment: (paymentId: number | string, data: FormData | Record<string, unknown>) =>
    api.post(`/payments/${paymentId}/submit/`, data, {
      headers:
        data instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : {},
    }),
  initializePayment: (paymentId: number | string, callbackUrl?: string) =>
    api.post(`/payments/${paymentId}/initialize/`, { callback_url: callbackUrl }),
  simulatePayment: (paymentId: number | string) =>
    api.post(`/payments/${paymentId}/simulate/`, {}),
  verifyPayment: (reference: string) =>
    api.get('/payments/verify/', { params: { reference } }),
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
  streetViewUrl: (lat: number, lng: number) => `${api.defaults.baseURL}/config/streetview/?lat=${lat}&lng=${lng}`,
  publicSettings: () => api.get('/config/public-settings/'),
  listStreetTypes: () =>
    api.get('/config/street-types/'),
  createStreetType: (data: Record<string, unknown>) =>
    api.post('/config/street-types/', data),
  updateStreetType: (id: number | string, data: Record<string, unknown>) =>
    api.patch(`/config/street-types/${id}/`, data),
  getBuildingSurveys: () =>
    api.get('/config/building-surveys/'),
  getStreets: (params?: Record<string, unknown>) =>
    api.get('/config/streets/', { params }),
  getStreetSummary: () =>
    api.get('/config/streets/summary/'),
  getLocalityWards: () =>
    api.get('/config/locality-wards/'),
  getStreetBuildings: (id: string) =>
    api.get(`/config/streets/${id}/buildings/`),
  mergeStreets: (targetId: string, sourceIds: string[]) =>
    api.post('/config/streets/merge/', { target_id: targetId, source_ids: sourceIds }),
  splitStreet: (id: string, name: string, buildingIds: number[], streetTypeId?: string) =>
    api.post(`/config/streets/${id}/split/`, { name, building_ids: buildingIds, street_type_id: streetTypeId }),
  updateStreet: (id: string, data: Record<string, unknown>) =>
    api.patch(`/config/streets/${id}/update/`, data),
  getRenewalSettings: () =>
    api.get('/config/renewal-settings/'),
  updateRenewalSettings: (data: Record<string, unknown>) =>
    api.patch('/config/renewal-settings/', data),
}

export default api

// Street Naming Committee (second-tier quorum workflow)
export const committeeApi = {
  members: () => api.get('/applications/committee/members/'),
  verifyMember: (number: number, pin: string) =>
    api.post('/applications/committee/verify-member/', { number, pin }),
  review: (appId: string, token: string) =>
    api.get(`/applications/committee/${appId}/review/`, { headers: { 'X-Committee-Member': token }, params: { member_token: token } }),
  markViewed: (appId: string, token: string) =>
    api.post(`/applications/committee/${appId}/mark-viewed/`, { member_token: token }, { headers: { 'X-Committee-Member': token } }),
  comment: (appId: string, token: string, data: Record<string, unknown>) =>
    api.post(`/applications/committee/${appId}/comment/`, { ...data, member_token: token }, { headers: { 'X-Committee-Member': token } }),
  forward: (appId: string, token: string, data: Record<string, unknown>) =>
    api.post(`/applications/committee/${appId}/forward/`, { ...data, member_token: token }, { headers: { 'X-Committee-Member': token } }),
}

// Secure receipts (#13)
export const receiptApi = {
  getSignature: () => api.get('/payments/signature/'),
  uploadSignature: (form: FormData) =>
    api.post('/payments/signature/', form, { headers: { 'Content-Type': 'multipart/form-data' } }),
  download: async (serial: string) => {
    const res = await api.get(`/payments/receipts/${serial}/download/`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data as Blob)
    const a = document.createElement('a'); a.href = url; a.download = `${serial}.pdf`; a.click()
    URL.revokeObjectURL(url)
  },
  verify: (serial: string, code: string) =>
    api.get(`/payments/receipts/verify/${serial}/`, { params: { code } }),
}
