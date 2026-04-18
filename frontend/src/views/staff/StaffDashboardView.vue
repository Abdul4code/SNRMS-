<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <!-- Header band -->
    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Staff Portal</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">
          Welcome back, {{ auth.user?.first_name || auth.user?.email }}
        </h1>
        <p class="text-slate-400 text-sm mt-1">
          {{ roleLabel }} · Ibeju-Lekki LGA Street Names Registry
        </p>
      </div>
    </div>

    <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">

      <!-- Stats grid -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div v-for="stat in stats" :key="stat.label"
             class="rounded-2xl p-6"
             style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
          <p class="text-4xl font-bold tracking-tight" :style="`color: ${stat.color}`">{{ stat.value }}</p>
          <p class="text-xs text-slate-500 mt-1.5 font-semibold uppercase tracking-wide">{{ stat.label }}</p>
          <div v-if="stat.value > 0 && stat.urgent" class="mt-2 flex items-center gap-1">
            <div class="w-1.5 h-1.5 rounded-full animate-pulse" style="background: #d97706"></div>
            <span class="text-[10px] font-semibold text-amber-600">Needs attention</span>
          </div>
        </div>
      </div>

      <!-- Finance: confirmed payment amounts by stage -->
      <div v-if="auth.isFinance || auth.isChairman" class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="rounded-2xl p-6"
             style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
          <div class="flex items-center gap-2.5 mb-4">
            <div class="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
                 style="background: rgba(5,150,105,0.1); border: 1px solid rgba(5,150,105,0.2)">
              <BanknotesIcon class="w-4 h-4" style="color: #059669" />
            </div>
            <p class="text-xs font-bold text-slate-600 uppercase tracking-wider">Stage A Confirmed</p>
          </div>
          <p class="text-2xl font-bold tracking-tight" style="color: #059669">
            {{ formatAmount(paymentAmounts.stage_a.total) }}
          </p>
          <p class="text-xs text-slate-400 mt-1.5">{{ paymentAmounts.stage_a.count }} payment{{ paymentAmounts.stage_a.count !== 1 ? 's' : '' }}</p>
        </div>
        <div class="rounded-2xl p-6"
             style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
          <div class="flex items-center gap-2.5 mb-4">
            <div class="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
                 style="background: rgba(2,132,199,0.1); border: 1px solid rgba(2,132,199,0.2)">
              <BanknotesIcon class="w-4 h-4" style="color: #0284c7" />
            </div>
            <p class="text-xs font-bold text-slate-600 uppercase tracking-wider">Stage C Confirmed</p>
          </div>
          <p class="text-2xl font-bold tracking-tight" style="color: #0284c7">
            {{ formatAmount(paymentAmounts.stage_c.total) }}
          </p>
          <p class="text-xs text-slate-400 mt-1.5">{{ paymentAmounts.stage_c.count }} payment{{ paymentAmounts.stage_c.count !== 1 ? 's' : '' }}</p>
        </div>
        <div class="rounded-2xl p-6"
             style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
          <div class="flex items-center gap-2.5 mb-4">
            <div class="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
                 style="background: rgba(124,58,237,0.1); border: 1px solid rgba(124,58,237,0.2)">
              <BanknotesIcon class="w-4 h-4" style="color: #7c3aed" />
            </div>
            <p class="text-xs font-bold text-slate-600 uppercase tracking-wider">Renewals Confirmed</p>
          </div>
          <p class="text-2xl font-bold tracking-tight" style="color: #7c3aed">
            {{ formatAmount(paymentAmounts.renewal.total) }}
          </p>
          <p class="text-xs text-slate-400 mt-1.5">{{ paymentAmounts.renewal.count }} payment{{ paymentAmounts.renewal.count !== 1 ? 's' : '' }}</p>
        </div>
      </div>

      <!-- Pending actions card -->
      <div class="rounded-2xl overflow-hidden"
           style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
        <div class="px-6 py-5 flex items-center justify-between" style="border-bottom: 1px solid #f1f5f9">

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

      <!-- Naming committee & chairman: certificate pipeline -->
      <div v-if="auth.isNamingCommittee || auth.isChairman" class="rounded-2xl overflow-hidden"
           style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
        <div class="px-6 py-5 flex items-center justify-between" style="border-bottom: 1px solid #f1f5f9">
          <div>
            <h2 class="text-sm font-bold text-slate-900">Awaiting Certificate &amp; Installation</h2>
            <p class="text-xs text-slate-500 mt-0.5">Applications pending certificate issuance, map upload, or signpost installation</p>
          </div>
          <span v-if="awaitingCertOrInstallApps.length"
                class="text-xs font-bold px-2.5 py-1 rounded-full bg-amber-100 text-amber-700">
            {{ awaitingCertOrInstallApps.length }}
          </span>
        </div>

        <div v-if="loadingApps" class="flex items-center justify-center py-12">
          <div class="w-8 h-8 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
        </div>

        <div v-else-if="!awaitingCertOrInstallApps.length" class="flex flex-col items-center py-12 gap-2">
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center"
               style="background: rgba(5,150,105,0.06); border: 1px solid rgba(5,150,105,0.12)">
            <CheckCircleIcon class="w-6 h-6" style="color: #059669" />
          </div>
          <p class="text-sm font-semibold text-slate-700 mt-1">All complete!</p>
          <p class="text-xs text-slate-500">No applications pending post-certificate actions.</p>
        </div>

        <div v-else>
          <!-- Mobile -->
          <div class="sm:hidden divide-y divide-slate-50">
            <RouterLink v-for="app in awaitingCertOrInstallApps" :key="app.id"
                        :to="`/staff/applications/${app.id}`"
                        class="flex items-start gap-3 p-4 hover:bg-slate-50/70 transition-colors">
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-slate-900 truncate">{{ app.proposed_street_name }}</p>
                <div class="flex items-center gap-2 mt-1 flex-wrap">
                  <StatusBadge :status="app.status" />
                  <span v-if="app.status === 'certificate_issued'" class="flex items-center gap-1.5 text-xs text-slate-500">
                    <span :class="app.google_map_uploaded ? 'text-emerald-600' : 'text-slate-400'">Map {{ app.google_map_uploaded ? '✓' : '○' }}</span>
                    <span :class="app.signpost_installed ? 'text-emerald-600' : 'text-slate-400'">Post {{ app.signpost_installed ? '✓' : '○' }}</span>
                  </span>
                </div>
              </div>
              <ChevronRightIcon class="w-4 h-4 text-slate-300 flex-shrink-0 mt-0.5" />
            </RouterLink>
          </div>

          <!-- Desktop -->
          <table class="hidden sm:table w-full text-sm">
            <thead>
              <tr style="background: #f8fafc; border-bottom: 1px solid #f1f5f9">
                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Reference</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Street Name</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Expires</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Map</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Post</th>
                <th class="px-5 py-3 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(app, i) in awaitingCertOrInstallApps" :key="app.id"
                  :style="i < awaitingCertOrInstallApps.length - 1 ? 'border-bottom: 1px solid #f8fafc' : ''"
                  :class="app.status === 'expired' ? 'bg-red-50/40' : ''"
                  class="hover:bg-slate-50/50 transition-colors">
                <td class="px-5 py-4 font-mono text-xs text-slate-400">{{ app.reference_number || `APP-${app.id}` }}</td>
                <td class="px-5 py-4 font-semibold text-slate-900">{{ app.proposed_street_name }}</td>
                <td class="px-5 py-4"><StatusBadge :status="app.status" /></td>
                <td class="px-5 py-4 text-xs">
                  <span v-if="app.expires_at" :class="app.status === 'expired' ? 'text-red-600 font-semibold' : 'text-slate-500'">
                    {{ formatDate(app.expires_at) }}
                  </span>
                  <span v-else class="text-slate-300">—</span>
                </td>
                <td class="px-5 py-4">
                  <span v-if="app.status === 'stage_c_confirmed'" class="text-xs text-slate-400">—</span>
                  <span v-else class="text-sm font-bold" :class="app.google_map_uploaded ? 'text-emerald-600' : 'text-slate-300'">
                    {{ app.google_map_uploaded ? '✓' : '○' }}
                  </span>
                </td>
                <td class="px-5 py-4">
                  <span v-if="app.status === 'stage_c_confirmed'" class="text-xs text-slate-400">—</span>
                  <span v-else class="text-sm font-bold" :class="app.signpost_installed ? 'text-emerald-600' : 'text-slate-300'">
                    {{ app.signpost_installed ? '✓' : '○' }}
                  </span>
                </td>
                <td class="px-5 py-4 text-right">
                  <RouterLink :to="`/staff/applications/${app.id}`"
                              class="inline-flex items-center gap-1 text-xs font-semibold transition-colors"
                              :class="app.status === 'expired' ? 'text-red-600 hover:text-red-700' : 'text-emerald-600 hover:text-emerald-700'">
                    {{ app.status === 'stage_c_confirmed' ? 'Issue Cert' : app.status === 'expired' ? 'View' : 'Update' }}
                    <ChevronRightIcon class="w-3.5 h-3.5" />
                  </RouterLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Quick links for chairman -->
      <div v-if="auth.isChairman" class="grid grid-cols-1 sm:grid-cols-1 gap-3">
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
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { ChevronRightIcon, CheckCircleIcon, UserGroupIcon, BanknotesIcon } from '@heroicons/vue/24/outline'
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
  google_map_uploaded?: boolean
  signpost_installed?: boolean
  expires_at?: string | null
}

