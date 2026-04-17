<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <!-- Header band -->
    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1">Staff Portal</p>
        <h1 class="text-white text-xl font-bold tracking-tight">
          Welcome back, {{ auth.user?.first_name || auth.user?.email }}
        </h1>
        <p class="text-slate-400 text-sm mt-0.5">
          {{ roleLabel }} · Ibeju-Lekki LGA Street Names Registry
        </p>
      </div>
    </div>

    <div class="max-w-6xl mx-auto px-4 sm:px-6 py-6 space-y-5">

      <!-- Stats grid -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div v-for="stat in stats" :key="stat.label"
             class="rounded-2xl p-5"
             style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
          <p class="text-3xl font-bold tracking-tight" :style="`color: ${stat.color}`">{{ stat.value }}</p>
          <p class="text-xs text-slate-500 mt-1 font-medium">{{ stat.label }}</p>
          <div v-if="stat.value > 0 && stat.urgent" class="mt-2 flex items-center gap-1">
            <div class="w-1.5 h-1.5 rounded-full animate-pulse" style="background: #d97706"></div>
            <span class="text-[10px] font-semibold text-amber-600">Needs attention</span>
          </div>
        </div>
      </div>

      <!-- Finance: confirmed payment amounts by stage -->
      <div v-if="auth.isFinance" class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div class="rounded-2xl p-5"
             style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
          <div class="flex items-center gap-2 mb-3">
            <div class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                 style="background: rgba(5,150,105,0.08); border: 1px solid rgba(5,150,105,0.15)">
              <BanknotesIcon class="w-4 h-4" style="color: #059669" />
            </div>
            <p class="text-xs font-bold text-slate-600 uppercase tracking-wider">Stage A Confirmed</p>
          </div>
          <p class="text-2xl font-bold tracking-tight" style="color: #059669">
            {{ formatAmount(paymentAmounts.stage_a.total) }}
          </p>
          <p class="text-xs text-slate-400 mt-1">{{ paymentAmounts.stage_a.count }} payment{{ paymentAmounts.stage_a.count !== 1 ? 's' : '' }}</p>
        </div>
        <div class="rounded-2xl p-5"
             style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
          <div class="flex items-center gap-2 mb-3">
            <div class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                 style="background: rgba(2,132,199,0.08); border: 1px solid rgba(2,132,199,0.15)">
              <BanknotesIcon class="w-4 h-4" style="color: #0284c7" />
            </div>
            <p class="text-xs font-bold text-slate-600 uppercase tracking-wider">Stage C Confirmed</p>
          </div>
          <p class="text-2xl font-bold tracking-tight" style="color: #0284c7">
            {{ formatAmount(paymentAmounts.stage_c.total) }}
          </p>
          <p class="text-xs text-slate-400 mt-1">{{ paymentAmounts.stage_c.count }} payment{{ paymentAmounts.stage_c.count !== 1 ? 's' : '' }}</p>
        </div>
        <div class="rounded-2xl p-5"
             style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
          <div class="flex items-center gap-2 mb-3">
            <div class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                 style="background: rgba(124,58,237,0.08); border: 1px solid rgba(124,58,237,0.15)">
              <BanknotesIcon class="w-4 h-4" style="color: #7c3aed" />
            </div>
            <p class="text-xs font-bold text-slate-600 uppercase tracking-wider">Renewals Confirmed</p>
          </div>
          <p class="text-2xl font-bold tracking-tight" style="color: #7c3aed">
            {{ formatAmount(paymentAmounts.renewal.total) }}
          </p>
          <p class="text-xs text-slate-400 mt-1">{{ paymentAmounts.renewal.count }} payment{{ paymentAmounts.renewal.count !== 1 ? 's' : '' }}</p>
        </div>
      </div>

      <!-- Pending actions card -->
      <div class="rounded-2xl overflow-hidden"
           style="background: #fff; border: 1px solid #e2e8f0">
        <div class="px-5 py-4 flex items-center justify-between" style="border-bottom: 1px solid #f1f5f9">
          <div>
            <h2 class="text-sm font-bold text-slate-900">Pending Actions</h2>
            <p class="text-xs text-slate-500 mt-0.5">Applications requiring your attention</p>
          </div>
          <RouterLink to="/staff/applications"
                      class="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex items-center gap-1 transition-colors">
            View all
            <ChevronRightIcon class="w-3.5 h-3.5" />
          </RouterLink>
        </div>

        <div v-if="loadingApps" class="flex items-center justify-center py-12">
          <div class="w-8 h-8 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
        </div>

        <div v-else-if="!pendingApps.length" class="flex flex-col items-center py-14 gap-2">
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center"
               style="background: rgba(5,150,105,0.06); border: 1px solid rgba(5,150,105,0.12)">
            <CheckCircleIcon class="w-6 h-6" style="color: #059669" />
          </div>
          <p class="text-sm font-semibold text-slate-700 mt-1">All clear!</p>
          <p class="text-xs text-slate-500">No pending actions at this time.</p>
        </div>

        <div v-else>
          <!-- Mobile: cards -->
          <div class="sm:hidden divide-y divide-slate-50">
            <RouterLink v-for="app in pendingApps" :key="app.id"
                        :to="`/staff/applications/${app.id}`"
                        class="flex items-start gap-3 p-4 hover:bg-slate-50/70 transition-colors">
              <div class="w-2 h-2 rounded-full flex-shrink-0 mt-1.5 bg-amber-400"></div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-slate-900 truncate">{{ app.proposed_street_name }}</p>
                <div class="flex items-center gap-2 mt-1">
                  <StatusBadge :status="app.status" />
                  <span class="text-xs text-slate-400">{{ formatDate(app.updated_at || app.created_at) }}</span>
                </div>
              </div>
              <ChevronRightIcon class="w-4 h-4 text-slate-300 flex-shrink-0 mt-0.5" />
            </RouterLink>
          </div>

          <!-- Desktop: table -->
          <table class="hidden sm:table w-full text-sm">
            <thead>
              <tr style="background: #f8fafc; border-bottom: 1px solid #f1f5f9">
                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Reference</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Street Name</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Updated</th>
                <th class="px-5 py-3 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(app, i) in pendingApps" :key="app.id"
                  :style="i < pendingApps.length - 1 ? 'border-bottom: 1px solid #f8fafc' : ''"
                  class="hover:bg-slate-50/50 transition-colors">
                <td class="px-5 py-4 font-mono text-xs text-slate-400">{{ app.reference_number || `APP-${app.id}` }}</td>
                <td class="px-5 py-4 font-semibold text-slate-900">{{ app.proposed_street_name }}</td>
                <td class="px-5 py-4"><StatusBadge :status="app.status" /></td>
                <td class="px-5 py-4 text-xs text-slate-400">{{ formatDate(app.updated_at || app.created_at) }}</td>
                <td class="px-5 py-4 text-right">
                  <RouterLink :to="`/staff/applications/${app.id}`"
                              class="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 hover:text-emerald-700 transition-colors">
                    Review
                    <ChevronRightIcon class="w-3.5 h-3.5" />
                  </RouterLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Quick links for chairman -->
      <div v-if="auth.isChairman" class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <RouterLink to="/admin/staff"
                    class="flex items-center gap-3 p-4 rounded-2xl transition-all hover:shadow-sm"
                    style="background: #fff; border: 1px solid #e2e8f0">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
               style="background: rgba(5,150,105,0.08); border: 1px solid rgba(5,150,105,0.15)">
            <UserGroupIcon class="w-5 h-5" style="color: #059669" />
          </div>
          <div>
            <p class="text-sm font-semibold text-slate-900">Staff Management</p>
            <p class="text-xs text-slate-500">Manage staff accounts</p>
          </div>
          <ChevronRightIcon class="w-4 h-4 text-slate-300 ml-auto" />
        </RouterLink>
        <RouterLink to="/admin/fees"
                    class="flex items-center gap-3 p-4 rounded-2xl transition-all hover:shadow-sm"
                    style="background: #fff; border: 1px solid #e2e8f0">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
               style="background: rgba(217,119,6,0.08); border: 1px solid rgba(217,119,6,0.15)">
            <CurrencyDollarIcon class="w-5 h-5" style="color: #d97706" />
          </div>
          <div>
            <p class="text-sm font-semibold text-slate-900">Fee Configuration</p>
            <p class="text-xs text-slate-500">Set application fees</p>
          </div>
          <ChevronRightIcon class="w-4 h-4 text-slate-300 ml-auto" />
        </RouterLink>
        <RouterLink to="/admin/street-types"
                    class="flex items-center gap-3 p-4 rounded-2xl transition-all hover:shadow-sm"
                    style="background: #fff; border: 1px solid #e2e8f0">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
               style="background: rgba(2,132,199,0.08); border: 1px solid rgba(2,132,199,0.15)">
            <MapIcon class="w-5 h-5" style="color: #0284c7" />
          </div>
          <div>
            <p class="text-sm font-semibold text-slate-900">Street Types</p>
            <p class="text-xs text-slate-500">Configure street categories</p>
          </div>
          <ChevronRightIcon class="w-4 h-4 text-slate-300 ml-auto" />
        </RouterLink>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { ChevronRightIcon, CheckCircleIcon, UserGroupIcon, CurrencyDollarIcon, MapIcon, BanknotesIcon } from '@heroicons/vue/24/outline'
