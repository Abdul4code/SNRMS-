<template>
  <div class="min-h-screen" style="background: #f1f5f9">
    <div style="background: #0f172a">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Administration</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">Applications Database</h1>
        <p class="text-slate-400 text-sm mt-1">All applications with applicant details and payment records.</p>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-4">
      <div class="flex flex-wrap items-center gap-3">
        <input v-model="search" @input="onSearch" type="text"
               placeholder="Search name, email, street or reference…"
               class="flex-1 min-w-[240px] rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" />
        <button @click="exportCsv" class="rounded-xl px-4 py-2.5 text-sm font-semibold text-white" style="background:#059669">
          Export CSV
        </button>
        <span class="text-xs text-slate-500">{{ rows.length }} record(s)</span>
      </div>

      <div class="rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <th class="px-4 py-3 font-semibold">Reference</th>
                <th class="px-4 py-3 font-semibold">Street</th>
                <th class="px-4 py-3 font-semibold">Applicant</th>
                <th class="px-4 py-3 font-semibold">Email</th>
                <th class="px-4 py-3 font-semibold">Phone</th>
                <th class="px-4 py-3 font-semibold">Locality</th>
                <th class="px-4 py-3 font-semibold">Status</th>
                <th class="px-4 py-3 font-semibold text-right">Paid (₦)</th>
                <th class="px-4 py-3 font-semibold">Payment IDs</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in rows" :key="r.id" class="border-t border-slate-50 hover:bg-slate-50">
                <td class="px-4 py-3 font-mono text-xs text-slate-500">{{ r.reference_number || '—' }}</td>
                <td class="px-4 py-3">
                  <span class="font-medium text-slate-800">{{ r.proposed_street_name }}</span>
                  <span class="text-xs text-slate-400 ml-1">{{ r.street_type }}</span>
                </td>
                <td class="px-4 py-3">
                  <RouterLink :to="`/staff/applications/${r.id}`"
                              class="font-medium text-emerald-600 hover:text-emerald-700 hover:underline">
                    {{ r.applicant_name || '—' }}
                  </RouterLink>
                </td>
                <td class="px-4 py-3 text-slate-600 text-xs">{{ r.applicant_email }}</td>
                <td class="px-4 py-3 text-slate-600 text-xs">{{ r.applicant_phone || '—' }}</td>
                <td class="px-4 py-3 text-slate-600 text-xs">{{ r.locality || '—' }}</td>
                <td class="px-4 py-3">
                  <span class="text-xs px-2 py-0.5 rounded"
                        :style="r.is_register_import
                          ? 'background:#fef3c7;color:#92400e'
                          : 'background:#f1f5f9;color:#475569'">
                    {{ r.status_display || r.status }}
                  </span>
                </td>
                <td class="px-4 py-3 text-right font-semibold text-slate-800">{{ r.total_paid.toLocaleString() }}</td>
                <td class="px-4 py-3">
                  <div v-for="(p, i) in r.payment_refs" :key="i" class="text-[11px] font-mono text-slate-500">
                    {{ p.reference || '—' }}
                    <span :style="p.status === 'confirmed' ? 'color:#059669' : 'color:#94a3b8'">({{ p.status }})</span>
                  </div>
                  <span v-if="!r.payment_refs.length" class="text-xs text-slate-400">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="loading" class="text-sm text-slate-400 text-center py-8">Loading…</p>
        <p v-else-if="rows.length === 0" class="text-sm text-slate-400 text-center py-8">No records found.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { applicationApi } from '@/services/api'

interface PayRef { stage: string; reference: string; status: string }
interface Row {
  id: string; reference_number: string; proposed_street_name: string; street_type: string
  status: string; status_display?: string; is_register_import?: boolean
  ward: string; locality: string
  applicant_name: string; applicant_email: string; applicant_phone: string
  total_paid: number; payment_refs: PayRef[]
}

const rows = ref<Row[]>([])
const loading = ref(true)
const search = ref('')
let timer: ReturnType<typeof setTimeout>

async function load() {
  loading.value = true
  try {
    const { data } = await applicationApi.getRegistry(search.value ? { search: search.value } : {})
    rows.value = data.results as Row[]
  } finally {
    loading.value = false
  }
}
function onSearch() { clearTimeout(timer); timer = setTimeout(load, 300) }

function exportCsv() {
  const head = ['Reference', 'Street', 'Type', 'Applicant', 'Email', 'Phone', 'Locality', 'Status', 'Paid', 'Payment IDs']
  const lines = rows.value.map(r => [
    r.reference_number, r.proposed_street_name, r.street_type, r.applicant_name,
    r.applicant_email, r.applicant_phone, r.locality, r.status_display || r.status, r.total_paid,
    r.payment_refs.map(p => `${p.reference}(${p.status})`).join(' | '),
  ].map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(','))
  const blob = new Blob([[head.join(','), ...lines].join('\n')], { type: 'text/csv' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `snrms-applications-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}

onMounted(load)
</script>
