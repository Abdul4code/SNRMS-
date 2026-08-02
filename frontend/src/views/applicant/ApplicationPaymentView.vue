<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <!-- Page header band -->
    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-2xl mx-auto px-4 sm:px-6 py-7">
        <nav class="flex items-center gap-2 text-xs text-slate-400 mb-4">
          <RouterLink to="/applications" class="hover:text-emerald-400 transition-colors">My Applications</RouterLink>
          <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
          <RouterLink :to="`/applications/${route.params.id}`" class="hover:text-emerald-400 transition-colors font-mono">
            APP-{{ route.params.id }}
          </RouterLink>
          <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
          <span class="text-slate-300">Payment</span>
        </nav>
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Payment</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">Application Payment</h1>
        <p class="text-slate-400 text-sm mt-1">Review the fees and submit your payment evidence</p>
      </div>
    </div>

    <div class="max-w-2xl mx-auto px-4 sm:px-6 py-8 space-y-5">

      <!-- Loading -->
      <div v-if="loading" class="flex flex-col items-center justify-center py-16 gap-3">
        <div class="w-9 h-9 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
        <p class="text-sm text-slate-500">Loading payment details…</p>
      </div>

      <template v-else>

        <!-- Fee breakdown card -->
        <div v-if="feeItems.length" class="rounded-2xl overflow-hidden"
             style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
          <div class="px-6 py-5 flex items-center gap-2.5" style="border-bottom: 1px solid #f1f5f9">
            <div class="w-7 h-7 rounded-lg flex items-center justify-center"
                 style="background: rgba(5,150,105,0.08); border: 1px solid rgba(5,150,105,0.15)">
              <BanknotesIcon class="w-4 h-4" style="color: #059669" />
            </div>
            <div>
              <h2 class="text-sm font-bold text-slate-900">{{ stageLabel }} — Fee Breakdown</h2>
              <p class="text-xs text-slate-500 mt-0">Pay securely online by card, bank transfer or USSD</p>
            </div>
          </div>
          <div class="px-5 py-4">
            <table class="w-full">
              <tbody>
                <tr v-for="item in feeItems" :key="item.component"
                    class="border-b border-slate-50 last:border-0">
                  <td class="py-3 text-sm text-slate-600">{{ item.label }}</td>
                  <td class="py-3 text-right text-sm font-semibold text-slate-900">₦{{ formatAmount(item.amount) }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr style="border-top: 2px solid #e2e8f0">
                  <td class="pt-4 font-bold text-slate-900">Total Due</td>
                  <td class="pt-4 text-right font-bold text-xl" style="color: #059669">₦{{ formatAmount(feeTotal) }}</td>
                </tr>
              </tfoot>
            </table>
          </div>
          <!-- Bank account info strip -->
          <div class="mx-5 mb-5 rounded-xl p-4" style="background: #f8fafc; border: 1px solid #e2e8f0">
            <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Payment Account Details</p>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <p class="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Bank</p>
                <p class="text-sm font-semibold text-slate-800 mt-0.5">Zenith Bank</p>
              </div>
              <div>
                <p class="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Account No.</p>
                <p class="text-sm font-mono font-semibold text-slate-800 mt-0.5">1234567890</p>
              </div>
              <div class="col-span-2">
                <p class="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Account Name</p>
                <p class="text-sm font-semibold text-slate-800 mt-0.5">Ibeju-Lekki Local Government Area — Street Naming</p>
              </div>
            </div>
          </div>
        </div>

        <!-- No fees available yet -->
        <div v-else-if="appStatus && appStatus !== 'draft'" class="rounded-2xl p-6 flex items-start gap-4"
             style="background: #fff; border: 1px solid #e2e8f0">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
               style="background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2)">
            <ClockIcon class="w-5 h-5" style="color: #d97706" />
          </div>
          <div>
            <p class="text-sm font-bold text-slate-800">Awaiting Finance Review</p>
            <p class="text-xs text-slate-500 mt-1 leading-relaxed">
              Your application is being reviewed. Once finance processes your submission,
              the payment amount will appear here and you'll be notified.
            </p>
          </div>
        </div>

        <!-- Existing payment records -->
        <div v-if="payments.length" class="rounded-2xl overflow-hidden"
             style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
          <div class="px-6 py-5" style="border-bottom: 1px solid #f1f5f9">
            <h2 class="text-sm font-bold text-slate-900">Payment Records</h2>
          </div>
          <ul class="divide-y divide-slate-50">
            <li v-for="p in payments" :key="p.id" class="flex items-center justify-between px-5 py-4 gap-4">
              <div class="min-w-0">
                <p class="text-sm font-semibold text-slate-900 font-mono">{{ p.payment_reference || 'Pending Reference' }}</p>
                <p class="text-xs text-slate-500 mt-0.5">
                  {{ p.bank_name }}{{ p.payment_date ? ' · ' + formatDate(p.payment_date) : '' }}
                </p>
                <p v-if="p.amount_submitted" class="text-xs font-semibold mt-0.5" style="color: #059669">
                  ₦{{ formatAmount(p.amount_submitted) }} submitted
                </p>
              </div>
              <div class="flex items-center gap-2 flex-shrink-0">
                <button v-if="p.status === 'confirmed' && p.receipt_serial"
                        @click="downloadReceipt(p.receipt_serial)"
                        class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white"
                        style="background:#059669">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                  Download Receipt
                </button>
                <span class="px-3 py-1 rounded-full text-xs font-bold"
                      :class="paymentStatusClass(p.status)">
                  {{ paymentStatusLabel(p.status) }}
                </span>
              </div>
            </li>
          </ul>
        </div>

        <!-- Rejection notice -->
        <div v-if="rejectedPayment" class="rounded-2xl p-4 flex items-start gap-3"
             style="background: #fef2f2; border: 1px solid rgba(220,38,38,0.25)">
          <svg class="w-5 h-5 flex-shrink-0 mt-0.5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
          </svg>
          <div>
            <p class="text-sm font-bold text-red-700">Payment Not Confirmed</p>
            <p class="text-xs text-red-500 mt-1">The Council Treasurer could not confirm this payment. Please re-submit with the correct details below.</p>
          </div>
        </div>

        <!-- Pay online (gateway) — shown when a payment is due -->
        <div v-if="pendingPayment" class="rounded-2xl overflow-hidden"
             style="background: #0f172a; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
          <div class="px-6 py-5">
            <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1">Fastest option</p>
            <h2 class="text-white text-sm font-bold">Pay online</h2>
            <p class="text-slate-400 text-xs mt-0.5">
              Pay by card, bank transfer or USSD. Your application advances automatically once payment succeeds — no waiting for manual confirmation.
            </p>
            <div v-if="onlineError" class="mt-3 text-xs text-red-300">{{ onlineError }}</div>
            <button
              @click="payOnline"
              :disabled="onlineBusy"
              class="mt-4 inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
              style="background:#059669">
              <svg v-if="onlineBusy" class="animate-spin w-4 h-4 opacity-80" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
              </svg>
              {{ onlineBusy ? 'Processing…' : `Pay ₦${formatAmount(pendingPayment.amount_expected)} online` }}
            </button>
            <p v-if="demoMode" class="text-[11px] text-slate-500 mt-2">
              Demo mode (no live gateway configured): clicking simulates a successful payment.
            </p>
          </div>
        </div>


        <!-- Back to application after teller submitted -->
        <div v-if="tellerSubmitted" class="rounded-2xl overflow-hidden"
             style="background: linear-gradient(135deg, #022c22, #064e3b); border: 1px solid rgba(52,211,153,0.2)">
          <div class="px-5 py-5 flex flex-col sm:flex-row sm:items-center gap-4">
            <div class="flex items-center gap-3 flex-1 min-w-0">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                   style="background: rgba(52,211,153,0.15); border: 1px solid rgba(52,211,153,0.25)">
                <CheckCircleIcon class="w-5 h-5" style="color: #34d399" />
              </div>
              <div>
                <p class="text-white text-sm font-bold">Payment Evidence Submitted</p>
                <p class="text-emerald-300 text-xs mt-0.5">Finance will verify within 1–2 business days</p>
              </div>
            </div>
            <RouterLink :to="`/applications/${route.params.id}`"
                        class="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white flex-shrink-0"
                        style="background: rgba(52,211,153,0.2); border: 1px solid rgba(52,211,153,0.3)">
              Back to Application
              <ChevronRightIcon class="w-4 h-4" />
            </RouterLink>
          </div>
        </div>

        <!-- Info strip -->
        <div class="flex items-start gap-3 rounded-2xl p-4"
             style="background: linear-gradient(135deg, #050f1e, #0a1a2e); border: 1px solid rgba(255,255,255,0.07)">
          <InformationCircleIcon class="w-5 h-5 flex-shrink-0 mt-0.5" style="color: #34d399" />
          <p class="text-xs text-slate-400 leading-relaxed">
            After submitting your payment evidence, the finance team will verify it within 1–2 business days.
            Your application will automatically advance once payment is confirmed.
          </p>
        </div>

      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import {
  ChevronRightIcon, BanknotesIcon, ArrowUpTrayIcon,
  InformationCircleIcon, ClockIcon, CheckCircleIcon,
} from '@heroicons/vue/24/outline'
import { applicationApi, paymentApi } from '@/services/api'
import { receiptApi } from '@/services/api'

interface FeeItem { component: string; label: string; amount: number }
interface PaymentRecord {
  id: string
  payment_reference?: string
  bank_name?: string
  payment_date?: string
  status: string
  amount_submitted?: number
  amount_expected: number
  finance_remarks?: string
  receipt_serial?: string | null
}

const route = useRoute()
const loading = ref(false)
const feeItems = ref<FeeItem[]>([])
const feeTotal = ref<number>(0)
const stageLabel = ref('Stage A — Application Processing')
const appStatus = ref('')
const payments = ref<PaymentRecord[]>([])
const pendingPayment = ref<PaymentRecord | null>(null)
const rejectedPayment = computed(() => payments.value.find(p => p.status === 'rejected') ?? null)
const submitting = ref(false)
const tellerSubmitted = ref(false)
const onlineBusy = ref(false)
const onlineError = ref('')
const demoMode = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const receiptFile = ref<File | null>(null)
const form = ref({
  payment_reference: '',
  bank_name: '',
  payment_date: new Date().toISOString().slice(0, 10),
  amount_submitted: '',
})

const STAGE_LABELS: Record<string, string> = {
  stage_a: 'Stage A — Application Processing',
  stage_c: 'Stage C — Approval & Certificate',
  renewal: 'Renewal',
}

function onFileChange(e: Event) {
  const t = e.target as HTMLInputElement
  receiptFile.value = t.files?.[0] ?? null
}

const MONEY_SAFE_KEYS = new Set([
  'Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
  'Tab', 'Home', 'End', 'Enter', 'Escape',
])

function filterMoneyKey(e: KeyboardEvent) {
  if (e.ctrlKey || e.metaKey) return
  if (MONEY_SAFE_KEYS.has(e.key)) return
  if (!/^[0-9.,]$/.test(e.key)) e.preventDefault()
}

function pasteMoneyAmount(e: ClipboardEvent, target: Record<string, unknown>, field: string) {
  e.preventDefault()
  const raw = e.clipboardData?.getData('text') ?? ''
  const filtered = raw.replace(/[^0-9.,]/g, '')
  const input = e.target as HTMLInputElement
  const start = input.selectionStart ?? 0
  const end = input.selectionEnd ?? 0
  const current = String(target[field] ?? '')
  target[field] = current.slice(0, start) + filtered + current.slice(end)
}

function formatAmount(n: number | string) {
  return new Intl.NumberFormat('en-NG', { minimumFractionDigits: 2 }).format(Number(n))
}

function formatDate(d?: string) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-NG', { day: 'numeric', month: 'short', year: 'numeric' })
}

