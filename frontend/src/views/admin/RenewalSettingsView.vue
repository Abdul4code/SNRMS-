<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-3xl mx-auto px-4 sm:px-6 py-6">
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1">Settings</p>
        <h1 class="text-white text-xl font-bold tracking-tight">Renewal Settings</h1>
        <p class="text-slate-400 text-sm mt-0.5">Configure how long a renewal extends a certificate's validity</p>
      </div>
    </div>

    <div class="max-w-3xl mx-auto px-4 sm:px-6 py-6 space-y-4">

      <transition enter-active-class="transition duration-200 ease-out"
                  enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
        <div v-if="errorMsg" class="flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 p-4">
          <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
          </svg>
          <p class="text-sm text-red-700">{{ errorMsg }}</p>
        </div>
      </transition>
      <transition enter-active-class="transition duration-200 ease-out"
                  enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
        <div v-if="successMsg" class="flex items-start gap-3 rounded-2xl border border-emerald-100 bg-emerald-50 p-4">
          <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/>
          </svg>
          <p class="text-sm text-emerald-700">{{ successMsg }}</p>
        </div>
      </transition>

      <div class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0">
        <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
          <h2 class="text-sm font-bold text-slate-900">Renewal Duration</h2>
          <p class="text-xs text-slate-500 mt-0.5">
            When finance confirms a renewal payment, this many years are added to the certificate's current expiry date.
          </p>
        </div>

        <div v-if="loading" class="flex items-center justify-center py-12">
          <div class="w-8 h-8 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
        </div>

        <form v-else @submit.prevent="handleSave" class="p-5 space-y-5">
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              Years per renewal <span class="text-red-500">*</span>
            </label>
            <div class="flex items-center gap-3">
              <input v-model.number="renewalYears" type="number" min="1" max="99" required
                     class="w-28 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-center font-bold focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all" />
              <span class="text-sm text-slate-500">year{{ renewalYears === 1 ? '' : 's' }}</span>
            </div>
            <p class="text-xs text-slate-400 mt-2">
              Example: if a certificate expires on 1 Jan 2030 and renewal is {{ renewalYears }} year{{ renewalYears === 1 ? '' : 's' }},
              the new expiry will be 1 Jan {{ 2030 + renewalYears }}.
            </p>
          </div>

          <div v-if="updatedAt" class="text-xs text-slate-400">
            Last updated: {{ formatDate(updatedAt) }}
          </div>

          <button type="submit" :disabled="saving"
                  class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60"
                  style="background: linear-gradient(135deg, #059669, #047857)">
            {{ saving ? 'Saving…' : 'Save Settings' }}
          </button>
        </form>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { configApi } from '@/services/api'

const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const renewalYears = ref(5)
const updatedAt = ref('')

async function load() {
  loading.value = true
  try {
    const { data } = await configApi.getRenewalSettings()
    renewalYears.value = data.renewal_years
    updatedAt.value = data.updated_at
  } catch {
    errorMsg.value = 'Failed to load renewal settings.'
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  errorMsg.value = ''
  successMsg.value = ''
  saving.value = true
  try {
    const { data } = await configApi.updateRenewalSettings({ renewal_years: renewalYears.value })
    renewalYears.value = data.renewal_years
    updatedAt.value = data.updated_at
    successMsg.value = `Renewal duration set to ${data.renewal_years} year${data.renewal_years === 1 ? '' : 's'}.`
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string; renewal_years?: string[] } } }
    errorMsg.value = e.response?.data?.detail || e.response?.data?.renewal_years?.[0] || 'Failed to save.'
  } finally {
    saving.value = false
  }
}

function formatDate(d: string) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-NG', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(load)
</script>