const auth = useAuthStore()

// Pending actions for this role (loaded with server-side status filter)
const pendingApps = ref<Application[]>([])
const certPipelineApps = ref<Application[]>([])
const loadingApps = ref(false)

// Server-side stat counts (accurate regardless of dataset size)
const totalCount = ref(0)
const pendingCount = ref(0)
const approvedCount = ref(0)
const rejectedCount = ref(0)

const financeStats = reactive({ pending: 0, confirmed: 0, rejected: 0 })
const paymentAmounts = reactive({
  stage_a: { count: 0, total: '0' },
  stage_c: { count: 0, total: '0' },
  renewal: { count: 0, total: '0' },
})

const FINANCE_PENDING_STATUSES = [
  'awaiting_stage_a_payment_confirmation',
  'awaiting_stage_c_payment_confirmation',
  'awaiting_renewal_payment_confirmation',
]
const FINANCE_CONFIRMED_STATUSES = [
  'stage_a_confirmed', 'under_naming_committee_review', 'approved_by_committee',
  'rejected_by_committee', 'awaiting_chairman_approval', 'approved_by_chairman',
  'rejected_by_chairman', 'awaiting_stage_c_payment', 'stage_c_confirmed',
  'certificate_issued', 'expired', 'renewal_submitted', 'awaiting_renewal_payment',
  'renewal_payment_confirmed', 'renewed',
]

