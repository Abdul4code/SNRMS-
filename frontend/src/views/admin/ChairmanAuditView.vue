<template>
  <div class="min-h-screen" style="background:#f1f5f9">
    <div style="background:#0f172a">
      <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Local Government Chairman</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">Audit &amp; Reports</h1>
        <p class="text-slate-400 text-sm mt-1">Applications and revenue within a period.</p>
      </div>
    </div>

    <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <div class="rounded-2xl bg-white border border-slate-200 p-5 flex flex-wrap items-end gap-4">
        <div>
          <label class="block text-xs font-semibold text-slate-600 mb-1">From</label>
          <input v-model="from" type="date" class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-600 mb-1">To</label>
          <input v-model="to" type="date" class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm" />
        </div>
        <button @click="run" :disabled="loading" class="rounded-lg px-4 py-2 text-sm font-semibold text-white disabled:opacity-60" style="background:#059669">
          {{ loading ? 'Running…' : 'Run report' }}
        </button>
        <button @click="downloadReport" :disabled="downloading" class="rounded-lg px-4 py-2 text-sm font-semibold disabled:opacity-60" style="background:#0f172a;color:#fff">
          {{ downloading ? 'Preparing…' : 'Download PDF' }}
        </button>
        <div class="flex gap-2 ml-auto">
          <button @click="preset('month')" class="text-xs text-slate-500 hover:text-slate-700 underline">This month</button>
          <button @click="preset('year')" class="text-xs text-slate-500 hover:text-slate-700 underline">This year</button>
        </div>
      </div>

      <div v-if="data" class="space-y-6">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="rounded-2xl bg-white border border-slate-200 p-5">
            <p class="text-3xl font-bold text-slate-900">{{ data.total_applications }}</p>
            <p class="text-xs text-slate-500 mt-1 font-semibold uppercase tracking-wide">Applications</p>
          </div>
          <div class="rounded-2xl bg-white border border-slate-200 p-5">
            <p class="text-3xl font-bold" style="color:#059669">{{ data.certificates_issued }}</p>
            <p class="text-xs text-slate-500 mt-1 font-semibold uppercase tracking-wide">Certificates issued</p>
          </div>
          <div class="rounded-2xl bg-white border border-slate-200 p-5">
            <p class="text-3xl font-bold text-slate-900">{{ data.payments_confirmed_count }}</p>
            <p class="text-xs text-slate-500 mt-1 font-semibold uppercase tracking-wide">Payments confirmed</p>
          </div>
          <div class="rounded-2xl bg-white border border-slate-200 p-5">
            <p class="text-2xl font-bold" style="color:#059669">₦{{ data.total_revenue.toLocaleString() }}</p>
            <p class="text-xs text-slate-500 mt-1 font-semibold uppercase tracking-wide">Total revenue</p>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="rounded-2xl bg-white border border-slate-200 p-5">
            <p class="text-sm font-bold text-slate-900 mb-3">Revenue by category</p>
            <div v-for="(v, k) in data.payments_by_category" :key="k" class="flex items-center justify-between py-2 border-b border-slate-50 last:border-0">
              <span class="text-sm text-slate-600">{{ STAGE_LABELS[k] || k }}</span>
              <span class="text-sm font-semibold text-slate-800">₦{{ v.total.toLocaleString() }} <span class="text-xs text-slate-400">({{ v.count }})</span></span>
            </div>
          </div>
          <div class="rounded-2xl bg-white border border-slate-200 p-5">
            <p class="text-sm font-bold text-slate-900 mb-3">Applications by status</p>
            <div v-for="(n, s) in data.applications_by_status" :key="s" class="flex items-center justify-between py-2 border-b border-slate-50 last:border-0">
              <span class="text-sm text-slate-600 capitalize">{{ String(s).replace(/_/g, ' ') }}</span>
              <span class="text-sm font-semibold text-slate-800">{{ n }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api, { applicationApi } from '@/services/api'

interface Cat { count: number; total: number }
interface Audit {
  total_applications: number; certificates_issued: number; payments_confirmed_count: number
  total_revenue: number; payments_by_category: Record<string, Cat>; applications_by_status: Record<string, number>
}
const STAGE_LABELS: Record<string, string> = { stage_a: 'Application Fee', stage_c: 'Certificate Fee', renewal: 'Renewal Fee' }
const from = ref('')
const to = ref('')
const data = ref<Audit | null>(null)
const loading = ref(false)
const downloading = ref(false)
async function downloadReport() {
  downloading.value = true
  try {
    const res = await api.get('/applications/audit/report/', { params: { from: from.value, to: to.value }, responseType: 'blob' })
    const url = URL.createObjectURL(res.data as Blob)
    const a = document.createElement('a'); a.href = url; a.download = `audit_${from.value}_${to.value}.pdf`; a.click()
    URL.revokeObjectURL(url)
  } catch { /* ignore */ } finally { downloading.value = false }
}

function iso(d: Date) { return d.toISOString().slice(0, 10) }
function preset(kind: 'month' | 'year') {
  const now = new Date()
  from.value = iso(new Date(now.getFullYear(), kind === 'year' ? 0 : now.getMonth(), 1))
  to.value = iso(now)
  run()
}
async function run() {
  loading.value = true
  try { data.value = (await applicationApi.audit({ from: from.value, to: to.value })).data }
  finally { loading.value = false }
}
onMounted(() => preset('month'))
</script>
