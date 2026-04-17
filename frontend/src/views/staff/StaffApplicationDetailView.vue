<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <nav class="text-sm text-gray-500 mb-6 flex items-center gap-2">
      <RouterLink to="/staff/applications" class="hover:text-blue-600">Applications</RouterLink>
      <span>/</span>
      <span class="text-gray-900">{{ application?.reference_number || `#${route.params.id}` }}</span>
    </nav>

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
              &nbsp;·&nbsp; {{ application.street_type_name }}
              &nbsp;·&nbsp; {{ formatDate(application.created_at) }}
            </p>
          </div>
        </div>

        <!-- Action feedback -->
        <div v-if="actionError" class="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{{ actionError }}</div>
        <div v-if="actionSuccess" class="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">{{ actionSuccess }}</div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <!-- Left column -->
        <div class="lg:col-span-2 space-y-5">

          <!-- Applicant info -->
          <AppCard title="Applicant Information">
            <dl class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt class="text-xs text-gray-500 uppercase font-semibold">Name</dt>
                <dd class="mt-1 text-gray-900">{{ application.applicant_name || '—' }}</dd>
              </div>
              <div>
                <dt class="text-xs text-gray-500 uppercase font-semibold">Email</dt>
                <dd class="mt-1 text-gray-900">{{ application.applicant_email || '—' }}</dd>
              </div>
              <div>
                <dt class="text-xs text-gray-500 uppercase font-semibold">Phone</dt>
                <dd class="mt-1 text-gray-900">{{ application.applicant_phone || '—' }}</dd>
              </div>
              <div>
                <dt class="text-xs text-gray-500 uppercase font-semibold">Street Type</dt>
                <dd class="mt-1 text-gray-900">{{ application.street_type_name }}</dd>
              </div>
              <div class="col-span-2">
                <dt class="text-xs text-gray-500 uppercase font-semibold">Location</dt>
                <dd class="mt-1 text-gray-900 whitespace-pre-line">{{ application.location_description }}</dd>
              </div>
            </dl>
          </AppCard>

          <!-- Documents -->
          <AppCard title="Documents">
            <div v-if="!documents.length" class="text-sm text-gray-500 py-4 text-center">No documents uploaded.</div>
            <ul v-else class="space-y-2">
              <li
                v-for="doc in documents"
                :key="doc.id"
                class="flex items-center justify-between p-3 bg-gray-50 rounded-lg text-sm border border-gray-100"
              >
                <div class="flex items-center gap-2">
                  <DocumentIcon class="w-4 h-4 text-gray-400" />
                  <span>{{ doc.document_type_display || doc.document_type }}</span>
                  <span v-if="doc.is_verified" class="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full">Verified</span>
                </div>
                <div class="flex items-center gap-2">
                  <a v-if="doc.file" :href="doc.file" target="_blank" class="text-blue-600 text-xs hover:underline">View</a>
                  <button
                    v-if="auth.isFinance || auth.isNamingCommittee || auth.isChairman"
                    class="text-xs text-green-700 hover:underline"
                    @click="verifyDoc(doc.id)"
                  >
                    Verify
                  </button>
                </div>
              </li>
            </ul>
          </AppCard>

          <!-- Payment records -->
          <AppCard title="Payment Records">
            <div v-if="!payments.length" class="text-sm text-gray-500 py-4 text-center">No payment records.</div>
            <ul v-else class="space-y-3">
              <li v-for="p in payments" :key="p.id" class="p-3 bg-gray-50 rounded-lg border border-gray-100 text-sm">
                <div class="flex justify-between items-start">
                  <div>
                    <p class="font-medium text-gray-900">{{ p.payment_reference || 'No reference' }}</p>
                    <p class="text-xs text-gray-500 mt-0.5">{{ p.bank_name }} · {{ formatDate(p.payment_date ?? '') }} · ₦{{ formatAmount(p.amount_submitted) }}</p>
                    <p v-if="p.finance_remarks" class="text-xs text-gray-600 mt-1 italic">Remark: {{ p.finance_remarks }}</p>
                  </div>
                  <span :class="paymentStatusClass(p.status)" class="text-xs px-2 py-0.5 rounded-full font-medium capitalize">{{ p.status }}</span>
                </div>
              </li>
            </ul>
          </AppCard>
        </div>

        <!-- Right column: action panel + history -->
        <div class="space-y-5">
          <!-- Action panel: Finance confirm payment -->
          <AppCard
            v-if="auth.isFinance && FINANCE_PAYMENT_STATUSES.includes(application.status)"
            title="Confirm Payment"
          >
            <form @submit.prevent="handleConfirmPayment" class="space-y-3">
              <div>
                <label class="form-label text-xs">Decision</label>
                <select v-model="financeForm.decision" required class="form-input text-sm">
                  <option value="">Select…</option>
                  <option value="confirm">Confirm Payment</option>
                  <option value="reject">Reject Payment</option>
                </select>
              </div>
              <div>
                <label class="form-label text-xs">Remarks</label>
                <textarea v-model="financeForm.finance_remarks" rows="3" class="form-input text-sm resize-none" placeholder="Optional remarks…" />
              </div>
              <button type="submit" :disabled="actionLoading" class="btn-primary w-full text-sm">
                {{ actionLoading ? 'Processing…' : 'Submit Decision' }}
              </button>
            </form>
          </AppCard>

          <!-- Action panel: Finance issue certificate -->
          <AppCard v-if="auth.isFinance && application.status === 'stage_c_confirmed'" title="Issue Certificate">
            <p class="text-sm text-gray-600 mb-3">Stage C payment is confirmed. You can now issue the street name certificate.</p>
            <button :disabled="actionLoading" class="btn-primary w-full text-sm" @click="handleIssueCertificate">
              {{ actionLoading ? 'Processing…' : 'Issue Certificate' }}
            </button>
          </AppCard>

          <!-- Action panel: Naming committee review -->
          <AppCard
            v-if="auth.isNamingCommittee && application.status === 'under_naming_committee_review'"
            title="Committee Review"
          >
            <form @submit.prevent="handleCommitteeReview" class="space-y-3">
              <div>
                <label class="form-label text-xs">Decision</label>
                <select v-model="committeeForm.decision" required class="form-input text-sm">
                  <option value="">Select…</option>
                  <option value="approved">Approve</option>
                  <option value="rejected">Reject</option>
                </select>
              </div>
              <div>
                <label class="form-label text-xs">Remarks <span class="text-red-500">*</span></label>
                <textarea v-model="committeeForm.remarks" rows="4" required class="form-input text-sm resize-none" placeholder="Provide your review remarks…" />
              </div>
              <button type="submit" :disabled="actionLoading" class="btn-primary w-full text-sm">
                {{ actionLoading ? 'Submitting…' : 'Submit Review' }}
              </button>
            </form>
          </AppCard>

          <!-- Action panel: Chairman approval -->
          <AppCard
            v-if="auth.isChairman && application.status === 'awaiting_chairman_approval'"
            title="Chairman Approval"
          >
            <form @submit.prevent="handleChairmanApproval" class="space-y-3">
              <div>
                <label class="form-label text-xs">Decision</label>
                <select v-model="chairmanForm.decision" required class="form-input text-sm">
                  <option value="">Select…</option>
                  <option value="approved">Approve</option>
                  <option value="rejected">Reject</option>
                </select>
              </div>
              <div>
                <label class="form-label text-xs">Remarks</label>
                <textarea v-model="chairmanForm.remarks" rows="4" class="form-input text-sm resize-none" placeholder="Optional remarks…" />
              </div>
              <button type="submit" :disabled="actionLoading" class="btn-primary w-full text-sm">
                {{ actionLoading ? 'Submitting…' : 'Submit Decision' }}
              </button>
            </form>
          </AppCard>

          <!-- Status history -->
          <AppCard title="Status History">
            <div v-if="!history.length" class="text-sm text-gray-500">No history.</div>
            <ol v-else class="relative border-l border-gray-200 ml-3 space-y-4">
              <li v-for="(entry, i) in history" :key="i" class="ml-4">
                <div class="absolute w-3 h-3 bg-blue-600 rounded-full -left-1.5 mt-1 border-2 border-white" />
                <StatusBadge :status="entry.new_status || entry.status || ''" class="mb-0.5" />
                <p class="text-xs text-gray-500 mt-0.5">{{ formatDate(entry.created_at || entry.timestamp || '') }}</p>
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
import { applicationApi, documentApi, paymentApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import StatusBadge from '@/components/StatusBadge.vue'
import AppCard from '@/components/AppCard.vue'

interface Application {
  id: number
  reference_number?: string
  proposed_street_name: string
  street_type?: number
  street_type_name?: string
  location_description: string
  status: string
  created_at: string
  updated_at?: string
  applicant_name?: string
  applicant_email?: string
  applicant_phone?: string
  committee_remarks?: string
  chairman_remarks?: string
}

interface Doc { id: number; document_type: string; document_type_display?: string; file?: string; is_verified?: boolean }
interface Payment { id: number; payment_reference?: string; bank_name?: string; payment_date?: string; status: string; amount_submitted?: number; finance_remarks?: string }
interface HistoryEntry { new_status?: string; status?: string; created_at?: string; timestamp?: string; remarks?: string; comment?: string }

const FINANCE_PAYMENT_STATUSES = ['awaiting_stage_a_payment', 'awaiting_stage_c_payment', 'awaiting_renewal_payment']

const route = useRoute()
const auth = useAuthStore()
const application = ref<Application | null>(null)
const documents = ref<Doc[]>([])
const payments = ref<Payment[]>([])
const history = ref<HistoryEntry[]>([])
const loading = ref(false)
const actionLoading = ref(false)
const actionError = ref('')
const actionSuccess = ref('')

const financeForm = ref({ decision: '', finance_remarks: '' })
const committeeForm = ref({ decision: '', remarks: '' })
const chairmanForm = ref({ decision: '', remarks: '' })

function formatDate(d: string) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-NG', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatAmount(n?: number) {
  if (!n) return '0.00'
  return new Intl.NumberFormat('en-NG', { minimumFractionDigits: 2 }).format(n)
}

