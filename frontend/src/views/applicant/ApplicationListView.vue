<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Page header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">My Applications</h1>
        <p class="text-sm text-gray-500 mt-0.5">Manage your street name registration applications</p>
      </div>
      <RouterLink to="/applications/new" class="btn-primary gap-2">
        <PlusIcon class="w-4 h-4" />
        New Application
      </RouterLink>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-6 flex flex-wrap gap-3">
      <div class="flex-1 min-w-48">
        <select v-model="filters.status" @change="loadApplications" class="form-input text-sm">
          <option value="">All Statuses</option>
          <option v-for="s in STATUS_OPTIONS" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
      </div>
      <button @click="clearFilters" class="btn-secondary text-sm">
        <FunnelIcon class="w-4 h-4 mr-1" />
        Clear
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-16">
      <div class="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" />
    </div>

    <!-- Empty state -->
    <div v-else-if="!applications.length" class="text-center py-20 bg-white rounded-xl border border-gray-200">
      <DocumentTextIcon class="w-12 h-12 text-gray-300 mx-auto mb-3" />
      <h3 class="text-base font-medium text-gray-900 mb-1">No applications yet</h3>
      <p class="text-sm text-gray-500 mb-4">Submit your first street name registration application.</p>
      <RouterLink to="/applications/new" class="btn-primary">New Application</RouterLink>
    </div>

    <!-- Table -->
    <div v-else class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Reference</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Street Name</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider hidden sm:table-cell">Type</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider hidden md:table-cell">Date</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="app in applications"
              :key="app.id"
              class="hover:bg-gray-50 transition-colors"
            >
              <td class="px-4 py-3 font-mono text-xs text-gray-600">{{ app.reference_number || `#${app.id}` }}</td>
              <td class="px-4 py-3 font-medium text-gray-900">{{ app.proposed_street_name }}</td>
              <td class="px-4 py-3 text-gray-600 hidden sm:table-cell">{{ app.street_type_name || app.street_type }}</td>
              <td class="px-4 py-3">
                <StatusBadge :status="app.status" />
              </td>
              <td class="px-4 py-3 text-gray-500 hidden md:table-cell">{{ formatDate(app.created_at) }}</td>
              <td class="px-4 py-3">
                <RouterLink
                  :to="`/applications/${app.id}`"
                  class="text-blue-600 hover:text-blue-700 font-medium text-xs"
                >
                  View →
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { PlusIcon, FunnelIcon, DocumentTextIcon } from '@heroicons/vue/24/outline'
import { applicationApi } from '@/services/api'
import StatusBadge from '@/components/StatusBadge.vue'

interface Application {
  id: number
  reference_number?: string
  proposed_street_name: string
  street_type?: string
  street_type_name?: string
  status: string
  created_at: string
}

const STATUS_OPTIONS = [
  { value: 'draft', label: 'Draft' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'awaiting_stage_a_payment', label: 'Awaiting Payment (Stage A)' },
  { value: 'stage_a_confirmed', label: 'Stage A Confirmed' },
  { value: 'under_naming_committee_review', label: 'Under Committee Review' },
  { value: 'approved_by_committee', label: 'Approved by Committee' },
  { value: 'rejected_by_committee', label: 'Rejected by Committee' },
  { value: 'awaiting_chairman_approval', label: 'Awaiting Chairman Approval' },
  { value: 'approved_by_chairman', label: 'Approved by Chairman' },
  { value: 'rejected_by_chairman', label: 'Rejected by Chairman' },
  { value: 'awaiting_stage_c_payment', label: 'Awaiting Payment (Stage C)' },
  { value: 'stage_c_confirmed', label: 'Stage C Confirmed' },
  { value: 'certificate_issued', label: 'Certificate Issued' },
  { value: 'expired', label: 'Expired' },
  { value: 'renewed', label: 'Renewed' },
  { value: 'withdrawn', label: 'Withdrawn' },
]

const applications = ref<Application[]>([])
const loading = ref(false)
const filters = ref({ status: '' })

async function loadApplications() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (filters.value.status) params.status = filters.value.status
    const { data } = await applicationApi.list(params)
    applications.value = Array.isArray(data) ? data : data.results ?? []
  } catch {
    applications.value = []
  } finally {
    loading.value = false
  }
}

function clearFilters() {
  filters.value.status = ''
  loadApplications()
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-NG', { day: 'numeric', month: 'short', year: 'numeric' })
}

onMounted(loadApplications)
</script>
