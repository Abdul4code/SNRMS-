<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-700 to-blue-900 flex items-center justify-center px-4 py-12">
    <div class="w-full max-w-lg">
      <!-- Header -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-white">SNRMS</h1>
        <p class="text-blue-200 mt-1">Street Names Registration & Management System</p>
        <p class="text-blue-300 text-sm mt-0.5">Ibeju-Lekki Local Government Area</p>
      </div>

      <div class="bg-white rounded-2xl shadow-2xl p-8">
        <h2 class="text-xl font-semibold text-gray-900 mb-6">Create an account</h2>

        <!-- Error alert -->
        <div
          v-if="errorMessage"
          class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
        >
          {{ errorMessage }}
        </div>

        <!-- Success -->
        <div
          v-if="success"
          class="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700"
        >
          Account created! Redirecting...
        </div>

        <form @submit.prevent="handleRegister" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="form-label">First name</label>
              <input v-model="form.first_name" type="text" required class="form-input" placeholder="John" />
            </div>
            <div>
              <label class="form-label">Last name</label>
              <input v-model="form.last_name" type="text" required class="form-input" placeholder="Doe" />
            </div>
          </div>

          <div>
            <label class="form-label">Email address</label>
            <input v-model="form.email" type="email" required class="form-input" placeholder="you@example.com" />
          </div>

          <div>
            <label class="form-label">Phone number</label>
            <input v-model="form.phone" type="tel" class="form-input" placeholder="+234 800 000 0000" />
          </div>

          <div>
            <label class="form-label">Password</label>
            <div class="relative">
              <input
                v-model="form.password"
                :type="showPwd ? 'text' : 'password'"
                required
                minlength="8"
                class="form-input pr-10"
                placeholder="At least 8 characters"
              />
              <button type="button" class="absolute inset-y-0 right-0 px-3 text-gray-400" @click="showPwd = !showPwd">
                <EyeIcon v-if="!showPwd" class="w-4 h-4" />
                <EyeSlashIcon v-else class="w-4 h-4" />
              </button>
            </div>
          </div>

          <div>
            <label class="form-label">Confirm password</label>
            <input
              v-model="form.confirm_password"
              type="password"
              required
              class="form-input"
              placeholder="Repeat your password"
            />
            <p v-if="form.confirm_password && form.password !== form.confirm_password" class="mt-1 text-xs text-red-600">
              Passwords do not match
            </p>
          </div>

          <button
            type="submit"
            :disabled="auth.loading || form.password !== form.confirm_password"
            class="btn-primary w-full py-2.5 mt-2"
          >
            <span v-if="auth.loading">Creating account...</span>
            <span v-else>Create account</span>
          </button>
        </form>

        <p class="mt-6 text-center text-sm text-gray-600">
          Already have an account?
          <RouterLink to="/login" class="text-blue-600 hover:text-blue-700 font-medium">Sign in</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { EyeIcon, EyeSlashIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const form = ref({
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  password: '',
  confirm_password: '',
})
const errorMessage = ref('')
const success = ref(false)
const showPwd = ref(false)

async function handleRegister() {
  errorMessage.value = ''
  if (form.value.password !== form.value.confirm_password) return

  try {
    const { confirm_password: _, ...payload } = form.value
    await auth.register(payload)
    // Auto-login after register
    await auth.login(form.value.email, form.value.password)
    success.value = true
    router.push('/applications')
  } catch (err: unknown) {
    const e = err as { response?: { data?: Record<string, string[]> } }
    const data = e.response?.data
    if (data) {
      const messages = Object.entries(data)
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
        .join(' | ')
      errorMessage.value = messages
    } else {
      errorMessage.value = 'Registration failed. Please try again.'
    }
  }
}
</script>
