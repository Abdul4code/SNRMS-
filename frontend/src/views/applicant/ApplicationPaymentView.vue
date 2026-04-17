<template>
  <div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <nav class="text-sm text-gray-500 mb-6 flex items-center gap-2">
      <RouterLink to="/applications" class="hover:text-blue-600">My Applications</RouterLink>
      <span>/</span>
      <RouterLink :to="`/applications/${route.params.id}`" class="hover:text-blue-600">
        #{{ route.params.id }}
      </RouterLink>
      <span>/</span>
      <span class="text-gray-900">Payment</span>
    </nav>

    <div v-if="loading" class="flex justify-center py-16">
      <div class="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" />
    </div>

    <template v-else>
      <!-- Fee breakdown -->
      <AppCard v-if="breakdown" title="Fee Breakdown" class="mb-5">
        <table class="w-full text-sm">
          <thead class="border-b border-gray-200">
            <tr>
              <th class="pb-2 text-left text-xs text-gray-500 font-semibold uppercase">Item</th>
              <th class="pb-2 text-right text-xs text-gray-500 font-semibold uppercase">Amount (₦)</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="item in breakdown.items" :key="item.label">
              <td class="py-2 text-gray-700">{{ item.label }}</td>
              <td class="py-2 text-right text-gray-900 font-medium">{{ formatAmount(item.amount) }}</td>
            </tr>
          </tbody>
          <tfoot class="border-t-2 border-gray-300">
            <tr>
              <td class="pt-3 font-bold text-gray-900">Total</td>
              <td class="pt-3 text-right font-bold text-blue-700 text-base">{{ formatAmount(breakdown.total) }}</td>
            </tr>
          </tfoot>
        </table>
      </AppCard>

      <!-- Existing payments -->
      <AppCard v-if="payments.length" title="Payment Records" class="mb-5">
        <ul class="space-y-3">
          <li v-for="p in payments" :key="p.id" class="flex items-center justify-between p-3 bg-gray-50 rounded-lg text-sm">
            <div>
              <p class="font-medium text-gray-900">{{ p.payment_reference || 'Pending' }}</p>
              <p class="text-xs text-gray-500 mt-0.5">{{ p.bank_name }} · {{ formatDate(p.payment_date) }}</p>
            </div>
            <span :class="paymentStatusClass(p.status)" class="text-xs px-2.5 py-0.5 rounded-full font-medium capitalize">
              {{ p.status }}
            </span>
          </li>
        </ul>
      </AppCard>

      <!-- Payment form -->
      <AppCard title="Submit Payment Reference">
        <p class="text-sm text-gray-600 mb-4">
          Make the payment at any bank branch using the breakdown above, then fill in the details below.
        </p>

        <div v-if="errorMsg" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{{ errorMsg }}</div>
        <div v-if="successMsg" class="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">{{ successMsg }}</div>

        <form @submit.prevent="handlePaymentSubmit" class="space-y-4">
          <div>
            <label class="form-label">Payment Reference / Teller No. <span class="text-red-500">*</span></label>
            <input v-model="form.payment_reference" type="text" required class="form-input" placeholder="e.g. TL20240517001" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="form-label">Bank Name <span class="text-red-500">*</span></label>
              <input v-model="form.bank_name" type="text" required class="form-input" placeholder="e.g. Access Bank" />
            </div>
            <div>
              <label class="form-label">Payment Date <span class="text-red-500">*</span></label>
              <input v-model="form.payment_date" type="date" required class="form-input" />
            </div>
          </div>
          <div>
            <label class="form-label">Amount Paid (₦) <span class="text-red-500">*</span></label>
            <input v-model="form.amount_submitted" type="number" step="0.01" required class="form-input" placeholder="0.00" />
          </div>
          <div>
            <label class="form-label">Receipt / Teller (optional)</label>
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              class="block w-full text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-100 file:text-blue-700 hover:file:bg-blue-200"
              @change="onFileChange"
            />
          </div>

          <button type="submit" :disabled="submitting" class="btn-primary w-full">
            {{ submitting ? 'Submitting…' : 'Submit Payment Evidence' }}
          </button>
        </form>
      </AppCard>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { applicationApi, paymentApi } from '@/services/api'
import AppCard from '@/components/AppCard.vue'

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
    pending: 'bg-yellow-100 text-yellow-700',
    confirmed: 'bg-green-100 text-green-700',
    rejected: 'bg-red-100 text-red-700',
  }
  return map[status] ?? 'bg-gray-100 text-gray-600'
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
      // Create via application endpoint with form data
      const obj: Record<string, string> = {
        application: route.params.id as string,
        payment_reference: form.value.payment_reference,
        bank_name: form.value.bank_name,
        payment_date: form.value.payment_date,
        amount_submitted: form.value.amount_submitted,
      }
      await paymentApi.submitPayment(route.params.id as string, obj)
    }
    successMsg.value = 'Payment evidence submitted. Finance will confirm your payment.'
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

    // Get fee breakdown based on current app status
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
