<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <div v-if="loading" class="flex flex-col items-center justify-center py-32 gap-3">
      <div class="w-10 h-10 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
      <p class="text-sm text-slate-500">Loading application…</p>
    </div>

    <template v-else-if="application">

      <!-- Header band -->
      <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 py-5">
          <nav class="flex items-center gap-2 text-xs text-slate-400 mb-3">
            <RouterLink to="/staff/applications" class="hover:text-emerald-400 transition-colors">Applications</RouterLink>
            <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
            <span class="text-slate-300 font-mono">{{ application.reference_number || `APP-${application.id}` }}</span>
          </nav>
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div class="flex items-center gap-3 flex-wrap">
                <h1 class="text-white text-xl font-bold tracking-tight">{{ application.proposed_street_name }}</h1>
                <StatusBadge :status="application.status" />
              </div>
              <p class="text-slate-400 text-sm mt-1">
                {{ application.street_type_name }} &nbsp;·&nbsp; {{ formatDate(application.created_at) }}
              </p>
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

      <div class="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">

          <!-- Left: details, docs, payments -->
          <div class="lg:col-span-2 space-y-4">

            <!-- Applicant info -->
            <div class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Applicant Information</h2>
              </div>
              <dl class="p-5 grid grid-cols-2 gap-5 text-sm">
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Full Name</dt>
                  <dd class="text-slate-900 font-semibold">{{ application.applicant_name || '—' }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Email</dt>
                  <dd class="text-slate-700">{{ application.applicant_email || '—' }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Phone</dt>
                  <dd class="text-slate-700">{{ application.applicant_phone || '—' }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Street Type</dt>
                  <dd class="text-slate-700">{{ application.street_type_name }}</dd>
                </div>
                <div class="col-span-2">
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Location Description</dt>
                  <dd class="text-slate-700 leading-relaxed whitespace-pre-line">{{ application.location_description }}</dd>
                </div>
              </dl>
            </div>

            <!-- Documents -->
            <div class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Documents</h2>
              </div>
              <div v-if="!documents.length" class="flex flex-col items-center py-10 gap-2">
                <DocumentIcon class="w-8 h-8 text-slate-300" />
                <p class="text-sm text-slate-500">No documents uploaded.</p>
              </div>
              <ul v-else class="divide-y divide-slate-50">
                <li v-for="doc in documents" :key="doc.id" class="flex items-center gap-4 px-5 py-3.5">
                  <div class="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
                       :style="doc.is_verified ? 'background: rgba(5,150,105,0.08); border: 1px solid rgba(5,150,105,0.18)' : 'background: #f8fafc; border: 1px solid #e2e8f0'">
                    <DocumentIcon class="w-4 h-4" :style="doc.is_verified ? 'color: #059669' : 'color: #94a3b8'" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-semibold text-slate-900 truncate">{{ doc.document_type_display || doc.document_type }}</p>
                    <p class="text-xs mt-0.5" :class="doc.is_verified ? 'text-emerald-600' : 'text-slate-400'">
                      {{ doc.is_verified ? '✓ Verified' : 'Pending verification' }}
                    </p>
                  </div>
                  <div class="flex items-center gap-3 flex-shrink-0">
                    <a v-if="doc.file" :href="doc.file" target="_blank"
                       class="text-xs font-semibold text-emerald-600 hover:text-emerald-700">View</a>
                    <button v-if="!doc.is_verified && (auth.isFinance || auth.isNamingCommittee || auth.isChairman)"
                            class="text-xs font-semibold text-blue-600 hover:text-blue-700"
                            @click="verifyDoc(doc.id)">
                      Verify
                    </button>
                  </div>
                </li>
              </ul>
            </div>

            <!-- Payments -->
            <div class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Payment Records</h2>
              </div>
              <div v-if="!payments.length" class="flex flex-col items-center py-10 gap-2">
                <CurrencyDollarIcon class="w-8 h-8 text-slate-300" />
                <p class="text-sm text-slate-500">No payment records.</p>
              </div>
              <ul v-else class="divide-y divide-slate-50">
                <li v-for="p in payments" :key="p.id" class="px-5 py-4">
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <p class="text-sm font-semibold text-slate-900 font-mono">{{ p.payment_reference || 'No reference' }}</p>
                      <p class="text-xs text-slate-500 mt-0.5">
                        {{ p.bank_name }} · {{ formatDate(p.payment_date ?? '') }} · ₦{{ formatAmount(p.amount_submitted) }}
                      </p>
                      <p v-if="p.finance_remarks" class="text-xs text-slate-600 mt-1 italic">"{{ p.finance_remarks }}"</p>
                    </div>
                    <span class="px-3 py-1 rounded-full text-xs font-semibold flex-shrink-0"
                          :class="paymentStatusClass(p.status)">{{ p.status }}</span>
                  </div>
                </li>
              </ul>
            </div>

          </div>

          <!-- Right: action panels + history -->
          <div class="space-y-4">

            <!-- Finance: confirm payment -->
            <div v-if="auth.isFinance && FINANCE_PAYMENT_STATUSES.includes(application.status)"
                 class="rounded-2xl overflow-hidden"
                 style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Confirm Payment</h2>
              </div>
              <form @submit.prevent="handleConfirmPayment" class="p-5 space-y-4" novalidate>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-1.5">Decision <span class="text-red-500">*</span></label>
                  <select v-model="financeForm.decision" required class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
                    <option value="">Select…</option>
                    <option value="confirm">Confirm Payment</option>
                    <option value="reject">Reject Payment</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-1.5">Remarks</label>
                  <textarea v-model="financeForm.finance_remarks" rows="3" placeholder="Optional remarks…"
                            class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"/>
                </div>
                <button type="submit" :disabled="actionLoading || !financeForm.decision"
                        class="w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60"
                        style="background: linear-gradient(135deg, #059669, #047857)">
                  {{ actionLoading ? 'Processing…' : 'Submit Decision' }}
                </button>
              </form>
            </div>

            <!-- Finance: issue certificate -->
            <div v-if="auth.isFinance && application.status === 'stage_c_confirmed'"
                 class="rounded-2xl overflow-hidden"
                 style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Issue Certificate</h2>
              </div>
              <div class="p-5">
                <p class="text-sm text-slate-600 mb-4">Stage C payment confirmed. Issue the official street name certificate.</p>
                <button :disabled="actionLoading"
                        class="w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60"
                        style="background: linear-gradient(135deg, #059669, #047857)"
                        @click="handleIssueCertificate">
                  {{ actionLoading ? 'Processing…' : 'Issue Certificate' }}
                </button>
              </div>
            </div>

            <!-- Naming committee review -->
            <div v-if="auth.isNamingCommittee && application.status === 'under_naming_committee_review'"
                 class="rounded-2xl overflow-hidden"
                 style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Committee Review</h2>
              </div>
              <form @submit.prevent="handleCommitteeReview" class="p-5 space-y-4" novalidate>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-1.5">Decision <span class="text-red-500">*</span></label>
                  <select v-model="committeeForm.decision" required class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
                    <option value="">Select…</option>
                    <option value="approved">Approve</option>
                    <option value="rejected">Reject</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-1.5">Remarks <span class="text-red-500">*</span></label>
                  <textarea v-model="committeeForm.remarks" rows="4" required placeholder="Provide your review remarks…"
                            class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"/>
                </div>
                <button type="submit" :disabled="actionLoading || !committeeForm.decision || !committeeForm.remarks"
                        class="w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60"
                        style="background: linear-gradient(135deg, #059669, #047857)">
                  {{ actionLoading ? 'Submitting…' : 'Submit Review' }}
                </button>
              </form>
            </div>

            <!-- Chairman approval -->
            <div v-if="auth.isChairman && application.status === 'awaiting_chairman_approval'"
                 class="rounded-2xl overflow-hidden"
                 style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Chairman Approval</h2>
              </div>
              <form @submit.prevent="handleChairmanApproval" class="p-5 space-y-4" novalidate>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-1.5">Decision <span class="text-red-500">*</span></label>
                  <select v-model="chairmanForm.decision" required class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
                    <option value="">Select…</option>
                    <option value="approved">Approve</option>
                    <option value="rejected">Reject</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-1.5">Remarks</label>
                  <textarea v-model="chairmanForm.remarks" rows="4" placeholder="Optional remarks…"
                            class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"/>
                </div>
                <button type="submit" :disabled="actionLoading || !chairmanForm.decision"
                        class="w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60"
                        style="background: linear-gradient(135deg, #059669, #047857)">
                  {{ actionLoading ? 'Submitting…' : 'Submit Decision' }}
                </button>
              </form>
            </div>

            <!-- Status timeline -->
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
                    <p class="text-xs text-slate-400 mt-1">{{ formatDate(entry.created_at || entry.timestamp || '') }}</p>
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
      <RouterLink to="/staff/applications" class="text-xs font-semibold text-emerald-600">← Back to applications</RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { DocumentIcon, ChevronRightIcon, ClockIcon, CurrencyDollarIcon } from '@heroicons/vue/24/outline'
import { applicationApi, documentApi, paymentApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import StatusBadge from '@/components/StatusBadge.vue'

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
    pending: 'bg-amber-100 text-amber-700',
    confirmed: 'bg-emerald-100 text-emerald-700',
    rejected: 'bg-red-100 text-red-700',
  }
  return m[status] ?? 'bg-slate-100 text-slate-600'
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
    const pendingPayment = payments.value.find(p => p.status === 'pending')
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
    await import('@/services/api').then(({ documentApi: da }) => da.verify(docId, { is_verified: true }))
    actionSuccess.value = 'Document verified.'
    await load()
  } catch {
    actionError.value = 'Failed to verify document.'
  }
}

onMounted(load)
</script>
