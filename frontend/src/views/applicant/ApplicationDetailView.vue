<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <!-- Loading -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-32 gap-3">
      <div class="w-10 h-10 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
      <p class="text-sm text-slate-500">Loading application…</p>
    </div>

    <template v-else-if="application">

      <!-- Page header band -->
      <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
        <div class="max-w-5xl mx-auto px-4 sm:px-6 py-5">
          <nav class="flex items-center gap-2 text-xs text-slate-400 mb-3">
            <RouterLink to="/applications" class="hover:text-emerald-400 transition-colors">My Applications</RouterLink>
            <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
            <span class="text-slate-300 font-mono">{{ application.reference_number || `APP-${application.id}` }}</span>
          </nav>
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div class="flex items-center gap-3 flex-wrap">
                <h1 class="text-white text-xl font-bold tracking-tight">{{ application.proposed_street_name }}</h1>
                <StatusBadge :status="application.status" />
              </div>
              <p class="text-slate-400 text-sm mt-1">
                {{ application.street_type_name }} &nbsp;·&nbsp; Submitted {{ formatDate(application.created_at) }}
              </p>
            </div>
            <!-- Action buttons -->
            <div class="flex flex-wrap gap-2">
              <RouterLink v-if="application.status === 'draft' && !allDocsUploaded"
                          :to="`/applications/${application.id}/documents`"
                          class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white transition-all"
                          style="background: linear-gradient(135deg, #059669, #047857); box-shadow: 0 4px 14px rgba(5,150,105,0.35)">
                Upload Documents
              </RouterLink>
              <RouterLink v-if="application.status === 'awaiting_document_resubmission'"
                          :to="`/applications/${application.id}/documents`"
                          class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white transition-all"
                          style="background: linear-gradient(135deg, #dc2626, #b91c1c); box-shadow: 0 4px 14px rgba(220,38,38,0.35)">
                Re-upload Documents
              </RouterLink>
              <button v-if="application.status === 'draft' && allDocsUploaded"
                      :disabled="actionLoading"
                      class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60"
                      style="background: linear-gradient(135deg, #0284c7, #0369a1); box-shadow: 0 4px 14px rgba(2,132,199,0.35)"
                      @click="handleRequestPayment">
                {{ actionLoading ? 'Processing…' : 'Proceed to Payment' }}
              </button>
              <RouterLink v-if="PAYMENT_STATUSES.includes(application.status)"
                          :to="`/applications/${application.id}/payment`"
                          class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white transition-all"
                          style="background: linear-gradient(135deg, #0284c7, #0369a1); box-shadow: 0 4px 14px rgba(2,132,199,0.35)">
                Proceed to Payment
              </RouterLink>
              <span v-if="application.status === 'awaiting_stage_a_payment_confirmation'"
                    class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold"
                    style="background: rgba(234,179,8,0.1); color: #92400e; border: 1px solid rgba(234,179,8,0.3)">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/>
                </svg>
                Payment Submitted
              </span>
              <button v-if="RENEWAL_STATUSES.includes(application.status)" :disabled="actionLoading"
                      class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-slate-700 border border-slate-200 bg-white hover:bg-slate-50 transition-all disabled:opacity-60"
                      @click="handleRenewal">
                Renew Certificate
              </button>
              <button v-if="application.status === 'draft'" :disabled="actionLoading"
                      class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-red-600 border border-red-200 bg-white hover:bg-red-50 transition-all disabled:opacity-60"
                      @click="handleWithdraw">
                Withdraw
              </button>
            </div>
          </div>

          <!-- Alerts -->
          <div v-if="actionError" class="mt-4 flex items-start gap-3 rounded-xl border border-red-300/40 bg-red-500/10 p-3.5">
            <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
            </svg>
            <p class="text-sm text-red-300">{{ actionError }}</p>
          </div>
          <div v-if="actionSuccess" class="mt-4 flex items-start gap-3 rounded-xl border border-emerald-400/30 bg-emerald-500/10 p-3.5">
            <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/>
            </svg>
            <p class="text-sm text-emerald-300">{{ actionSuccess }}</p>
          </div>
        </div>
      </div>

      <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">

          <!-- Left: details + documents -->
          <div class="lg:col-span-2 space-y-4">

            <!-- Application details card -->
            <div class="rounded-2xl overflow-hidden"
                 style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Application Details</h2>
              </div>
              <dl class="p-5 grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Proposed Name</dt>
                  <dd class="text-sm font-semibold text-slate-900">{{ application.proposed_street_name }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Street Type</dt>
                  <dd class="text-sm text-slate-700">{{ application.street_type_name }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Ward</dt>
                  <dd class="text-sm text-slate-700">{{ application.ward_display || '—' }}</dd>
                </div>
                <div class="sm:col-span-2">
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Location Description</dt>
                  <dd class="text-sm text-slate-700 leading-relaxed whitespace-pre-line">{{ application.location_description }}</dd>
                </div>
                <div v-if="application.committee_remarks" class="sm:col-span-2 rounded-xl p-4"
                     style="background: rgba(139,92,246,0.05); border: 1px solid rgba(139,92,246,0.15)">
                  <dt class="text-xs font-semibold uppercase tracking-wider mb-1" style="color: #7c3aed">Committee Remarks</dt>
                  <dd class="text-sm italic" style="color: #5b21b6">{{ application.committee_remarks }}</dd>
                </div>
                <div v-if="application.chairman_remarks" class="sm:col-span-2 rounded-xl p-4"
                     style="background: rgba(5,150,105,0.05); border: 1px solid rgba(5,150,105,0.15)">
                  <dt class="text-xs font-semibold uppercase tracking-wider mb-1" style="color: #059669">Chairman Remarks</dt>
                  <dd class="text-sm italic" style="color: #047857">{{ application.chairman_remarks }}</dd>
                </div>
              </dl>
            </div>

            <!-- Documents card -->
            <div class="rounded-2xl overflow-hidden"
                 style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4 flex items-center justify-between" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Documents</h2>
                <RouterLink :to="`/applications/${application.id}/documents`"
                            class="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex items-center gap-1">
                  Manage
                  <ChevronRightIcon class="w-3.5 h-3.5" />
                </RouterLink>
              </div>
              <div v-if="!documents.length" class="flex flex-col items-center py-10 gap-2">
                <DocumentIcon class="w-8 h-8 text-slate-300" />
                <p class="text-sm text-slate-500">No documents uploaded yet.</p>
                <RouterLink :to="`/applications/${application.id}/documents`"
                            class="mt-1 text-xs font-semibold text-emerald-600 hover:text-emerald-700">
                  Upload documents →
                </RouterLink>
              </div>
              <ul v-else class="divide-y divide-slate-50">
                <li v-for="doc in documents" :key="doc.id"
                    class="flex items-center justify-between px-5 py-3.5">
                  <div class="flex items-center gap-3 min-w-0">
                    <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                         style="background: rgba(5,150,105,0.07); border: 1px solid rgba(5,150,105,0.12)">
                      <DocumentIcon class="w-4 h-4" style="color: #059669" />
                    </div>
                    <div class="min-w-0">
                      <p class="text-sm font-medium text-slate-900 truncate">{{ doc.document_type_display || doc.document_type }}</p>
                      <p class="text-xs mt-0.5" :class="doc.is_verified ? 'text-emerald-600' : 'text-slate-400'">
                        {{ doc.is_verified ? 'Verified' : 'Pending verification' }}
                      </p>
                    </div>
                  </div>
                  <a v-if="doc.file" :href="doc.file" target="_blank"
                     class="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex-shrink-0 ml-3">
                    View
                  </a>
                </li>
              </ul>
            </div>

          </div>

          <!-- Right: timeline -->
          <div>
            <div class="rounded-2xl overflow-hidden sticky top-4"
                 style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Status History</h2>
              </div>
              <div v-if="!history.length" class="flex flex-col items-center py-10 gap-2">
                <ClockIcon class="w-8 h-8 text-slate-300" />
                <p class="text-xs text-slate-400">No history yet.</p>
              </div>
              <ol v-else class="p-5 space-y-4">
                <li v-for="(entry, i) in history" :key="i" class="flex gap-3">
                  <div class="flex flex-col items-center">
                    <div class="w-2.5 h-2.5 rounded-full flex-shrink-0 mt-1"
                         :style="i === 0 ? 'background: #059669' : 'background: #cbd5e1'"></div>
                    <div v-if="i < history.length - 1" class="w-px flex-1 mt-1" style="background: #e2e8f0; min-height: 20px"></div>
                  </div>
                  <div class="pb-2 min-w-0">
                    <StatusBadge :status="entry.new_status || entry.status || ''" />
                    <p class="text-xs text-slate-400 mt-1">{{ formatDate(entry.created_at || entry.timestamp) }}</p>
                    <p v-if="entry.remarks || entry.comment" class="text-xs text-slate-600 mt-1 italic leading-snug">
                      "{{ entry.remarks || entry.comment }}"
                    </p>
                  </div>
                </li>
              </ol>
            </div>
          </div>

        </div>
      </div>
    </template>

    <div v-else class="flex flex-col items-center justify-center py-32 gap-2">
      <p class="text-slate-500 text-sm">Application not found.</p>
      <RouterLink to="/applications" class="text-xs font-semibold text-emerald-600 hover:text-emerald-700">← Back to applications</RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink, useRouter } from 'vue-router'
import { DocumentIcon, ChevronRightIcon, ClockIcon } from '@heroicons/vue/24/outline'
import { applicationApi, documentApi } from '@/services/api'
import StatusBadge from '@/components/StatusBadge.vue'

const REQUIRED_DOC_TYPES = [
  'nin_verification_slip',
  'passport_photograph',
  'royal_fathers_recognition_letter',
  'survey_property_document',
]

interface Application {
  id: number
  reference_number?: string
  proposed_street_name: string
  street_type_name?: string
  ward_display?: string
  location_description: string
  status: string
  created_at: string
  committee_remarks?: string
  chairman_remarks?: string
}
interface Document { id: number; document_type: string; document_type_display?: string; file?: string; is_verified?: boolean }
interface HistoryEntry { new_status?: string; status?: string; created_at?: string; timestamp?: string; remarks?: string; comment?: string }

const PAYMENT_STATUSES = ['awaiting_stage_a_payment', 'awaiting_stage_c_payment', 'awaiting_renewal_payment']
const RENEWAL_STATUSES = ['certificate_issued', 'expired', 'renewed']

const route = useRoute()
const router = useRouter()
const application = ref<Application | null>(null)
const documents = ref<Document[]>([])
const history = ref<HistoryEntry[]>([])
const loading = ref(false)
const actionLoading = ref(false)
const actionError = ref('')
const actionSuccess = ref('')

const allDocsUploaded = computed(() =>
  REQUIRED_DOC_TYPES.every(type => documents.value.some(d => d.document_type === type))
)

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

async function handleRequestPayment() {
  actionError.value = ''
  actionLoading.value = true
  try {
    await applicationApi.requestPayment(application.value!.id)
    router.push(`/applications/${application.value!.id}/payment`)
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    actionError.value = e.response?.data?.detail || 'Failed to proceed to payment.'
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
    await applicationApi.renew(application.value!.id)
    actionSuccess.value = 'Renewal request submitted.'
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