function paymentStatusLabel(status: string) {
  const map: Record<string, string> = {
    pending: 'Pending',
    submitted: 'Under Review',
    confirmed: 'Confirmed',
    rejected: 'Rejected',
  }
  return map[status] ?? status
}

function paymentStatusClass(status: string) {
  const map: Record<string, string> = {
    pending: 'bg-amber-100 text-amber-700',
    submitted: 'bg-blue-100 text-blue-700',
    confirmed: 'bg-emerald-100 text-emerald-700',
    rejected: 'bg-red-100 text-red-700',
  }
  return map[status] ?? 'bg-slate-100 text-slate-600'
}

async function handlePaymentSubmit() {
  if (!pendingPayment.value) return
  errorMsg.value = ''
  successMsg.value = ''
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('payment_reference', form.value.payment_reference)
    fd.append('bank_name', form.value.bank_name)
    fd.append('payment_date', form.value.payment_date)
    fd.append('amount_submitted', String(form.value.amount_submitted).replace(/,/g, ''))
    if (receiptFile.value) fd.append('receipt_file', receiptFile.value)
    await paymentApi.submitPayment(pendingPayment.value.id, fd)
    tellerSubmitted.value = true
    form.value = { payment_reference: '', bank_name: '', payment_date: new Date().toISOString().slice(0, 10), amount_submitted: '' }
    receiptFile.value = null
    await loadData()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    errorMsg.value = e.response?.data?.detail || 'Failed to submit payment. Please try again.'
  } finally {
    submitting.value = false
  }
}