const COMMITTEE_APPROVED_STATUSES = [
  'awaiting_chairman_approval', 'approved_by_chairman', 'rejected_by_chairman',
  'awaiting_stage_c_payment', 'stage_c_confirmed', 'certificate_issued',
  'expired', 'renewal_submitted', 'awaiting_renewal_payment',
  'renewal_payment_confirmed', 'renewed',
]
const CHAIRMAN_APPROVED_STATUSES = [
  'approved_by_chairman', 'awaiting_stage_c_payment', 'stage_c_confirmed',
  'certificate_issued', 'expired', 'renewal_submitted', 'awaiting_renewal_payment',
  'renewal_payment_confirmed', 'renewed',
]
const CHAIRMAN_REJECTED_STATUSES = ['rejected_by_chairman', 'rejected_by_committee']

const ROLE_PENDING_STATUSES: Record<string, string[]> = {
  finance: FINANCE_PENDING_STATUSES,
  naming_committee: ['under_naming_committee_review', 'awaiting_document_resubmission'],
  committee_chairman: ['awaiting_chairman_approval'],
}

const roleLabel = computed(() => {
  const map: Record<string, string> = {
    finance: 'Finance Officer',
    naming_committee: 'Naming Committee Member',
    committee_chairman: 'Committee Chairman',
  }
  return map[auth.user?.role ?? ''] ?? auth.user?.role ?? ''
})

const awaitingCertOrInstallApps = computed(() =>
  certPipelineApps.value.filter(a => {
    if (a.status === 'stage_c_confirmed') return true
    if (a.status === 'certificate_issued') return !a.google_map_uploaded || !a.signpost_installed
    if (a.status === 'expired') return true
    return false
  })
)

