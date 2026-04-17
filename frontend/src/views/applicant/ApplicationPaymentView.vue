<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <!-- Page header band -->
    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-2xl mx-auto px-4 sm:px-6 py-5">
        <nav class="flex items-center gap-2 text-xs text-slate-400 mb-3">
          <RouterLink to="/applications" class="hover:text-emerald-400 transition-colors">My Applications</RouterLink>
          <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
          <RouterLink :to="`/applications/${route.params.id}`" class="hover:text-emerald-400 transition-colors font-mono">
            APP-{{ route.params.id }}
          </RouterLink>
          <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
          <span class="text-slate-300">Payment</span>
        </nav>
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1">Payment</p>
        <h1 class="text-white text-xl font-bold tracking-tight">Submit Payment Evidence</h1>
        <p class="text-slate-400 text-sm mt-0.5">Pay at any bank branch, then submit your teller details here</p>
      </div>
    </div>

    <div class="max-w-2xl mx-auto px-4 sm:px-6 py-6 space-y-4">

      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center py-16">
        <div class="w-9 h-9 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
      </div>

      <template v-else>

        <!-- Fee breakdown card -->
        <div v-if="breakdown" class="rounded-2xl overflow-hidden"
             style="background: #fff; border: 1px solid #e2e8f0">
          <div class="px-5 py-4 flex items-center gap-2.5" style="border-bottom: 1px solid #f1f5f9">
            <div class="w-7 h-7 rounded-lg flex items-center justify-center"
                 style="background: rgba(5,150,105,0.08); border: 1px solid rgba(5,150,105,0.15)">
              <CurrencyDollarIcon class="w-4 h-4" style="color: #059669" />
            </div>
            <h2 class="text-sm font-bold text-slate-900">Fee Breakdown</h2>
          </div>
          <div class="px-5 py-4">
            <table class="w-full text-sm">
              <tbody class="divide-y divide-slate-50">
                <tr v-for="item in breakdown.items" :key="item.label">
                  <td class="py-3 text-slate-600">{{ item.label }}</td>
                  <td class="py-3 text-right font-semibold text-slate-900">₦{{ formatAmount(item.amount) }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr style="border-top: 2px solid #e2e8f0">
                  <td class="pt-4 font-bold text-slate-900 text-base">Total Due</td>
                  <td class="pt-4 text-right font-bold text-xl" style="color: #059669">₦{{ formatAmount(breakdown.total) }}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <!-- Existing payments -->
        <div v-if="payments.length" class="rounded-2xl overflow-hidden"
             style="background: #fff; border: 1px solid #e2e8f0">
          <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
            <h2 class="text-sm font-bold text-slate-900">Payment Records</h2>
          </div>
          <ul class="divide-y divide-slate-50">
            <li v-for="p in payments" :key="p.id" class="flex items-center justify-between px-5 py-4 gap-4">
              <div class="min-w-0">
                <p class="text-sm font-semibold text-slate-900 font-mono">{{ p.payment_reference || 'Pending Reference' }}</p>
                <p class="text-xs text-slate-500 mt-0.5">
                  {{ p.bank_name }}{{ p.payment_date ? ' · ' + formatDate(p.payment_date) : '' }}
                </p>
              </div>
              <span class="px-3 py-1 rounded-full text-xs font-semibold flex-shrink-0"
                    :class="paymentStatusClass(p.status)">
                {{ p.status }}
              </span>
            </li>
          </ul>
        </div>

        <!-- Payment form card -->
        <div class="rounded-2xl overflow-hidden"
             style="background: #fff; border: 1px solid #e2e8f0">
          <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
            <h2 class="text-sm font-bold text-slate-900">Payment Details</h2>
            <p class="text-xs text-slate-500 mt-0.5">Enter the details from your bank teller / payment receipt</p>
          </div>

          <!-- Status msgs -->
          <transition enter-active-class="transition duration-200 ease-out"
                      enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
            <div v-if="errorMsg" class="mx-5 mt-5 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-3.5">
              <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
              </svg>
              <p class="text-sm text-red-700">{{ errorMsg }}</p>
            </div>
          </transition>
          <transition enter-active-class="transition duration-200 ease-out"
                      enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
            <div v-if="successMsg" class="mx-5 mt-5 flex items-start gap-3 rounded-xl border border-emerald-100 bg-emerald-50 p-3.5">
              <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/>
              </svg>
              <p class="text-sm text-emerald-700">{{ successMsg }}</p>
            </div>
          </transition>

          <form @submit.prevent="handlePaymentSubmit" class="px-5 py-5 space-y-4" novalidate>
            <!-- Payment reference -->
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1.5">
                Payment Reference / Teller No. <span class="text-red-500">*</span>
              </label>
              <input v-model="form.payment_reference" type="text" required
                     placeholder="e.g. TL20240517001"
                     class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-mono text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
            </div>
            <!-- Bank + Date -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1.5">
                  Bank Name <span class="text-red-500">*</span>
                </label>
                <input v-model="form.bank_name" type="text" required placeholder="e.g. Access Bank"
                       class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
              </div>
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1.5">
                  Payment Date <span class="text-red-500">*</span>
                </label>
                <input v-model="form.payment_date" type="date" required
                       class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
              </div>
            </div>
            <!-- Amount -->
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1.5">
                Amount Paid (₦) <span class="text-red-500">*</span>
              </label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <span class="text-slate-500 font-semibold text-sm">₦</span>
                </div>
                <input v-model="form.amount_submitted" type="number" step="0.01" required placeholder="0.00"
                       class="block w-full rounded-xl border border-slate-200 bg-slate-50 pl-8 pr-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
              </div>
            </div>
            <!-- Receipt upload -->
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1.5">Receipt / Teller Upload <span class="text-slate-400 font-normal text-xs">(optional)</span></label>
              <label class="flex items-center gap-3 p-4 rounded-xl border-2 border-dashed cursor-pointer transition-colors"
                     :class="receiptFile ? 'border-emerald-300 bg-emerald-50' : 'border-slate-200 hover:border-slate-300 bg-slate-50'">
                <ArrowUpTrayIcon class="w-5 h-5 flex-shrink-0"
                                 :class="receiptFile ? 'text-emerald-500' : 'text-slate-400'" />
                <div>
                  <p class="text-sm font-medium text-slate-700">
                    {{ receiptFile ? receiptFile.name : 'Click to attach receipt' }}
                  </p>
                  <p v-if="receiptFile" class="text-xs text-slate-500">{{ (receiptFile.size / 1024).toFixed(1) }} KB</p>
                  <p v-else class="text-xs text-slate-400 mt-0.5">PDF, JPG, PNG</p>
                </div>
                <input type="file" class="hidden" accept=".pdf,.jpg,.jpeg,.png" @change="onFileChange" />
              </label>
            </div>

            <button type="submit"
                    :disabled="submitting || !form.payment_reference || !form.bank_name || !form.payment_date || !form.amount_submitted"
                    class="flex items-center justify-center gap-2 w-full px-5 py-3.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                    style="background: linear-gradient(135deg, #059669, #047857); box-shadow: 0 4px 16px rgba(5,150,105,0.3)">
              <svg v-if="submitting" class="animate-spin w-4 h-4 opacity-80" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              {{ submitting ? 'Submitting…' : 'Submit Payment Evidence' }}
            </button>
          </form>
        </div>

        <!-- Info strip -->
        <div class="flex items-start gap-3 rounded-2xl p-4"
             style="background: linear-gradient(135deg, #050f1e, #0a1a2e); border: 1px solid rgba(255,255,255,0.07)">
          <InformationCircleIcon class="w-5 h-5 flex-shrink-0 mt-0.5" style="color: #34d399" />
          <p class="text-xs text-slate-400 leading-relaxed">
            After submitting, the finance team will verify your payment within 1–2 business days.
            Your application will automatically advance once payment is confirmed.
          </p>
        </div>

      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { ChevronRightIcon, CurrencyDollarIcon, ArrowUpTrayIcon, InformationCircleIcon } from '@heroicons/vue/24/outline'
import { applicationApi, paymentApi } from '@/services/api'

interface FeeItem { label: string; amount: number }
interface Breakdown { items: FeeItem[]; total: number }
interface Payment { id: number; payment_reference?: string; bank_name?: string; payment_date?: string; status: string; amount?: number }

const route = useRoute()
const loading = ref(false)
const breakdown = ref<Breakdown | null>(null)
const payments = ref<Payment[]>([])
const pendingPayment = ref<Payment | null>(null)
const submitting = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const receiptFile = ref<File | null>(null)
const form = ref({
  payment_reference: '',
  bank_name: '',
  payment_date: new Date().toISOString().slice(0, 10),
  amount_submitted: '',
})

function onFileChange(e: Event) {
  const t = e.target as HTMLInputElement
  receiptFile.value = t.files?.[0] ?? null
}

function formatAmount(n: number) {
  return new Intl.NumberFormat('en-NG', { minimumFractionDigits: 2 }).format(n)
}

function formatDate(d?: string) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-NG', { day: 'numeric', month: 'short', year: 'numeric' })
}

function paymentStatusClass(status: string) {
  const map: Record<string, string> = {
    pending: 'bg-amber-100 text-amber-700',
    confirmed: 'bg-emerald-100 text-emerald-700',
    rejected: 'bg-red-100 text-red-700',
  }
  return map[status] ?? 'bg-slate-100 text-slate-600'
}

async function handlePaymentSubmit() {
  errorMsg.value = ''
  successMsg.value = ''
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('payment_reference', form.value.payment_reference)
    fd.append('bank_name', form.value.bank_name)
    fd.append('payment_date', form.value.payment_date)
    fd.append('amount_submitted', form.value.amount_submitted)
    if (receiptFile.value) fd.append('receipt_file', receiptFile.value)

    if (pendingPayment.value) {
      await paymentApi.submitPayment(pendingPayment.value.id, fd)
    } else {
      const obj: Record<string, string> = {
        application: route.params.id as string,
        payment_reference: form.value.payment_reference,
        bank_name: form.value.bank_name,
        payment_date: form.value.payment_date,
        amount_submitted: form.value.amount_submitted,
      }
      await paymentApi.submitPayment(route.params.id as string, obj)
    }
    successMsg.value = 'Payment evidence submitted. Finance will confirm your payment within 1–2 business days.'
    await loadData()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    errorMsg.value = e.response?.data?.detail || 'Failed to submit payment.'
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
    payments.value = Array.isArray(payRes.data) ? payRes.data : payRes.data.results ?? []
    pendingPayment.value = payments.value.find((p) => p.status === 'pending') ?? null

    const stageMap: Record<string, string> = {
      awaiting_stage_a_payment: 'stage_a',
      awaiting_stage_c_payment: 'stage_c',
      awaiting_renewal_payment: 'renewal',
    }
    const stage = stageMap[app.status]
    if (stage) {
      const bRes = await paymentApi.getBreakdown(stage, app.street_type).catch(() => null)
      breakdown.value = bRes?.data ?? null
    }
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>
