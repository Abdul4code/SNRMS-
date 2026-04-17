<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 py-6">
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1">Admin</p>
        <h1 class="text-white text-xl font-bold tracking-tight">Fee Configuration</h1>
        <p class="text-slate-400 text-sm mt-0.5">Manage application processing fees for each stage</p>
      </div>
    </div>

    <div class="max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-4">

      <!-- Alerts -->
      <transition enter-active-class="transition duration-200 ease-out"
                  enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
        <div v-if="errorMsg" class="flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 p-4">
          <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
          </svg>
          <p class="text-sm text-red-700">{{ errorMsg }}</p>
        </div>
      </transition>
      <transition enter-active-class="transition duration-200 ease-out"
                  enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
        <div v-if="successMsg" class="flex items-start gap-3 rounded-2xl border border-emerald-100 bg-emerald-50 p-4">
          <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/>
          </svg>
          <p class="text-sm text-emerald-700">{{ successMsg }}</p>
        </div>
      </transition>

      <div class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0">
        <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
          <h2 class="text-sm font-bold text-slate-900">Fee Schedule</h2>
          <p class="text-xs text-slate-500 mt-0.5">Click "Edit" to update any fee amount inline</p>
        </div>

        <div v-if="loading" class="flex items-center justify-center py-12">
          <div class="w-8 h-8 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
        </div>
        <div v-else-if="!feeConfigs.length" class="flex flex-col items-center py-12 gap-2">
          <p class="text-sm text-slate-500">No fee configurations found.</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0">
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Fee Type</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider hidden sm:table-cell">Stage</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider hidden md:table-cell">Street Type</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Amount (₦)</th>
                <th class="px-5 py-3.5 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(cfg, i) in feeConfigs" :key="cfg.id"
                  :style="i < feeConfigs.length - 1 ? 'border-bottom: 1px solid #f8fafc' : ''"
                  class="hover:bg-slate-50/60 transition-colors">
                <td class="px-5 py-4 font-semibold text-slate-900">{{ cfg.fee_type_display || cfg.fee_type }}</td>
                <td class="px-5 py-4 text-slate-500 capitalize hidden sm:table-cell">{{ cfg.stage?.replace(/_/g, ' ') || '—' }}</td>
                <td class="px-5 py-4 text-slate-500 hidden md:table-cell">{{ cfg.street_type_name || 'All types' }}</td>
                <td class="px-5 py-4">
                  <template v-if="editingId === cfg.id">
                    <input v-model="editAmount" type="number" step="0.01" min="0"
                           class="w-36 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                           @keydown.enter="saveEdit(cfg)"
                           @keydown.esc="cancelEdit" />
                  </template>
                  <span v-else class="font-semibold text-slate-900">₦{{ formatAmount(cfg.amount) }}</span>
                </td>
                <td class="px-5 py-4 text-right">
                  <template v-if="editingId === cfg.id">
                    <button class="text-xs font-semibold text-emerald-600 hover:text-emerald-700 mr-3" @click="saveEdit(cfg)">Save</button>
                    <button class="text-xs font-semibold text-slate-400 hover:text-slate-600" @click="cancelEdit">Cancel</button>
                  </template>
                  <button v-else class="text-xs font-semibold text-slate-500 hover:text-slate-700 transition-colors" @click="startEdit(cfg)">Edit</button>
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
import { ref, onMounted } from 'vue'
import { paymentApi } from '@/services/api'

interface FeeConfig {
  id: number
  fee_type: string
  fee_type_display?: string
  stage?: string
  street_type?: number
  street_type_name?: string
  amount: number
}

const feeConfigs = ref<FeeConfig[]>([])
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const editingId = ref<number | null>(null)
const editAmount = ref<string>('')

function formatAmount(n: number) {
  return new Intl.NumberFormat('en-NG', { minimumFractionDigits: 2 }).format(n)
}

function startEdit(cfg: FeeConfig) {
  editingId.value = cfg.id
  editAmount.value = String(cfg.amount)
  errorMsg.value = ''
  successMsg.value = ''
}

function cancelEdit() {
  editingId.value = null
  editAmount.value = ''
}

async function saveEdit(cfg: FeeConfig) {
  const amount = parseFloat(editAmount.value)
  if (isNaN(amount) || amount < 0) { errorMsg.value = 'Enter a valid amount.'; return }
  try {
    const { data } = await paymentApi.updateFeeConfig(cfg.id, { amount })
    const idx = feeConfigs.value.findIndex(f => f.id === cfg.id)
    if (idx !== -1) feeConfigs.value[idx] = data
    successMsg.value = `Fee updated to ₦${formatAmount(amount)}.`
    cancelEdit()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    errorMsg.value = e.response?.data?.detail || 'Failed to update fee.'
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await paymentApi.listFeeConfig()
    feeConfigs.value = Array.isArray(data) ? data : data.results ?? []
  } finally {
    loading.value = false
  }
})
</script>
