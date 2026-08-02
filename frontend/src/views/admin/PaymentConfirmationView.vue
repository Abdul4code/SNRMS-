<template>
  <div class="min-h-screen" style="background:#f1f5f9">
    <div style="background:#0f172a">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Council Treasurer</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">Confirm Payments</h1>
        <p class="text-slate-400 text-sm mt-1">Online payments awaiting your confirmation. Confirming issues the receipt and advances the application.</p>
      </div>
    </div>

    <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      <div class="rounded-2xl bg-white border border-slate-200">
        <div class="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
          <p class="text-sm font-bold text-slate-900">Awaiting confirmation ({{ rows.length }})</p>
          <button @click="load" class="text-xs font-semibold text-emerald-600 hover:text-emerald-700">Refresh</button>
        </div>
        <div v-if="loading" class="py-12 text-center text-sm text-slate-400">Loading…</div>
        <div v-else-if="rows.length === 0" class="py-12 text-center text-sm text-slate-400">No payments awaiting confirmation.</div>
        <ul v-else class="divide-y divide-slate-50">
          <li v-for="p in rows" :key="p.id" class="px-5 py-4 flex flex-wrap items-center gap-4">
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold text-slate-900">{{ p.street_name }}
                <span class="text-xs font-normal text-slate-400 ml-1">{{ STAGE_LABELS[p.stage] || p.stage }}</span></p>
              <p class="text-xs text-slate-500">{{ p.applicant_name }} · {{ p.applicant_email }}</p>
              <p class="text-[11px] font-mono text-slate-400 mt-0.5">{{ p.reference }}</p>
            </div>
            <div class="text-right">
              <p class="text-sm font-bold text-slate-900">₦{{ p.amount.toLocaleString() }}</p>
              <p class="text-[11px] text-slate-400">{{ formatDate(p.submitted_at) }}</p>
            </div>
            <div class="flex items-center gap-2">
              <button @click="confirm(p, 'confirmed')" :disabled="busyId === p.id"
                      class="rounded-lg px-3 py-2 text-xs font-semibold text-white disabled:opacity-60" style="background:#059669">
                {{ busyId === p.id ? '…' : 'Confirm' }}
              </button>
              <button @click="confirm(p, 'rejected')" :disabled="busyId === p.id"
                      class="rounded-lg px-3 py-2 text-xs font-semibold text-red-600 border border-red-200 hover:bg-red-50">
                Reject
              </button>
            </div>
          </li>
        </ul>
      </div>
      <p v-if="note" class="text-sm text-emerald-600 mt-3">{{ note }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { paymentApi } from '@/services/api'

interface Row {
  id: string; reference: string; stage: string; amount: number; submitted_at: string
  street_name: string; application_ref: string; applicant_name: string; applicant_email: string
}
const STAGE_LABELS: Record<string, string> = { stage_a: 'Application Fee', stage_c: 'Certificate Fee', renewal: 'Renewal Fee' }
const rows = ref<Row[]>([])
const loading = ref(true)
const busyId = ref('')
const note = ref('')

function formatDate(d: string) { return d ? new Date(d).toLocaleString() : '' }
async function load() {
  loading.value = true
  try { rows.value = (await paymentApi.pendingConfirmation()).data.results as Row[] }
  finally { loading.value = false }
}
async function confirm(p: Row, decision: 'confirmed' | 'rejected') {
  busyId.value = p.id; note.value = ''
  try {
    await paymentApi.confirm(p.id, { status: decision })
    note.value = decision === 'confirmed'
      ? `Payment ${p.reference} confirmed — receipt issued.`
      : `Payment ${p.reference} rejected.`
    await load()
  } catch { note.value = 'Action failed. Please retry.' }
  finally { busyId.value = '' }
}
onMounted(load)
</script>
