<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <!-- Page header band -->
    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1">My Portal</p>
            <h1 class="text-white text-xl font-bold tracking-tight">Street Name Applications</h1>
            <p class="text-slate-400 text-sm mt-0.5">Track and manage your registration requests</p>
          </div>
          <RouterLink to="/applications/new"
                      class="flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white transition-all active:scale-[0.97]"
                      style="background: linear-gradient(135deg, #059669, #047857); box-shadow: 0 4px 16px rgba(5,150,105,0.4)">
            <PlusIcon class="w-4 h-4" />
            <span class="hidden sm:inline">New Application</span>
            <span class="sm:hidden">New</span>
          </RouterLink>
        </div>
      </div>
    </div>

    <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-5">

      <!-- Stats row -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div v-for="stat in stats" :key="stat.label"
             class="rounded-xl p-4"
             style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
          <p class="text-2xl font-bold" :style="`color: ${stat.color}`">{{ stat.value }}</p>
          <p class="text-xs text-slate-500 mt-0.5 font-medium">{{ stat.label }}</p>
        </div>
      </div>

      <!-- Filter bar -->
      <div class="flex flex-wrap gap-2.5 items-center rounded-xl p-3"
           style="background: #fff; border: 1px solid #e2e8f0">
        <select v-model="filters.status" @change="loadApplications"
                class="flex-1 min-w-36 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
          <option value="">All Statuses</option>
          <option v-for="s in STATUS_OPTIONS" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
        <button v-if="filters.status" @click="clearFilters"
                class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-slate-600 border border-slate-200 hover:bg-slate-50 transition-colors">
          <XMarkIcon class="w-3.5 h-3.5" />
          Clear
        </button>
        <span class="ml-auto text-xs text-slate-400 font-medium hidden sm:block">
          {{ applications.length }} {{ applications.length === 1 ? 'result' : 'results' }}
        </span>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex flex-col items-center justify-center py-20 gap-3">
        <div class="w-10 h-10 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
        <p class="text-sm text-slate-500">Loading applications…</p>
      </div>

      <!-- Empty state -->
      <div v-else-if="!applications.length"
           class="text-center py-20 rounded-2xl"
           style="background: #fff; border: 1px solid #e2e8f0">
        <div class="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
             style="background: linear-gradient(135deg, rgba(5,150,105,0.08), rgba(5,150,105,0.04)); border: 1px solid rgba(5,150,105,0.15)">
          <DocumentTextIcon class="w-8 h-8" style="color: #059669" />
        </div>
        <h3 class="text-base font-bold text-slate-900 mb-1">No applications yet</h3>
        <p class="text-sm text-slate-500 mb-6 max-w-xs mx-auto">
          Submit your first street name registration application with Ibeju-Lekki LGA.
        </p>
        <RouterLink to="/applications/new"
                    class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white"
                    style="background: linear-gradient(135deg, #059669, #047857); box-shadow: 0 4px 16px rgba(5,150,105,0.3)">
          <PlusIcon class="w-4 h-4" />
          Start your first application
        </RouterLink>
      </div>

      <!-- Application cards (mobile) / table (desktop) -->
      <div v-else>

        <!-- Mobile: card list -->
        <div class="sm:hidden space-y-3">
          <RouterLink v-for="app in applications" :key="app.id"
                      :to="`/applications/${app.id}`"
                      class="block rounded-2xl p-4 transition-all active:scale-[0.99]"
                      style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
            <div class="flex items-start justify-between gap-3 mb-2.5">
              <div class="min-w-0">
                <p class="font-semibold text-slate-900 text-sm truncate">{{ app.proposed_street_name }}</p>
                <p class="text-xs text-slate-500 mt-0.5">{{ app.street_type_name || app.street_type }}</p>
              </div>
              <StatusBadge :status="app.status" />
            </div>
            <div class="flex items-center justify-between">
              <span class="font-mono text-xs text-slate-400">{{ app.reference_number || `APP-${app.id}` }}</span>
              <span class="text-xs text-slate-400">{{ formatDate(app.created_at) }}</span>
            </div>
          </RouterLink>
        </div>

        <!-- Desktop: table -->
        <div class="hidden sm:block rounded-2xl overflow-hidden"
             style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
          <table class="w-full text-sm">
            <thead>
              <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0">
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Reference</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Street Name</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider hidden lg:table-cell">Type</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider hidden md:table-cell">Date</th>
                <th class="px-5 py-3.5 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(app, i) in applications" :key="app.id"
                  :style="i < applications.length - 1 ? 'border-bottom: 1px solid #f1f5f9' : ''"
                  class="hover:bg-slate-50/70 transition-colors">
                <td class="px-5 py-4 font-mono text-xs text-slate-400 font-medium">
                  {{ app.reference_number || `APP-${app.id}` }}
                </td>
                <td class="px-5 py-4 font-semibold text-slate-900">{{ app.proposed_street_name }}</td>
                <td class="px-5 py-4 text-slate-500 hidden lg:table-cell">{{ app.street_type_name || app.street_type }}</td>
                <td class="px-5 py-4"><StatusBadge :status="app.status" /></td>
                <td class="px-5 py-4 text-slate-400 text-xs hidden md:table-cell">{{ formatDate(app.created_at) }}</td>
                <td class="px-5 py-4 text-right">
                  <RouterLink :to="`/applications/${app.id}`"
                              class="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 hover:text-emerald-700 transition-colors">
                    View
                    <ChevronRightIcon class="w-3.5 h-3.5" />
                  </RouterLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { PlusIcon, DocumentTextIcon, XMarkIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'
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

const stats = computed(() => {
  const all = applications.value
  return [
    { label: 'Total', value: all.length, color: '#0f172a' },
    { label: 'Active', value: all.filter(a => !['draft','certificate_issued','withdrawn','expired'].includes(a.status)).length, color: '#059669' },
    { label: 'Approved', value: all.filter(a => a.status === 'certificate_issued').length, color: '#0284c7' },
    { label: 'Pending', value: all.filter(a => a.status === 'draft').length, color: '#d97706' },
  ]
})

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
