<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Admin</p>
            <h1 class="text-white text-2xl font-bold tracking-tight">Fee Configuration</h1>
            <p class="text-slate-400 text-sm mt-1">Manage application processing fees for each stage</p>
          </div>
          <button @click="openAdd"
                  class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white transition-all flex-shrink-0 mt-1"
                  style="background: linear-gradient(135deg, #059669, #047857)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            Add Fee
          </button>
        </div>
      </div>
    </div>

    <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-5">

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

      <div class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
        <div class="px-6 py-5" style="border-bottom: 1px solid #f1f5f9">
          <h2 class="text-sm font-bold text-slate-900">Fee Schedule</h2>
          <p class="text-xs text-slate-500 mt-0.5">Click Edit to modify any fee, or Add Fee to create a new one</p>
        </div>

        <div v-if="loading" class="flex items-center justify-center py-12">
          <div class="w-8 h-8 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
        </div>
        <div v-else-if="!feeConfigs.length" class="flex flex-col items-center py-12 gap-2">
          <p class="text-sm text-slate-500">No fee configurations yet. Click "Add Fee" to get started.</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0">
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Fee Type</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider hidden sm:table-cell">Stage</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider hidden md:table-cell">Street Type</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Amount (₦)</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider hidden sm:table-cell">Status</th>
                <th class="px-5 py-3.5 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(cfg, i) in feeConfigs" :key="cfg.id"
                  :style="i < feeConfigs.length - 1 ? 'border-bottom: 1px solid #f8fafc' : ''"
                  :class="cfg.is_active ? '' : 'opacity-50'"
                  class="hover:bg-slate-50/60 transition-colors">
                <td class="px-5 py-4 font-semibold text-slate-900">{{ cfg.fee_type_display || cfg.fee_type }}</td>
                <td class="px-5 py-4 hidden sm:table-cell">
                  <span v-if="cfg.stage" class="text-xs font-semibold px-2 py-0.5 rounded-full"
                        :class="stageBadgeClass(cfg.stage)">
                    {{ STAGE_LABELS[cfg.stage] || cfg.stage }}
                  </span>
                  <span v-else class="text-slate-400">—</span>
                </td>
                <td class="px-5 py-4 text-slate-500 hidden md:table-cell">{{ cfg.street_type_name || 'All types' }}</td>
                <td class="px-5 py-4 font-semibold text-slate-900">₦{{ formatAmount(cfg.amount) }}</td>
                <td class="px-5 py-4 hidden sm:table-cell">
                  <span class="text-xs font-semibold px-2 py-0.5 rounded-full"
                        :class="cfg.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'">
                    {{ cfg.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td class="px-5 py-4 text-right">
                  <template v-if="deleteConfirmId === cfg.id">
                    <span class="text-xs text-slate-600 mr-2">Delete?</span>
                    <button class="text-xs font-semibold text-red-600 hover:text-red-700 mr-3"
                            :disabled="deletingId === cfg.id"
                            @click="handleDelete(cfg.id)">
                      {{ deletingId === cfg.id ? '…' : 'Yes' }}
                    </button>
                    <button class="text-xs font-semibold text-slate-400 hover:text-slate-600"
                            @click="deleteConfirmId = null">No</button>
                  </template>
                  <template v-else>
                    <button class="text-xs font-semibold text-slate-500 hover:text-slate-700 transition-colors mr-4"
                            @click="openEdit(cfg)">Edit</button>
                    <button class="text-xs font-semibold text-red-400 hover:text-red-600 transition-colors"
                            @click="deleteConfirmId = cfg.id">Delete</button>
                  </template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- Add / Edit Modal -->
  <Teleport to="body">
    <Transition enter-active-class="transition ease-out duration-150"
                enter-from-class="opacity-0" enter-to-class="opacity-100"
                leave-active-class="transition ease-in duration-100"
                leave-from-class="opacity-100" leave-to-class="opacity-0">
      <div v-if="showModal"
           class="fixed inset-0 z-50 flex items-center justify-center p-4"
           style="background: rgba(0,0,0,0.4)"
           @click.self="closeModal">
        <div class="w-full max-w-md rounded-2xl shadow-2xl overflow-hidden" style="background: #fff">

          <!-- Modal header -->
          <div class="px-6 py-5" style="background: #0a1628">
            <h2 class="text-white font-bold text-base">{{ modalMode === 'add' ? 'Add Fee Configuration' : 'Edit Fee Configuration' }}</h2>
            <p class="text-slate-400 text-xs mt-0.5">{{ modalMode === 'add' ? 'Create a new fee entry' : 'Update the selected fee' }}</p>
          </div>

          <!-- Modal body -->
          <form @submit.prevent="handleSave" class="p-6 space-y-5">

            <!-- Error -->
            <div v-if="modalError" class="flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 p-3">
              <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
              </svg>
              <p class="text-sm text-red-700">{{ modalError }}</p>
            </div>

            <!-- Fee Type -->
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1.5">
                Fee Type <span class="text-red-500">*</span>
              </label>
              <select v-model="modalForm.component" required
                      class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all">
                <option value="" disabled>Select a fee type…</option>
                <optgroup label="Stage A — Application">
                  <option v-for="c in FEE_COMPONENTS.filter(f => f.stage === 'stage_a')" :key="c.value" :value="c.value">
                    {{ c.label }}
                  </option>
                </optgroup>
                <optgroup label="Stage C — Certificate">
                  <option v-for="c in FEE_COMPONENTS.filter(f => f.stage === 'stage_c')" :key="c.value" :value="c.value">
                    {{ c.label }}
                  </option>
                </optgroup>
                <optgroup label="Renewal">
                  <option v-for="c in FEE_COMPONENTS.filter(f => f.stage === 'renewal')" :key="c.value" :value="c.value">
                    {{ c.label }}
                  </option>
                </optgroup>
              </select>
            </div>

            <!-- Stage (derived, read-only) -->
            <div v-if="modalForm.component">
              <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Stage</label>
              <span class="inline-flex text-xs font-semibold px-3 py-1 rounded-full"
                    :class="stageBadgeClass(modalComponentStage)">
                {{ STAGE_LABELS[modalComponentStage] || modalComponentStage }}
              </span>
            </div>

            <!-- Street Type (only for street_name_fee) -->
            <div v-if="modalForm.component === 'street_name_fee'">
              <label class="block text-sm font-semibold text-slate-700 mb-1.5">
                Street Type <span class="text-red-500">*</span>
              </label>
              <select v-model="modalForm.street_type_id" required
                      class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all">
                <option value="" disabled>Select a street type…</option>
                <option v-for="st in streetTypes" :key="st.id" :value="st.id">{{ st.name }}</option>
              </select>
            </div>

            <!-- Amount -->
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1.5">
                Amount (₦) <span class="text-red-500">*</span>
              </label>
              <input v-model="modalForm.amount" type="text" inputmode="decimal" required
                     placeholder="0.00"
                     @keydown="filterMoneyKey"
                     @paste="(e) => pasteMoneyAmount(e, modalForm, 'amount')"
                     class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all" />
            </div>

            <!-- Active toggle -->
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-semibold text-slate-700">Active</p>
                <p class="text-xs text-slate-400">Inactive fees are excluded from payment calculations</p>
              </div>
              <button type="button"
                      class="relative inline-flex h-6 w-11 flex-shrink-0 rounded-full border-2 border-transparent transition-colors focus:outline-none"
                      :class="modalForm.is_active ? 'bg-emerald-500' : 'bg-slate-200'"
                      @click="modalForm.is_active = !modalForm.is_active">
                <span class="inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform"
                      :class="modalForm.is_active ? 'translate-x-5' : 'translate-x-0'"></span>
              </button>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-3 pt-1">
              <button type="submit" :disabled="modalSaving"
                      class="flex-1 flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60"
                      style="background: linear-gradient(135deg, #059669, #047857)">
                {{ modalSaving ? 'Saving…' : modalMode === 'add' ? 'Add Fee' : 'Save Changes' }}
              </button>
              <button type="button"
                      class="flex-1 px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-100 transition-all"
                      @click="closeModal">Cancel</button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { paymentApi, configApi } from '@/services/api'

interface FeeConfig {
  id: string
  component: string
  fee_type: string
  fee_type_display: string
  stage: string | null
  amount: number
  street_type_id: string | null
  street_type_name: string | null
  is_active: boolean
  updated_at: string
}

const FEE_COMPONENTS = [
  { value: 'application_fee',          label: 'Application Fee',           stage: 'stage_a' },
  { value: 'inspection_fee',           label: 'Inspection Fee',            stage: 'stage_a' },
  { value: 'radio_tv_tax',             label: 'Radio/TV Tax',              stage: 'stage_a' },
  { value: 'committee_verification_fee', label: 'Committee Verification Fee', stage: 'stage_a' },
  { value: 'street_name_fee',          label: 'Street Name Fee',           stage: 'stage_c' },
  { value: 'signpost_installation_fee', label: 'Signpost Installation Fee', stage: 'stage_c' },
  { value: 'map_upload_fee',           label: 'Map Upload Fee',            stage: 'stage_c' },
  { value: 'renewal_fee',              label: 'Renewal Fee',               stage: 'renewal' },
]

const STAGE_LABELS: Record<string, string> = {
  stage_a: 'Stage A',
  stage_c: 'Stage C',
  renewal:  'Renewal',
}

function stageBadgeClass(stage: string | null) {
  if (stage === 'stage_a') return 'bg-emerald-100 text-emerald-700'
  if (stage === 'stage_c') return 'bg-blue-100 text-blue-700'
  if (stage === 'renewal')  return 'bg-amber-100 text-amber-700'
  return 'bg-slate-100 text-slate-500'
}

const feeConfigs = ref<FeeConfig[]>([])
const streetTypes = ref<{ id: string; name: string }[]>([])
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

// Modal
const showModal = ref(false)
const modalMode = ref<'add' | 'edit'>('add')
const editingId = ref<string | null>(null)
const modalForm = ref({ component: '', amount: '', street_type_id: '', is_active: true })
const modalError = ref('')
const modalSaving = ref(false)

// Delete
const deleteConfirmId = ref<string | null>(null)
const deletingId = ref<string | null>(null)

const modalComponentStage = computed(() =>
  FEE_COMPONENTS.find(c => c.value === modalForm.value.component)?.stage ?? ''
)

function formatAmount(n: number) {
  return new Intl.NumberFormat('en-NG', { minimumFractionDigits: 2 }).format(n)
}

function openAdd() {
  modalMode.value = 'add'
  editingId.value = null
  modalForm.value = { component: '', amount: '', street_type_id: '', is_active: true }
  modalError.value = ''
  successMsg.value = ''
  errorMsg.value = ''
  showModal.value = true
}

function openEdit(cfg: FeeConfig) {
  modalMode.value = 'edit'
  editingId.value = cfg.id
  modalForm.value = {
    component: cfg.component,
    amount: String(cfg.amount),
    street_type_id: cfg.street_type_id ?? '',
    is_active: cfg.is_active,
  }
  modalError.value = ''
  successMsg.value = ''
  errorMsg.value = ''
  showModal.value = true
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

function closeModal() {
  showModal.value = false
}

async function handleSave() {
  if (!modalForm.value.component) { modalError.value = 'Please select a fee type.'; return }
  const amount = parseFloat(String(modalForm.value.amount).replace(/,/g, ''))
  if (isNaN(amount) || amount <= 0) { modalError.value = 'Enter a valid amount greater than 0.'; return }
  if (modalForm.value.component === 'street_name_fee' && !modalForm.value.street_type_id) {
    modalError.value = 'Please select a street type for Street Name Fee.'
    return
  }

  const payload: Record<string, unknown> = {
    component: modalForm.value.component,
    amount: amount,
    is_active: modalForm.value.is_active,
    street_type: modalForm.value.component === 'street_name_fee' ? modalForm.value.street_type_id : null,
  }

  modalSaving.value = true
  modalError.value = ''
  try {
    if (modalMode.value === 'add') {
      const { data } = await paymentApi.createFeeConfig(payload)
      feeConfigs.value.push(data)
      feeConfigs.value.sort((a, b) => a.component.localeCompare(b.component))
      successMsg.value = 'Fee configuration added.'
    } else {
      const { data } = await paymentApi.updateFeeConfig(editingId.value!, payload)
      const idx = feeConfigs.value.findIndex(f => f.id === editingId.value)
      if (idx !== -1) feeConfigs.value[idx] = data
      successMsg.value = 'Fee configuration updated.'
    }
    closeModal()
  } catch (err: unknown) {
    const e = err as { response?: { data?: Record<string, string[] | string> } }
    const d = e.response?.data
    if (d) {
      modalError.value = Object.values(d).flat().join(' ') || 'Failed to save.'
    } else {
      modalError.value = 'Failed to save.'
    }
  } finally {
    modalSaving.value = false
  }
}

async function handleDelete(id: string) {
  deletingId.value = id
  try {
    await paymentApi.deleteFeeConfig(id)
    feeConfigs.value = feeConfigs.value.filter(f => f.id !== id)
    successMsg.value = 'Fee configuration deleted.'
  } catch {
    errorMsg.value = 'Failed to delete fee configuration.'
  } finally {
    deletingId.value = null
    deleteConfirmId.value = null
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const [feesRes, stRes] = await Promise.all([
      paymentApi.listFeeConfig(),
      configApi.listStreetTypes(),
    ])
    feeConfigs.value = Array.isArray(feesRes.data) ? feesRes.data : feesRes.data.results ?? []
    streetTypes.value = Array.isArray(stRes.data) ? stRes.data : stRes.data.results ?? []
  } finally {
    loading.value = false
  }
})
</script>
