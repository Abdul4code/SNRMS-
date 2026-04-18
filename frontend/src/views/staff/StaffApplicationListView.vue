<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <!-- Header band -->
    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Staff Portal</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">
          {{ auth.isFinance ? 'Payment Confirmations' : 'All Applications' }}
        </h1>
        <p class="text-slate-400 text-sm mt-1">
          {{ auth.isFinance
            ? 'Review and confirm payment evidence submitted by applicants'
            : 'Review and manage street name registration requests' }}
        </p>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-5">

      <!-- Finance stats -->
      <div v-if="auth.isFinance" class="grid grid-cols-3 gap-4">
        <div class="rounded-2xl p-5" style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
          <p class="text-3xl font-bold tracking-tight" style="color: #d97706">{{ stats.pending }}</p>
          <p class="text-xs text-slate-500 mt-1 font-semibold uppercase tracking-wide">Awaiting Confirmation</p>
          <div v-if="stats.pending > 0" class="mt-2 flex items-center gap-1">
            <div class="w-1.5 h-1.5 rounded-full animate-pulse bg-amber-400"></div>
            <span class="text-[10px] font-semibold text-amber-600">Needs action</span>
          </div>
        </div>
        <div class="rounded-2xl p-5" style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
          <p class="text-3xl font-bold tracking-tight" style="color: #059669">{{ stats.confirmed }}</p>
          <p class="text-xs text-slate-500 mt-1 font-semibold uppercase tracking-wide">Payments Confirmed</p>
        </div>
        <div class="rounded-2xl p-5" style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
          <p class="text-3xl font-bold tracking-tight" style="color: #dc2626">{{ stats.rejected }}</p>
          <p class="text-xs text-slate-500 mt-1 font-semibold uppercase tracking-wide">Payments Rejected</p>
        </div>
      </div>

      <!-- Filter bar -->
      <div class="flex flex-wrap gap-3 items-end rounded-2xl p-5"
           style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 1px 4px rgba(0,0,0,0.05)">
        <div v-if="!auth.isFinance" class="flex-1 min-w-40">
          <label class="block text-xs font-semibold text-slate-600 mb-1.5">Status</label>
          <select v-model="filters.status"
                  class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  @change="() => { page = 1; load() }">
            <option value="">All Statuses</option>
            <option v-for="s in STATUS_OPTIONS" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </div>
        <div class="min-w-36">
          <label class="block text-xs font-semibold text-slate-600 mb-1.5">From</label>
          <input v-model="filters.date_from" type="date"
                 class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                 @change="() => { page = 1; load() }" />
        </div>
        <div class="min-w-36">
          <label class="block text-xs font-semibold text-slate-600 mb-1.5">To</label>
          <input v-model="filters.date_to" type="date"
                 class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                 @change="() => { page = 1; load() }" />
        </div>
        <button v-if="filters.date_from || filters.date_to || (!auth.isFinance && filters.status)"
                class="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold text-slate-600 border border-slate-200 hover:bg-slate-50 transition-colors"
                @click="clearFilters">
          <XMarkIcon class="w-3.5 h-3.5" />
          Clear
        </button>
        <span class="ml-auto text-xs text-slate-400 font-medium hidden sm:block self-end pb-1">
          {{ totalCount }} application{{ totalCount === 1 ? '' : 's' }}
        </span>
      </div>

      <!-- Table card -->
      <div class="rounded-2xl overflow-hidden"
           style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">

        <div v-if="loading" class="flex items-center justify-center py-16">
          <div class="w-9 h-9 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
        </div>

        <div v-else-if="!applications.length" class="flex flex-col items-center py-16 gap-2">
          <DocumentTextIcon class="w-10 h-10 text-slate-300" />
          <p class="text-sm font-medium text-slate-500">
            {{ auth.isFinance ? 'No payment confirmations pending.' : 'No applications found.' }}
          </p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0">
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Ref</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Street Name</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider hidden sm:table-cell">Applicant</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider hidden md:table-cell">Updated</th>
                <th class="px-5 py-3.5 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(app, i) in applications" :key="app.id"
                  :style="i < applications.length - 1 ? 'border-bottom: 1px solid #f8fafc' : ''"
                  class="hover:bg-slate-50/60 transition-colors">
                <td class="px-5 py-4 font-mono text-xs text-slate-400 font-medium">{{ app.reference_number || `APP-${app.id}` }}</td>
                <td class="px-5 py-4 font-semibold text-slate-900">{{ app.proposed_street_name }}</td>
                <td class="px-5 py-4 text-slate-500 text-sm hidden sm:table-cell">{{ app.applicant_name || '—' }}</td>
                <td class="px-5 py-4"><StatusBadge :status="app.status" /></td>
                <td class="px-5 py-4 text-xs text-slate-400 hidden md:table-cell">{{ formatDate(app.updated_at || app.created_at) }}</td>
                <td class="px-5 py-4 text-right">
                  <RouterLink :to="`/staff/applications/${app.id}`"
                              class="inline-flex items-center gap-1 text-xs font-semibold transition-colors"
                              :class="actionLabelClass(app)">
                    {{ actionLabel(app) }}
                    <ChevronRightIcon class="w-3.5 h-3.5" />
                  </RouterLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="flex items-center justify-between px-5 py-3.5"
             style="border-top: 1px solid #f1f5f9; background: #f8fafc">
          <p class="text-xs text-slate-500">
            Page {{ page }} of {{ totalPages }} &nbsp;·&nbsp; {{ totalCount }} total
          </p>
          <div class="flex gap-2">
            <button :disabled="page <= 1"
                    class="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 border border-slate-200 hover:bg-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    @click="changePage(page - 1)">← Prev</button>
            <button :disabled="page >= totalPages"
                    class="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 border border-slate-200 hover:bg-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    @click="changePage(page + 1)">Next →</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { XMarkIcon, ChevronRightIcon, DocumentTextIcon } from '@heroicons/vue/24/outline'
import { applicationApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import StatusBadge from '@/components/StatusBadge.vue'

interface Application {
  id: string
  reference_number?: string
  proposed_street_name: string
  applicant_name?: string
  status: string
  created_at: string
  updated_at?: string
}

const auth = useAuthStore()
const applications = ref<Application[]>([])
const loading = ref(false)
const page = ref(1)
const totalPages = ref(1)
const totalCount = ref(0)
const PAGE_SIZE = 20

// Finance stats loaded alongside pending list
const stats = reactive({ pending: 0, confirmed: 0, rejected: 0 })

const filters = ref({ status: '', date_from: '', date_to: '' })

// Finance sees only payment confirmation statuses
const FINANCE_STATUSES = [
  'awaiting_stage_a_payment_confirmation',
  'awaiting_stage_c_payment',
  'awaiting_renewal_payment',
]

// Statuses that count as "confirmed" for finance (moved past payment)
const FINANCE_CONFIRMED_STATUSES = [
  'stage_a_confirmed',
  'under_naming_committee_review',
  'approved_by_committee',
  'rejected_by_committee',
  'awaiting_chairman_approval',
  'approved_by_chairman',
  'rejected_by_chairman',
  'awaiting_stage_c_payment',
  'stage_c_confirmed',
  'certificate_issued',
  'expired',
  'renewal_submitted',
  'awaiting_renewal_payment',
  'renewal_payment_confirmed',
  'renewed',
]

// Status that means payment was rejected and sent back
const FINANCE_REJECTED_STATUSES = ['awaiting_stage_a_payment']

const STATUS_OPTIONS = [
  { value: 'submitted', label: 'Submitted' },
  { value: 'awaiting_stage_a_payment', label: 'Awaiting Payment (A)' },
  { value: 'awaiting_stage_a_payment_confirmation', label: 'Awaiting Payment Confirmation (A)' },
  { value: 'stage_a_confirmed', label: 'Stage A Confirmed' },
  { value: 'under_naming_committee_review', label: 'Under Committee Review' },
  { value: 'approved_by_committee', label: 'Approved by Committee' },
  { value: 'rejected_by_committee', label: 'Rejected by Committee' },
  { value: 'awaiting_chairman_approval', label: 'Awaiting Chairman' },
  { value: 'approved_by_chairman', label: 'Approved by Chairman' },
  { value: 'rejected_by_chairman', label: 'Rejected by Chairman' },
  { value: 'awaiting_stage_c_payment', label: 'Awaiting Payment (C)' },
  { value: 'stage_c_confirmed', label: 'Stage C Confirmed' },
  { value: 'certificate_issued', label: 'Certificate Issued' },
  { value: 'expired', label: 'Expired' },
  { value: 'awaiting_renewal_payment', label: 'Awaiting Renewal Payment' },
]

function actionLabel(app: Application): string {
  if (auth.isFinance && FINANCE_STATUSES.includes(app.status)) return 'Confirm'
  if (auth.isNamingCommittee && app.status === 'under_naming_committee_review') return 'Review'
  if (auth.isChairman && app.status === 'awaiting_chairman_approval') return 'Approve'
  return 'View'
}

function actionLabelClass(app: Application): string {
  const label = actionLabel(app)
  if (label === 'Confirm') return 'text-amber-600 hover:text-amber-700'
  if (label === 'Review' || label === 'Approve') return 'text-blue-600 hover:text-blue-700'
  return 'text-emerald-600 hover:text-emerald-700'
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-NG', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function loadFinanceStats() {
  // Run three parallel count queries to populate stats
  try {
    const [pendingRes, confirmedRes, rejectedRes] = await Promise.all([
      applicationApi.list({ status: FINANCE_STATUSES.join(','), page_size: 1 }).catch(() => null),
      // Count apps that have moved past payment stages (finance confirmed them)
      Promise.all(
        FINANCE_CONFIRMED_STATUSES.map(s =>
          applicationApi.list({ status: s, page_size: 1 }).catch(() => ({ data: { count: 0 } }))
        )
      ),
      applicationApi.list({ status: 'awaiting_stage_a_payment', page_size: 1 }).catch(() => null),
    ])

    // Pending = awaiting confirmation
    const pendingData = pendingRes?.data
    stats.pending = Array.isArray(pendingData) ? pendingData.length : (pendingData?.count ?? 0)

    // Confirmed = sum of all past-payment statuses
    const confirmedTotal = confirmedRes.reduce((sum, r) => {
      const d = r?.data
      return sum + (Array.isArray(d) ? d.length : (d?.count ?? 0))
    }, 0)
    stats.confirmed = confirmedTotal

    // Rejected = sent back to awaiting_stage_a_payment
    const rejectedData = rejectedRes?.data
    stats.rejected = Array.isArray(rejectedData) ? rejectedData.length : (rejectedData?.count ?? 0)
  } catch {
    // stats stay at 0 on error
  }
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: PAGE_SIZE }

    if (auth.isFinance) {
      // Finance only sees payment confirmation statuses
      params.status = FINANCE_STATUSES.join(',')
    } else {
      if (filters.value.status) params.status = filters.value.status
    }

    if (filters.value.date_from) params.created_at__gte = filters.value.date_from
    if (filters.value.date_to) params.created_at__lte = filters.value.date_to

    const { data } = await applicationApi.list(params)
    if (Array.isArray(data)) {
      applications.value = data
      totalCount.value = data.length
      totalPages.value = 1
    } else {
      applications.value = data.results ?? []
      totalCount.value = data.count ?? 0
      totalPages.value = Math.ceil(totalCount.value / PAGE_SIZE)
    }
  } finally {
    loading.value = false
  }
}

function changePage(p: number) {
  page.value = p
  load()
}

function clearFilters() {
  filters.value = { status: '', date_from: '', date_to: '' }
  page.value = 1
  load()
}

onMounted(async () => {
  await load()
  if (auth.isFinance) loadFinanceStats()
})
</script>