function paymentStatusClass(status: string) {
  const m: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-700',
    confirmed: 'bg-green-100 text-green-700',
    rejected: 'bg-red-100 text-red-700',
  }
  return m[status] ?? 'bg-gray-100 text-gray-600'
}

async function load() {
  loading.value = true
  try {
    const [appRes, docRes, payRes, histRes] = await Promise.all([
      applicationApi.get(route.params.id as string),
      documentApi.list(route.params.id as string).catch(() => ({ data: [] })),
      paymentApi.listForApplication(route.params.id as string).catch(() => ({ data: [] })),
      applicationApi.getHistory(route.params.id as string).catch(() => ({ data: [] })),
    ])
    application.value = appRes.data
    documents.value = Array.isArray(docRes.data) ? docRes.data : docRes.data.results ?? []
    payments.value = Array.isArray(payRes.data) ? payRes.data : payRes.data.results ?? []
    history.value = Array.isArray(histRes.data) ? histRes.data : histRes.data.results ?? []
  } finally {
    loading.value = false
  }
}

async function handleConfirmPayment() {
  actionError.value = ''
  actionSuccess.value = ''
  actionLoading.value = true
  try {
    const pendingPayment = payments.value.find((p) => p.status === 'pending')
    if (!pendingPayment) throw new Error('No pending payment found.')
    await paymentApi.confirmPayment(pendingPayment.id, {
      status: financeForm.value.decision === 'confirm' ? 'confirmed' : 'rejected',
      finance_remarks: financeForm.value.finance_remarks,
    })
    actionSuccess.value = 'Payment decision recorded.'
    financeForm.value = { decision: '', finance_remarks: '' }
    await load()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; message?: string }
    actionError.value = e.response?.data?.detail || e.message || 'Failed.'
  } finally {
    actionLoading.value = false
  }
}

