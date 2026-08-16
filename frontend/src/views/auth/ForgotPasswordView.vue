<template>
  <div class="min-h-screen flex items-center justify-center px-4" style="background:#0a1628">
    <div class="w-full max-w-md">
      <div class="bg-white rounded-3xl px-6 py-8" style="box-shadow:0 20px 60px rgba(0,0,0,0.35)">
        <h1 class="text-slate-900 text-xl font-bold tracking-tight">Reset your password</h1>
        <p class="text-slate-500 text-sm mt-1 mb-5">
          {{ step === 'request'
            ? "Enter your account email and we'll send you a reset code."
            : 'Enter the 6-digit code we emailed you and choose a new password.' }}
        </p>

        <!-- Alerts -->
        <div v-if="errorMessage" class="mb-4 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-3.5">
          <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/></svg>
          <p class="text-sm text-red-700">{{ errorMessage }}</p>
        </div>
        <div v-if="infoMessage" class="mb-4 rounded-xl border border-emerald-100 bg-emerald-50 p-3.5">
          <p class="text-sm text-emerald-700">{{ infoMessage }}</p>
        </div>

        <!-- Success state -->
        <div v-if="done" class="text-center py-4">
          <div class="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-3">
            <svg class="w-6 h-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5"/></svg>
          </div>
          <p class="text-sm font-semibold text-slate-800">Password reset</p>
          <p class="text-xs text-slate-500 mt-1 mb-4">Your password has been changed. You can now sign in with it.</p>
          <RouterLink to="/login" class="inline-flex items-center justify-center w-full py-3 rounded-xl text-sm font-semibold text-white" style="background:linear-gradient(135deg,#059669,#047857)">Back to sign in</RouterLink>
        </div>

        <!-- Step 1: request code -->
        <form v-else-if="step === 'request'" @submit.prevent="handleRequest" class="space-y-4" novalidate>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">Email address</label>
            <input v-model="email" type="email" autocomplete="email" required placeholder="you@example.com"
                   class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white" />
          </div>
          <button type="submit" :disabled="loading || !email"
                  class="w-full py-3.5 rounded-xl text-sm font-semibold text-white disabled:opacity-60"
                  style="background:linear-gradient(135deg,#059669,#047857)">
            {{ loading ? 'Sending…' : 'Send reset code' }}
          </button>
        </form>

        <!-- Step 2: confirm -->
        <form v-else @submit.prevent="handleConfirm" class="space-y-4" novalidate>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">Reset code</label>
            <input v-model="code" inputmode="numeric" maxlength="6" required placeholder="______"
                   class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-center tracking-[0.4em] text-lg font-semibold focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white" />
          </div>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">New password</label>
            <input v-model="newPassword" type="password" autocomplete="new-password" required placeholder="At least 8 characters"
                   class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white" />
          </div>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">Confirm new password</label>
            <input v-model="confirmPassword" type="password" autocomplete="new-password" required placeholder="Re-enter password"
                   class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white" />
          </div>
          <button type="submit" :disabled="loading || code.length < 6 || newPassword.length < 8 || newPassword !== confirmPassword"
                  class="w-full py-3.5 rounded-xl text-sm font-semibold text-white disabled:opacity-60"
                  style="background:linear-gradient(135deg,#059669,#047857)">
            {{ loading ? 'Resetting…' : 'Reset password' }}
          </button>
          <div class="flex justify-between text-xs">
            <button type="button" @click="step = 'request'; errorMessage = ''" class="text-slate-400 hover:text-slate-600">← Change email</button>
            <button type="button" @click="handleRequest" :disabled="loading" class="text-emerald-600 hover:text-emerald-700 font-semibold">Resend code</button>
          </div>
        </form>

        <div v-if="!done" class="mt-5 text-center">
          <RouterLink to="/login" class="text-xs font-semibold text-slate-500 hover:text-slate-700">Back to sign in</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { authApi } from '@/services/api'

const step = ref<'request' | 'confirm'>('request')
const email = ref('')
const code = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const errorMessage = ref('')
const infoMessage = ref('')
const done = ref(false)

async function handleRequest() {
  if (!email.value) return
  errorMessage.value = ''
  infoMessage.value = ''
  loading.value = true
  try {
    await authApi.requestPasswordReset(email.value.trim())
    step.value = 'confirm'
    code.value = ''
    infoMessage.value = 'If an account with that email exists, a 6-digit reset code has been sent. Check your inbox (and spam).'
  } catch {
    errorMessage.value = 'Could not send the reset code. Please try again.'
  } finally {
    loading.value = false
  }
}

async function handleConfirm() {
  errorMessage.value = ''
  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = 'The passwords do not match.'
    return
  }
  loading.value = true
  try {
    await authApi.confirmPasswordReset(email.value.trim(), code.value.trim(), newPassword.value)
    done.value = true
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    errorMessage.value = e.response?.data?.detail || 'Could not reset your password. Check the code and try again.'
    code.value = ''
  } finally {
    loading.value = false
  }
}
</script>
