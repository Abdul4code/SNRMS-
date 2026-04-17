<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Breadcrumb -->
    <nav class="text-sm text-gray-500 mb-6 flex items-center gap-2">
      <RouterLink to="/applications" class="hover:text-blue-600">My Applications</RouterLink>
      <span>/</span>
      <span class="text-gray-900">{{ application?.reference_number || `#${route.params.id}` }}</span>
    </nav>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-16">
      <div class="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" />
    </div>

    <template v-else-if="application">
      <!-- Header -->
      <div class="bg-white rounded-xl border border-gray-200 p-6 mb-5">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div class="flex items-center gap-3 mb-1">
              <h1 class="text-xl font-bold text-gray-900">{{ application.proposed_street_name }}</h1>
              <StatusBadge :status="application.status" />
            </div>
            <p class="text-sm text-gray-500">
              Ref: <span class="font-mono">{{ application.reference_number || `#${application.id}` }}</span>
              &nbsp;·&nbsp; Type: {{ application.street_type_name }}
              &nbsp;·&nbsp; Submitted {{ formatDate(application.created_at) }}
            </p>
          </div>

          <!-- Action buttons -->
          <div class="flex flex-wrap gap-2">
            <button
              v-if="application.status === 'draft'"
              :disabled="actionLoading"
              class="btn-primary"
              @click="handleSubmit"
            >
              Submit Application
            </button>
            <RouterLink
              v-if="PAYMENT_STATUSES.includes(application.status)"
              :to="`/applications/${application.id}/payment`"
              class="btn-primary"
            >
              Make Payment
            </RouterLink>
            <button
              v-if="RENEWAL_STATUSES.includes(application.status)"
              :disabled="actionLoading"
              class="btn-secondary"
              @click="handleRenewal"
            >
              Renew Certificate
            </button>
            <button
              v-if="application.status === 'draft'"
              :disabled="actionLoading"
              class="btn-danger"
              @click="handleWithdraw"
            >
              Withdraw
            </button>
          </div>
        </div>

        <div v-if="actionError" class="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {{ actionError }}
        </div>
        <div v-if="actionSuccess" class="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
          {{ actionSuccess }}
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <!-- Left: Details -->
        <div class="lg:col-span-2 space-y-5">
          <!-- Application details -->
          <AppCard title="Application Details">
            <dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <dt class="text-xs font-medium text-gray-500 uppercase tracking-wide">Proposed Name</dt>
                <dd class="mt-1 text-sm text-gray-900">{{ application.proposed_street_name }}</dd>
              </div>
              <div>
                <dt class="text-xs font-medium text-gray-500 uppercase tracking-wide">Street Type</dt>
                <dd class="mt-1 text-sm text-gray-900">{{ application.street_type_name }}</dd>
              </div>
              <div class="sm:col-span-2">
                <dt class="text-xs font-medium text-gray-500 uppercase tracking-wide">Location Description</dt>
                <dd class="mt-1 text-sm text-gray-900 whitespace-pre-line">{{ application.location_description }}</dd>
              </div>
              <div v-if="application.committee_remarks">
                <dt class="text-xs font-medium text-gray-500 uppercase tracking-wide">Committee Remarks</dt>
                <dd class="mt-1 text-sm text-gray-700 italic">{{ application.committee_remarks }}</dd>
              </div>
              <div v-if="application.chairman_remarks">
                <dt class="text-xs font-medium text-gray-500 uppercase tracking-wide">Chairman Remarks</dt>
                <dd class="mt-1 text-sm text-gray-700 italic">{{ application.chairman_remarks }}</dd>
              </div>
            </dl>
          </AppCard>

          <!-- Documents -->
          <AppCard title="Documents">
            <div v-if="!documents.length" class="text-sm text-gray-500 py-4 text-center">
              No documents uploaded.
            </div>
            <ul v-else class="space-y-2">
              <li
                v-for="doc in documents"
                :key="doc.id"
                class="flex items-center justify-between p-3 bg-gray-50 rounded-lg text-sm"
              >
                <div class="flex items-center gap-2">
                  <DocumentIcon class="w-4 h-4 text-gray-400" />
                  <span class="text-gray-800">{{ doc.document_type_display || doc.document_type }}</span>
                </div>
                <a v-if="doc.file" :href="doc.file" target="_blank" class="text-blue-600 hover:underline text-xs">
                  View
                </a>
              </li>
            </ul>
            <div class="mt-3">
              <RouterLink :to="`/applications/${application.id}/documents`" class="btn-secondary text-xs">
                Manage Documents →
              </RouterLink>
            </div>
          </AppCard>
        </div>

        <!-- Right: Status timeline -->
        <div>
          <AppCard title="Status History">
            <div v-if="!history.length" class="text-sm text-gray-500">No history yet.</div>
            <ol v-else class="relative border-l border-gray-200 ml-3 space-y-4">
              <li v-for="(entry, i) in history" :key="i" class="ml-4">
                <div class="absolute w-3 h-3 bg-blue-600 rounded-full -left-1.5 mt-1 border-2 border-white" />
                <StatusBadge :status="entry.new_status || entry.status || ''" class="mb-0.5" />
                <p class="text-xs text-gray-500 mt-0.5">{{ formatDate(entry.created_at || entry.timestamp) }}</p>
                <p v-if="entry.remarks || entry.comment" class="text-xs text-gray-600 mt-0.5 italic">
                  {{ entry.remarks || entry.comment }}
                </p>
              </li>
            </ol>
          </AppCard>
        </div>
      </div>
    </template>

    <div v-else class="text-center py-16 text-gray-500">Application not found.</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { DocumentIcon } from '@heroicons/vue/24/outline'
