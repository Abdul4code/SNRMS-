<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
      <p class="text-sm text-gray-500 mt-0.5">
        Welcome back, {{ auth.user?.full_name || auth.user?.email }}
        <span class="ml-1 text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full capitalize">{{ auth.user?.role?.replace(/_/g, ' ') }}</span>
      </p>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div v-for="stat in stats" :key="stat.label" class="bg-white rounded-xl border border-gray-200 p-4">
        <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">{{ stat.label }}</p>
        <p class="text-2xl font-bold mt-1" :class="stat.color">{{ stat.value }}</p>
      </div>
    </div>

    <!-- Action items -->
    <AppCard title="Pending Actions">
      <div v-if="loadingApps" class="flex justify-center py-8">
        <div class="animate-spin w-6 h-6 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
      <div v-else-if="!pendingApps.length" class="text-sm text-gray-500 text-center py-8">
        No pending actions at this time.
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="border-b border-gray-200">
            <tr>
              <th class="pb-2 text-left text-xs text-gray-500 font-semibold uppercase">Reference</th>
              <th class="pb-2 text-left text-xs text-gray-500 font-semibold uppercase">Street Name</th>
              <th class="pb-2 text-left text-xs text-gray-500 font-semibold uppercase">Status</th>
              <th class="pb-2 text-left text-xs text-gray-500 font-semibold uppercase">Date</th>
              <th class="pb-2 text-left text-xs text-gray-500 font-semibold uppercase">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="app in pendingApps" :key="app.id" class="hover:bg-gray-50">
              <td class="py-2 font-mono text-xs text-gray-600">{{ app.reference_number || `#${app.id}` }}</td>
              <td class="py-2 font-medium text-gray-900">{{ app.proposed_street_name }}</td>
              <td class="py-2"><StatusBadge :status="app.status" /></td>
              <td class="py-2 text-gray-500 text-xs">{{ formatDate(app.updated_at || app.created_at) }}</td>
              <td class="py-2">
                <RouterLink :to="`/staff/applications/${app.id}`" class="text-blue-600 hover:text-blue-700 font-medium text-xs">
                  Review →
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <template #footer>
        <RouterLink to="/staff/applications" class="text-sm text-blue-600 hover:text-blue-700 font-medium">
          View all applications →
        </RouterLink>
      </template>
    </AppCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { applicationApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import AppCard from '@/components/AppCard.vue'
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

const ROLE_PENDING_STATUS: Record<string, string[]> = {
  finance: ['awaiting_stage_a_payment', 'awaiting_stage_c_payment', 'awaiting_renewal_payment'],
  naming_committee: ['under_naming_committee_review'],
  committee_chairman: ['awaiting_chairman_approval', 'stage_c_confirmed'],
}

const pendingStatuses = computed(() => ROLE_PENDING_STATUS[auth.user?.role ?? ''] ?? [])

const pendingApps = computed(() =>
  allApps.value.filter((a) => pendingStatuses.value.includes(a.status)),
)

const stats = computed(() => {
  const counts: Record<string, number> = {}
  allApps.value.forEach((a) => { counts[a.status] = (counts[a.status] ?? 0) + 1 })
  return [
    { label: 'Total', value: allApps.value.length, color: 'text-gray-900' },
    { label: 'Pending Action', value: pendingApps.value.length, color: 'text-yellow-600' },
    { label: 'Approved', value: (counts['approved_by_chairman'] ?? 0) + (counts['certificate_issued'] ?? 0), color: 'text-green-600' },
    { label: 'Rejected', value: (counts['rejected_by_committee'] ?? 0) + (counts['rejected_by_chairman'] ?? 0), color: 'text-red-600' },
  ]
})

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-NG', { day: 'numeric', month: 'short', year: 'numeric' })
}

onMounted(async () => {
  loadingApps.value = true
  try {
    const { data } = await applicationApi.list()
    allApps.value = Array.isArray(data) ? data : data.results ?? []
  } finally {
    loadingApps.value = false
  }
})
</script>