async function loadData() {
  loading.value = true
  try {
    const [appRes, payRes] = await Promise.all([
      applicationApi.get(route.params.id as string),
      paymentApi.listForApplication(route.params.id as string).catch(() => ({ data: [] })),
    ])
    const app = appRes.data
    appStatus.value = app.status
    payments.value = Array.isArray(payRes.data) ? payRes.data : payRes.data.results ?? []
    pendingPayment.value = payments.value.find(p => p.status === 'pending' || p.status === 'rejected') ?? null

    const stageMap: Record<string, string> = {
      awaiting_stage_a_payment: 'stage_a',
      awaiting_stage_a_payment_confirmation: 'stage_a',
      awaiting_stage_c_payment: 'stage_c',
      awaiting_renewal_payment: 'renewal',
    }
    // Show Stage A fees for draft/submitted apps so the user knows what to expect
    const stage = stageMap[app.status] ?? (
      ['draft', 'submitted'].includes(app.status) ? 'stage_a' : null
    )
    if (stage) {
      stageLabel.value = STAGE_LABELS[stage] ?? stage
      const bRes = await paymentApi.getBreakdown(stage, app.street_type).catch(() => null)
      if (bRes?.data) {
        feeItems.value = bRes.data.breakdown ?? []
        feeTotal.value = Number(bRes.data.total ?? 0)
      }
    }
  } finally {
    loading.value = false
  }
}