async function handleIssueCertificate() {
  actionError.value = ''
  actionLoading.value = true
  try {
    await applicationApi.issueCertificate(application.value!.id)
    actionSuccess.value = 'Certificate issued successfully.'
    await load()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    actionError.value = e.response?.data?.detail || 'Failed to issue certificate.'
  } finally {
    actionLoading.value = false
  }
}

async function handleCommitteeReview() {
  actionError.value = ''
  actionSuccess.value = ''
  actionLoading.value = true
  try {
    await applicationApi.committeeReview(application.value!.id, {
      decision: committeeForm.value.decision,
      remarks: committeeForm.value.remarks,
    })
    actionSuccess.value = 'Review submitted.'
    committeeForm.value = { decision: '', remarks: '' }
    await load()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    actionError.value = e.response?.data?.detail || 'Failed to submit review.'
  } finally {
    actionLoading.value = false
  }
}

async function handleChairmanApproval() {
  actionError.value = ''
  actionSuccess.value = ''
  actionLoading.value = true
  try {
    await applicationApi.chairmanApproval(application.value!.id, {
      decision: chairmanForm.value.decision,
      remarks: chairmanForm.value.remarks,
    })
    actionSuccess.value = 'Decision recorded.'
    chairmanForm.value = { decision: '', remarks: '' }
    await load()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    actionError.value = e.response?.data?.detail || 'Failed to submit decision.'
  } finally {
    actionLoading.value = false
  }
}

async function verifyDoc(docId: number) {
  try {
    await import('@/services/api').then(({ documentApi: da }) =>
      da.verify(docId, { is_verified: true }),
    )
    actionSuccess.value = 'Document verified.'
    await load()
  } catch {
    actionError.value = 'Failed to verify document.'
  }
}

onMounted(load)
</script>
