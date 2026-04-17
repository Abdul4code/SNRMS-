<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Fee Configuration</h1>
      <p class="text-sm text-gray-500 mt-0.5">Manage application processing fees for each stage</p>
    </div>

    <div v-if="errorMsg" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{{ errorMsg }}</div>
    <div v-if="successMsg" class="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">{{ successMsg }}</div>

    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
      <div v-else-if="!feeConfigs.length" class="text-center py-12 text-gray-500">
        No fee configurations found.
      </div>
      <table v-else class="w-full text-sm">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Fee Type</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase hidden sm:table-cell">Stage</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase hidden md:table-cell">Street Type</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Amount (₦)</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="cfg in feeConfigs" :key="cfg.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-gray-900 font-medium">{{ cfg.fee_type_display || cfg.fee_type }}</td>
            <td class="px-4 py-3 text-gray-600 hidden sm:table-cell capitalize">{{ cfg.stage?.replace(/_/g, ' ') || '—' }}</td>
            <td class="px-4 py-3 text-gray-600 hidden md:table-cell">{{ cfg.street_type_name || 'All types' }}</td>
            <td class="px-4 py-3">
              <!-- Inline edit -->
              <template v-if="editingId === cfg.id">
                <input
                  v-model="editAmount"
                  type="number"
                  step="0.01"
                  min="0"
                  class="form-input text-sm w-32"
                  @keydown.enter="saveEdit(cfg)"
                  @keydown.esc="cancelEdit"
                />
              </template>
              <span v-else class="font-medium text-gray-900">{{ formatAmount(cfg.amount) }}</span>
            </td>
            <td class="px-4 py-3">
              <template v-if="editingId === cfg.id">
                <button class="text-xs text-green-700 hover:underline mr-2 font-medium" @click="saveEdit(cfg)">Save</button>
                <button class="text-xs text-gray-500 hover:underline" @click="cancelEdit">Cancel</button>
              </template>
              <button v-else class="text-xs text-blue-600 hover:underline font-medium" @click="startEdit(cfg)">Edit</button>
            </td>
          </tr>
        </tbody>
      </table>
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
  if (isNaN(amount) || amount < 0) {
    errorMsg.value = 'Enter a valid amount.'
    return
  }
  try {
    const { data } = await paymentApi.updateFeeConfig(cfg.id, { amount })
    const idx = feeConfigs.value.findIndex((f) => f.id === cfg.id)
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