import { applicationApi, documentApi } from '@/services/api'
import StatusBadge from '@/components/StatusBadge.vue'
import AppCard from '@/components/AppCard.vue'

interface Application {
  id: number
  reference_number?: string
  proposed_street_name: string
  street_type_name?: string
  location_description: string
  status: string
  created_at: string
  committee_remarks?: string
  chairman_remarks?: string
}

interface Document { id: number; document_type: string; document_type_display?: string; file?: string }
interface HistoryEntry { new_status?: string; status?: string; created_at?: string; timestamp?: string; remarks?: string; comment?: string }

const PAYMENT_STATUSES = ['awaiting_stage_a_payment', 'awaiting_stage_c_payment', 'awaiting_renewal_payment']
const RENEWAL_STATUSES = ['certificate_issued', 'expired', 'renewed']

const route = useRoute()
const application = ref<Application | null>(null)
const documents = ref<Document[]>([])
const history = ref<HistoryEntry[]>([])
const loading = ref(false)
const actionLoading = ref(false)
const actionError = ref('')
const actionSuccess = ref('')

async function loadApplication() {
  loading.value = true
  try {
    const [appRes, docsRes, histRes] = await Promise.all([
      applicationApi.get(route.params.id as string),
      documentApi.list(route.params.id as string).catch(() => ({ data: [] })),
      applicationApi.getHistory(route.params.id as string).catch(() => ({ data: [] })),
    ])
    application.value = appRes.data
    documents.value = Array.isArray(docsRes.data) ? docsRes.data : docsRes.data.results ?? []
    history.value = Array.isArray(histRes.data) ? histRes.data : histRes.data.results ?? []
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  actionError.value = ''
  actionSuccess.value = ''
  actionLoading.value = true
  try {
    const { data } = await applicationApi.submit(application.value!.id)
    application.value = data
    actionSuccess.value = 'Application submitted successfully.'
    await loadApplication()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    actionError.value = e.response?.data?.detail || 'Failed to submit application.'
  } finally {
    actionLoading.value = false
  }
}

async function handleWithdraw() {
  if (!confirm('Are you sure you want to withdraw this application?')) return
  actionLoading.value = true
  actionError.value = ''
  try {
    await applicationApi.withdraw(application.value!.id)
    actionSuccess.value = 'Application withdrawn.'
    await loadApplication()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    actionError.value = e.response?.data?.detail || 'Failed to withdraw.'
  } finally {
    actionLoading.value = false
  }
}

async function handleRenewal() {
  actionLoading.value = true
  actionError.value = ''
  try {
    // Submit as renewal — backend determines the renewal flow
    await applicationApi.submit(application.value!.id)
    actionSuccess.value = 'Renewal submitted.'
    await loadApplication()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    actionError.value = e.response?.data?.detail || 'Failed to submit renewal.'
  } finally {
    actionLoading.value = false
  }
}

function formatDate(d?: string) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-NG', { day: 'numeric', month: 'short', year: 'numeric' })
}

onMounted(loadApplication)
</script>