import { applicationApi, paymentApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import StatusBadge from '@/components/StatusBadge.vue'

interface Application {
  id: number
  reference_number?: string
  proposed_street_name: string
  status: string
  created_at: string
  updated_at?: string
}

const auth = useAuthStore()
const allApps = ref<Application[]>([])
const loadingApps = ref(false)

// Finance-specific stat counts loaded separately
const financeStats = reactive({ pending: 0, confirmed: 0, rejected: 0 })
const paymentAmounts = reactive({
  stage_a: { count: 0, total: '0' },
  stage_c: { count: 0, total: '0' },
  renewal: { count: 0, total: '0' },
})

const FINANCE_PENDING_STATUSES = [
  'awaiting_stage_a_payment_confirmation',
  'awaiting_stage_c_payment',
  'awaiting_renewal_payment',
]
const FINANCE_CONFIRMED_STATUSES = [
  'stage_a_confirmed', 'under_naming_committee_review', 'approved_by_committee',
  'rejected_by_committee', 'awaiting_chairman_approval', 'approved_by_chairman',
  'rejected_by_chairman', 'awaiting_stage_c_payment', 'stage_c_confirmed',
  'certificate_issued', 'expired', 'renewal_submitted', 'awaiting_renewal_payment',
  'renewal_payment_confirmed', 'renewed',
]

const ROLE_PENDING_STATUS: Record<string, string[]> = {
  finance: FINANCE_PENDING_STATUSES,
  naming_committee: ['under_naming_committee_review'],
  committee_chairman: ['awaiting_chairman_approval', 'stage_c_confirmed'],
}

const roleLabel = computed(() => {
  const map: Record<string, string> = {
    finance: 'Finance Officer',
    naming_committee: 'Naming Committee Member',
    committee_chairman: 'Committee Chairman',
  }
  return map[auth.user?.role ?? ''] ?? auth.user?.role ?? ''
})

const pendingStatuses = computed(() => ROLE_PENDING_STATUS[auth.user?.role ?? ''] ?? [])
const pendingApps = computed(() => allApps.value.filter(a => pendingStatuses.value.includes(a.status)))

const stats = computed(() => {
  if (auth.isFinance) {
    return [
      { label: 'Awaiting Confirmation', value: financeStats.pending, color: financeStats.pending > 0 ? '#d97706' : '#0f172a', urgent: financeStats.pending > 0 },
      { label: 'Pending Action', value: financeStats.pending, color: financeStats.pending > 0 ? '#d97706' : '#0f172a', urgent: financeStats.pending > 0 },
      { label: 'Payments Confirmed', value: financeStats.confirmed, color: '#059669', urgent: false },
      { label: 'Payments Rejected', value: financeStats.rejected, color: '#dc2626', urgent: false },
    ].filter((_, i) => i !== 1) // remove duplicate — show 3 meaningful cards
  }
  const counts: Record<string, number> = {}
  allApps.value.forEach(a => { counts[a.status] = (counts[a.status] ?? 0) + 1 })
  const pending = pendingApps.value.length
  return [
    { label: 'Total Applications', value: allApps.value.length, color: '#0f172a', urgent: false },
    { label: 'Pending Action', value: pending, color: pending > 0 ? '#d97706' : '#0f172a', urgent: pending > 0 },
    { label: 'Approved', value: (counts['approved_by_chairman'] ?? 0) + (counts['certificate_issued'] ?? 0), color: '#059669', urgent: false },
    { label: 'Rejected', value: (counts['rejected_by_committee'] ?? 0) + (counts['rejected_by_chairman'] ?? 0), color: '#dc2626', urgent: false },
  ]
})

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-NG', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatAmount(value: string | number): string {
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '₦0'
  return '₦' + num.toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function loadFinanceStats() {
  try {
    const [pendingRes, confirmedRes, rejectedRes, amountsRes] = await Promise.all([
      applicationApi.list({ status: FINANCE_PENDING_STATUSES.join(','), page_size: 1 }).catch(() => null),
      Promise.all(
        FINANCE_CONFIRMED_STATUSES.map(s =>
          applicationApi.list({ status: s, page_size: 1 }).catch(() => ({ data: { count: 0 } }))
        )
      ),
      applicationApi.list({ status: 'awaiting_stage_a_payment', page_size: 1 }).catch(() => null),
      paymentApi.getStats().catch(() => null),
    ])

    const pendingData = pendingRes?.data
    financeStats.pending = Array.isArray(pendingData) ? pendingData.length : (pendingData?.count ?? 0)

    financeStats.confirmed = confirmedRes.reduce((sum, r) => {
      const d = r?.data
      return sum + (Array.isArray(d) ? d.length : (d?.count ?? 0))
    }, 0)

    const rejectedData = rejectedRes?.data
    financeStats.rejected = Array.isArray(rejectedData) ? rejectedData.length : (rejectedData?.count ?? 0)

    if (amountsRes?.data) {
      const d = amountsRes.data
      if (d.stage_a) { paymentAmounts.stage_a.count = d.stage_a.count; paymentAmounts.stage_a.total = d.stage_a.total }
      if (d.stage_c) { paymentAmounts.stage_c.count = d.stage_c.count; paymentAmounts.stage_c.total = d.stage_c.total }
      if (d.renewal) { paymentAmounts.renewal.count = d.renewal.count; paymentAmounts.renewal.total = d.renewal.total }
    }
  } catch {
    // stats stay at 0 on error
  }
}

onMounted(async () => {
  loadingApps.value = true
  try {
    const { data } = await applicationApi.list()
    allApps.value = Array.isArray(data) ? data : data.results ?? []
  } finally {
    loadingApps.value = false
  }
  if (auth.isFinance) loadFinanceStats()
})
</script>
