<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Admin</p>
            <h1 class="text-white text-2xl font-bold tracking-tight">Street Types</h1>
            <p class="text-slate-400 text-sm mt-1">Configure available street type categories</p>
          </div>
          <button class="flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white transition-all"
                  style="background: linear-gradient(135deg, #059669, #047857); box-shadow: 0 4px 14px rgba(5,150,105,0.35)"
                  @click="showForm = !showForm">
            <PlusIcon class="w-4 h-4" />
            Add Street Type
          </button>
        </div>
      </div>
    </div>

    <div class="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-5">

      <!-- Add form -->
      <transition enter-active-class="transition duration-200 ease-out"
                  enter-from-class="opacity-0 -translate-y-2" enter-to-class="opacity-100 translate-y-0"
                  leave-active-class="transition duration-150 ease-in"
                  leave-from-class="opacity-100 translate-y-0" leave-to-class="opacity-0 -translate-y-2">
        <div v-if="showForm" class="rounded-2xl overflow-hidden"
             style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
          <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
            <h3 class="text-sm font-bold text-slate-900">New Street Type</h3>
          </div>
          <div v-if="formError" class="mx-5 mt-5 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-3.5">
            <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
            </svg>
            <p class="text-sm text-red-700">{{ formError }}</p>
          </div>
          <form @submit.prevent="handleCreate" class="px-5 py-5 flex flex-wrap gap-3 items-end">
            <div class="flex-1 min-w-44">
              <label class="block text-sm font-semibold text-slate-700 mb-1.5">Name <span class="text-red-500">*</span></label>
              <input v-model="newType.name" type="text" required placeholder="e.g. Avenue"
                     class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
            </div>
            <div class="flex-1 min-w-44">
              <label class="block text-sm font-semibold text-slate-700 mb-1.5">Description <span class="text-slate-400 font-normal text-xs">(optional)</span></label>
              <input v-model="newType.description" type="text" placeholder="Brief description"
                     class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
            </div>
            <div class="flex items-center gap-2">
              <button type="submit" :disabled="creating"
                      class="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60"
                      style="background: linear-gradient(135deg, #059669, #047857)">
                {{ creating ? 'Adding…' : 'Add' }}
              </button>
              <button type="button"
                      class="px-4 py-2.5 rounded-xl text-sm font-semibold text-slate-600 border border-slate-200 hover:bg-slate-50 transition-all"
                      @click="showForm = false">
                Cancel
              </button>
            </div>
          </form>
        </div>
      </transition>

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

      <!-- Table card -->
      <div class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
        <div class="px-6 py-5" style="border-bottom: 1px solid #f1f5f9">
          <h2 class="text-sm font-bold text-slate-900">Configured Street Types</h2>
          <p class="text-xs text-slate-500 mt-0.5">{{ streetTypes.length }} type{{ streetTypes.length === 1 ? '' : 's' }}</p>
        </div>

        <div v-if="loading" class="flex items-center justify-center py-12">
          <div class="w-8 h-8 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
        </div>
        <div v-else-if="!streetTypes.length" class="flex flex-col items-center py-12 gap-2">
          <p class="text-sm text-slate-500">No street types configured.</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0">
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Name</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider hidden sm:table-cell">Description</th>
                <th class="px-5 py-3.5 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(st, i) in streetTypes" :key="st.id"
                  :style="i < streetTypes.length - 1 ? 'border-bottom: 1px solid #f8fafc' : ''"
                  class="hover:bg-slate-50/60 transition-colors">
                <td class="px-5 py-4">
                  <template v-if="editingId === st.id">
                    <input v-model="editName" type="text"
                           class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm w-40 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"/>
                  </template>
                  <span v-else class="font-semibold text-slate-900">{{ st.name }}</span>
                </td>
                <td class="px-5 py-4 hidden sm:table-cell">
                  <template v-if="editingId === st.id">
                    <input v-model="editDesc" type="text" placeholder="Description"
                           class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm w-52 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"/>
                  </template>
                  <span v-else class="text-slate-500">{{ st.description || '—' }}</span>
                </td>
                <td class="px-5 py-4 text-right">
                  <template v-if="editingId === st.id">
                    <button class="text-xs font-semibold text-emerald-600 hover:text-emerald-700 mr-3" @click="saveEdit(st)">Save</button>
                    <button class="text-xs font-semibold text-slate-400 hover:text-slate-600" @click="cancelEdit">Cancel</button>
                  </template>
                  <button v-else class="text-xs font-semibold text-slate-500 hover:text-slate-700 transition-colors" @click="startEdit(st)">Edit</button>
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
import { PlusIcon } from '@heroicons/vue/24/outline'
import { configApi } from '@/services/api'

interface StreetType { id: number; name: string; description?: string }

const streetTypes = ref<StreetType[]>([])
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const showForm = ref(false)
const creating = ref(false)
const formError = ref('')
const editingId = ref<number | null>(null)
const editName = ref('')
const editDesc = ref('')
const newType = ref({ name: '', description: '' })

async function load() {
  loading.value = true
  try {
    const { data } = await configApi.listStreetTypes()
    streetTypes.value = Array.isArray(data) ? data : data.results ?? []
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  formError.value = ''
  creating.value = true
  try {
    await configApi.createStreetType({ ...newType.value })
    successMsg.value = `Street type "${newType.value.name}" added.`
    newType.value = { name: '', description: '' }
    showForm.value = false
    await load()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string; name?: string[] } } }
    formError.value = e.response?.data?.detail || e.response?.data?.name?.[0] || 'Failed to create.'
  } finally {
    creating.value = false
  }
}

function startEdit(st: StreetType) {
  editingId.value = st.id
  editName.value = st.name
  editDesc.value = st.description ?? ''
}

function cancelEdit() { editingId.value = null }

async function saveEdit(st: StreetType) {
  try {
    const { data } = await configApi.updateStreetType(st.id, { name: editName.value, description: editDesc.value })
    const idx = streetTypes.value.findIndex(t => t.id === st.id)
    if (idx !== -1) streetTypes.value[idx] = data
    successMsg.value = 'Street type updated.'
    cancelEdit()
  } catch {
    errorMsg.value = 'Failed to update.'
  }
}

onMounted(load)
</script>
