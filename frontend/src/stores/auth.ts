import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '@/services/api'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  phone: string
  role: 'applicant' | 'finance' | 'naming_committee' | 'committee_chairman'
  is_active: boolean
  created_at: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const loading = ref(false)

  // ── Getters ────────────────────────────────────────────────────────────────
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const isApplicant = computed(() => user.value?.role === 'applicant')
  const isFinance = computed(() => user.value?.role === 'finance')
  const isNamingCommittee = computed(() => user.value?.role === 'naming_committee')
  const isChairman = computed(() => user.value?.role === 'committee_chairman')
  const isStaff = computed(() =>
    ['finance', 'naming_committee', 'committee_chairman'].includes(user.value?.role ?? ''),
  )

  // ── Actions ────────────────────────────────────────────────────────────────
  async function login(email: string, password: string) {
    loading.value = true
    try {
      const { data } = await authApi.login(email, password)
      accessToken.value = data.tokens.access
      refreshToken.value = data.tokens.refresh
      localStorage.setItem('access_token', data.tokens.access)
      localStorage.setItem('refresh_token', data.tokens.refresh)
      await fetchProfile()
    } finally {
      loading.value = false
    }
  }

  function logout() {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async function fetchProfile() {
    loading.value = true
    try {
      const { data } = await authApi.getProfile()
      user.value = data
    } finally {
      loading.value = false
    }
  }

  async function register(data: Record<string, unknown>) {
    loading.value = true
    try {
      const response = await authApi.register(data)
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(data: Record<string, unknown>) {
    const { data: updated } = await authApi.updateProfile(data)
    user.value = updated
    return updated
  }

  async function changePassword(data: Record<string, unknown>) {
    return authApi.changePassword(data)
  }

  return {
    user,
    accessToken,
    refreshToken,
    loading,
    isAuthenticated,
    isApplicant,
    isFinance,
    isNamingCommittee,
    isChairman,
    isStaff,
    login,
    logout,
    fetchProfile,
    register,
    updateProfile,
    changePassword,
  }
})
