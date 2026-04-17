<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">All Applications</h1>
      <p class="text-sm text-gray-500 mt-0.5">Review and manage street name registration applications</p>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-5 flex flex-wrap gap-3 items-end">
      <div class="flex-1 min-w-40">
        <label class="form-label text-xs">Status</label>
        <select v-model="filters.status" class="form-input text-sm" @change="() => { page = 1; load() }">
          <option value="">All Statuses</option>
          <option v-for="s in STATUS_OPTIONS" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
      </div>
      <div class="min-w-36">
        <label class="form-label text-xs">From</label>
        <input v-model="filters.date_from" type="date" class="form-input text-sm" @change="() => { page = 1; load() }" />
      </div>
      <div class="min-w-36">
        <label class="form-label text-xs">To</label>
        <input v-model="filters.date_to" type="date" class="form-input text-sm" @change="() => { page = 1; load() }" />
      </div>
      <button class="btn-secondary text-sm" @click="clearFilters">Clear</button>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
      <div v-else-if="!applications.length" class="text-center py-16 text-gray-500">
        No applications found.
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Ref</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Street Name</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase hidden sm:table-cell">Applicant</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase hidden md:table-cell">Updated</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="app in applications" :key="app.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 font-mono text-xs text-gray-600">{{ app.reference_number || `#${app.id}` }}</td>
              <td class="px-4 py-3 font-medium text-gray-900">{{ app.proposed_street_name }}</td>
              <td class="px-4 py-3 text-gray-600 hidden sm:table-cell">{{ app.applicant_name || app.applicant }}</td>
              <td class="px-4 py-3"><StatusBadge :status="app.status" /></td>
              <td class="px-4 py-3 text-gray-500 text-xs hidden md:table-cell">{{ formatDate(app.updated_at || app.created_at) }}</td>
              <td class="px-4 py-3">
                <RouterLink
                  :to="`/staff/applications/${app.id}`"
                  class="text-blue-600 hover:text-blue-700 font-medium text-xs mr-3"
                >
                  View
                </RouterLink>
                <!-- Role-specific quick action badges -->
                <span v-if="showReviewBtn(app)" class="text-purple-600 text-xs font-medium">Review</span>
                <span v-else-if="showApproveBtn(app)" class="text-emerald-600 text-xs font-medium">Approve</span>
                <span v-else-if="showConfirmBtn(app)" class="text-yellow-700 text-xs font-medium">Confirm Payment</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50">
        <p class="text-sm text-gray-600">
          Page {{ page }} of {{ totalPages }} &nbsp;({{ totalCount }} total)
        </p>
        <div class="flex gap-2">
          <button :disabled="page <= 1" class="btn-secondary text-xs" @click="changePage(page - 1)">← Prev</button>
          <button :disabled="page >= totalPages" class="btn-secondary text-xs" @click="changePage(page + 1)">Next →</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { applicationApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import StatusBadge from '@/components/StatusBadge.vue'

interface Application {
  id: number
  reference_number?: string
  proposed_street_name: string
  applicant?: string
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

const filters = ref({ status: '', date_from: '', date_to: '' })

const STATUS_OPTIONS = [
  { value: 'submitted', label: 'Submitted' },
  { value: 'awaiting_stage_a_payment', label: 'Awaiting Payment (A)' },
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

function showReviewBtn(app: Application) {
  return auth.isNamingCommittee && app.status === 'under_naming_committee_review'
}
function showApproveBtn(app: Application) {
  return auth.isChairman && app.status === 'awaiting_chairman_approval'
}
function showConfirmBtn(app: Application) {
  return (
    auth.isFinance &&
    ['awaiting_stage_a_payment', 'awaiting_stage_c_payment', 'awaiting_renewal_payment'].includes(app.status)
  )
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-NG', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: PAGE_SIZE }
    if (filters.value.status) params.status = filters.value.status
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

onMounted(load)
</script>
