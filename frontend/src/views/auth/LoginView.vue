<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-700 to-blue-900 flex items-center justify-center px-4 py-12">
    <div class="w-full max-w-md">
      <!-- Header -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-white">SNRMS</h1>
        <p class="text-blue-200 mt-1">Street Names Registration & Management System</p>
        <p class="text-blue-300 text-sm mt-0.5">Ibeju-Lekki Local Government Area</p>
      </div>

      <!-- Card -->
      <div class="bg-white rounded-2xl shadow-2xl p-8">
        <h2 class="text-xl font-semibold text-gray-900 mb-6">Sign in to your account</h2>

        <!-- Error alert -->
        <div
          v-if="errorMessage"
          class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-start gap-2"
        >
          <ExclamationCircleIcon class="w-4 h-4 mt-0.5 flex-shrink-0" />
          {{ errorMessage }}
        </div>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label for="email" class="form-label">Email address</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              autocomplete="email"
              required
              class="form-input"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label for="password" class="form-label">Password</label>
            <div class="relative">
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                required
                class="form-input pr-10"
                placeholder="••••••••"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 px-3 text-gray-400 hover:text-gray-600"
                @click="showPassword = !showPassword"
              >
                <EyeIcon v-if="!showPassword" class="w-4 h-4" />
                <EyeSlashIcon v-else class="w-4 h-4" />
              </button>
            </div>
          </div>

          <button
            type="submit"
            :disabled="auth.loading"
            class="btn-primary w-full py-2.5 mt-2"
          >
            <span v-if="auth.loading" class="flex items-center gap-2">
              <svg class="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              Signing in...
            </span>
            <span v-else>Sign in</span>
          </button>
        </form>

        <p class="mt-6 text-center text-sm text-gray-600">
          Don't have an account?
          <RouterLink to="/register" class="text-blue-600 hover:text-blue-700 font-medium">
            Register here
          </RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { ExclamationCircleIcon, EyeIcon, EyeSlashIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { getRoleDefault } from '@/router/index'

const auth = useAuthStore()
const router = useRouter()

const form = ref({ email: '', password: '' })
const errorMessage = ref('')
const showPassword = ref(false)

async function handleLogin() {
  errorMessage.value = ''
  try {
    await auth.login(form.value.email, form.value.password)
    const redirect = (router.currentRoute.value.query.redirect as string) || getRoleDefault(auth.user?.role)
    router.push(redirect)
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string; non_field_errors?: string[] } } }
    errorMessage.value =
      e.response?.data?.detail ||
      e.response?.data?.non_field_errors?.[0] ||
      'Invalid email or password. Please try again.'
  }
}
</script>