const stats = computed(() => {
  if (auth.isFinance) {
    return [
      { label: 'Awaiting Confirmation', value: financeStats.pending, color: financeStats.pending > 0 ? '#d97706' : '#0f172a', urgent: financeStats.pending > 0 },
      { label: 'Payments Confirmed', value: financeStats.confirmed, color: '#059669', urgent: false },
      { label: 'Payments Rejected', value: financeStats.rejected, color: '#dc2626', urgent: false },
    ]
  }

  let approvedLabel = 'Approved'
  let rejectedLabel = 'Rejected'
  if (auth.isNamingCommittee) {
    approvedLabel = 'Forwarded to Chairman'
    rejectedLabel = 'Rejected by Committee'
  }

  return [
    { label: 'Total Applications', value: totalCount.value, color: '#0f172a', urgent: false },
    { label: 'Pending Action', value: pendingCount.value, color: pendingCount.value > 0 ? '#d97706' : '#0f172a', urgent: pendingCount.value > 0 },
    { label: approvedLabel, value: approvedCount.value, color: '#059669', urgent: false },
    { label: rejectedLabel, value: rejectedCount.value, color: '#dc2626', urgent: false },
  ]
})

function getCount(data: unknown): number {
  if (!data) return 0
  if (Array.isArray(data)) return data.length
  return (data as { count?: number }).count ?? 0
}

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
      applicationApi.list({ status: FINANCE_PENDING_STATUSES.join(',') }).catch(() => null),
      Promise.all(
        FINANCE_CONFIRMED_STATUSES.map(s =>
          applicationApi.list({ status: s }).catch(() => ({ data: { count: 0 } }))
        )
      ),
      applicationApi.list({ status: 'awaiting_stage_a_payment' }).catch(() => null),
      paymentApi.getStats().catch(() => null),
    ])

    financeStats.pending = getCount(pendingRes?.data)
    financeStats.confirmed = confirmedRes.reduce((sum, r) => sum + getCount(r?.data), 0)
    financeStats.rejected = getCount(rejectedRes?.data)

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

async function loadRoleStats() {
  const role = auth.user?.role ?? ''
  const myPendingStatuses = ROLE_PENDING_STATUSES[role] ?? []

  const queries: Promise<unknown>[] = [
    // Total applications
    applicationApi.list({}).then(({ data }) => {
      totalCount.value = getCount(data)
    }).catch(() => {}),
  ]

  if (myPendingStatuses.length) {
    queries.push(
      applicationApi.list({ status: myPendingStatuses.join(',') }).then(({ data }) => {
        pendingCount.value = getCount(data)
      }).catch(() => {})
    )
  }

  if (auth.isNamingCommittee) {
    queries.push(
      applicationApi.list({ status: COMMITTEE_APPROVED_STATUSES.join(',') }).then(({ data }) => {
        approvedCount.value = getCount(data)
      }).catch(() => {}),
      applicationApi.list({ status: 'rejected_by_committee' }).then(({ data }) => {
        rejectedCount.value = getCount(data)
      }).catch(() => {})
    )
  } else if (auth.isChairman) {
    queries.push(
      applicationApi.list({ status: CHAIRMAN_APPROVED_STATUSES.join(',') }).then(({ data }) => {
        approvedCount.value = getCount(data)
      }).catch(() => {}),
      applicationApi.list({ status: CHAIRMAN_REJECTED_STATUSES.join(',') }).then(({ data }) => {
        rejectedCount.value = getCount(data)
      }).catch(() => {})
    )
  }

  await Promise.all(queries)
}

onMounted(async () => {
  loadingApps.value = true
  try {
    const role = auth.user?.role ?? ''
    const myPendingStatuses = ROLE_PENDING_STATUSES[role] ?? []

    const fetches: Promise<unknown>[] = []

    // Load pending apps for this role (capped at 20 for dashboard preview)
    if (myPendingStatuses.length) {
      fetches.push(
        applicationApi.list({ status: myPendingStatuses.join(',') }).then(({ data }) => {
          pendingApps.value = Array.isArray(data) ? data : data.results ?? []
        }).catch(() => {})
      )
    }

    // Load cert pipeline for naming committee / chairman
    if (auth.isNamingCommittee || auth.isChairman) {
      fetches.push(
        applicationApi.list({ status: 'stage_c_confirmed,certificate_issued,expired' }).then(({ data }) => {
          certPipelineApps.value = Array.isArray(data) ? data : data.results ?? []
        }).catch(() => {})
      )
    }

    await Promise.all(fetches)
  } finally {
    loadingApps.value = false
  }

  // Load accurate stat counts in parallel (these are count-only queries)
  if (auth.isFinance || auth.isChairman) loadFinanceStats()
  if (!auth.isFinance) loadRoleStats()
})
</script>
