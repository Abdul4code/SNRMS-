<template>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Street Types</h1>
        <p class="text-sm text-gray-500 mt-0.5">Configure available street type categories</p>
      </div>
      <button class="btn-primary gap-2" @click="showForm = !showForm">
        <PlusIcon class="w-4 h-4" />
        Add Street Type
      </button>
    </div>

    <!-- Add form -->
    <div v-if="showForm" class="bg-blue-50 border border-blue-200 rounded-xl p-5 mb-5">
      <h3 class="text-sm font-semibold text-blue-900 mb-3">New Street Type</h3>
      <div v-if="formError" class="mb-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">{{ formError }}</div>
      <form @submit.prevent="handleCreate" class="flex gap-3 flex-wrap">
        <div class="flex-1 min-w-48">
          <label class="form-label text-xs">Name</label>
          <input v-model="newType.name" type="text" required class="form-input text-sm" placeholder="e.g. Avenue" />
        </div>
        <div class="flex-1 min-w-48">
          <label class="form-label text-xs">Description (optional)</label>
          <input v-model="newType.description" type="text" class="form-input text-sm" placeholder="Brief description" />
        </div>
        <div class="flex items-end gap-2">
          <button type="submit" :disabled="creating" class="btn-primary text-sm">
            {{ creating ? 'Adding…' : 'Add' }}
          </button>
          <button type="button" class="btn-secondary text-sm" @click="showForm = false">Cancel</button>
        </div>
      </form>
    </div>

    <div v-if="errorMsg" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{{ errorMsg }}</div>
    <div v-if="successMsg" class="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">{{ successMsg }}</div>

    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
      <div v-else-if="!streetTypes.length" class="text-center py-12 text-gray-500">No street types configured.</div>
      <table v-else class="w-full text-sm">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Name</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase hidden sm:table-cell">Description</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="st in streetTypes" :key="st.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 font-medium text-gray-900">
              <template v-if="editingId === st.id">
                <input v-model="editName" type="text" class="form-input text-sm w-40" />
              </template>
              <span v-else>{{ st.name }}</span>
            </td>
            <td class="px-4 py-3 text-gray-600 hidden sm:table-cell">
              <template v-if="editingId === st.id">
                <input v-model="editDesc" type="text" class="form-input text-sm w-48" placeholder="Description" />
              </template>
              <span v-else>{{ st.description || '—' }}</span>
            </td>
            <td class="px-4 py-3">
              <template v-if="editingId === st.id">
                <button class="text-xs text-green-700 hover:underline mr-2 font-medium" @click="saveEdit(st)">Save</button>
                <button class="text-xs text-gray-500 hover:underline" @click="cancelEdit">Cancel</button>
              </template>
              <button v-else class="text-xs text-blue-600 hover:underline font-medium" @click="startEdit(st)">Edit</button>
            </td>
          </tr>
        </tbody>
      </table>
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

function cancelEdit() {
  editingId.value = null
}

async function saveEdit(st: StreetType) {
  try {
    const { data } = await configApi.updateStreetType(st.id, { name: editName.value, description: editDesc.value })
    const idx = streetTypes.value.findIndex((t) => t.id === st.id)
    if (idx !== -1) streetTypes.value[idx] = data
    successMsg.value = 'Street type updated.'
    cancelEdit()
  } catch {
    errorMsg.value = 'Failed to update.'
  }
}

onMounted(load)
</script>