async function payOnline() {
  if (!pendingPayment.value) return
  onlineError.value = ''
  onlineBusy.value = true
  try {
    const { data } = await paymentApi.initializePayment(pendingPayment.value.id, window.location.href.split('?')[0])
    if (data.authorization_url) {
      // Redirect to Ibeju Pay hosted checkout; on return, ?reference= is verified on mount.
      window.location.href = data.authorization_url
      return
    }
    // Demo mode — no live gateway configured: simulate a successful payment.
    demoMode.value = true
    await paymentApi.simulatePayment(pendingPayment.value.id)
    await loadData()
    tellerSubmitted.value = true
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    onlineError.value = err.response?.data?.detail || 'Could not start online payment. Please try again.'
  } finally {
    onlineBusy.value = false
  }
}

onMounted(async () => {
  await loadData()
  // If we returned from Ibeju Pay checkout, verify the transaction.
  const reference = (route.query.reference || route.query.trxref) as string | undefined
  if (reference) {
    onlineBusy.value = true
    try {
      await paymentApi.verifyPayment(reference)
      await loadData()
      tellerSubmitted.value = true
    } catch {
      onlineError.value = 'We could not confirm that payment. If you were debited, please contact the council.'
    } finally {
      onlineBusy.value = false
    }
  }
})

async function downloadReceipt(serial: string) {
  try { await receiptApi.download(serial) } catch { /* ignore */ }
}
</script>
