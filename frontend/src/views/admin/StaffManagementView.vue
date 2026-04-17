<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Staff Management</h1>
        <p class="text-sm text-gray-500 mt-0.5">Manage staff user accounts</p>
      </div>
      <button class="btn-primary gap-2" @click="showModal = true">
        <PlusIcon class="w-4 h-4" />
        Add Staff
      </button>
    </div>

    <div v-if="errorMsg" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{{ errorMsg }}</div>
    <div v-if="successMsg" class="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">{{ successMsg }}</div>

    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
      <div v-else-if="!staffList.length" class="text-center py-12 text-gray-500">No staff accounts found.</div>
      <table v-else class="w-full text-sm">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Name</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase hidden sm:table-cell">Email</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Role</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="s in staffList" :key="s.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 font-medium text-gray-900">{{ s.full_name || `${s.first_name} ${s.last_name}` }}</td>
            <td class="px-4 py-3 text-gray-600 hidden sm:table-cell">{{ s.email }}</td>
            <td class="px-4 py-3">
              <span class="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full capitalize">
                {{ s.role?.replace(/_/g, ' ') }}
              </span>
            </td>
            <td class="px-4 py-3">
              <span
                :class="s.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'"
                class="text-xs px-2 py-0.5 rounded-full"
              >
                {{ s.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td class="px-4 py-3">
              <button
                v-if="s.is_active"
                class="text-xs text-red-600 hover:underline font-medium"
                @click="deactivateStaff(s.id)"
              >
                Deactivate
              </button>
              <button
                v-else
                class="text-xs text-green-700 hover:underline font-medium"
                @click="reactivateStaff(s.id)"
              >
                Reactivate
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add Staff Modal -->
    <TransitionRoot appear :show="showModal" as="template">
      <Dialog as="div" class="relative z-50" @close="showModal = false">
        <TransitionChild
          as="template"
          enter="duration-200 ease-out" enter-from="opacity-0" enter-to="opacity-100"
          leave="duration-150 ease-in" leave-from="opacity-100" leave-to="opacity-0"
        >
          <div class="fixed inset-0 bg-black/40" />
        </TransitionChild>

        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4">
            <TransitionChild
              as="template"
              enter="duration-200 ease-out" enter-from="opacity-0 scale-95" enter-to="opacity-100 scale-100"
              leave="duration-150 ease-in" leave-from="opacity-100 scale-100" leave-to="opacity-0 scale-95"
            >
              <DialogPanel class="w-full max-w-md bg-white rounded-2xl shadow-xl p-6">
                <DialogTitle class="text-lg font-bold text-gray-900 mb-4">Add Staff Account</DialogTitle>

                <div v-if="modalError" class="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{{ modalError }}</div>

                <form @submit.prevent="handleCreateStaff" class="space-y-4">
                  <div class="grid grid-cols-2 gap-3">
                    <div>
                      <label class="form-label text-xs">First Name</label>
                      <input v-model="newStaff.first_name" type="text" required class="form-input text-sm" />
                    </div>
                    <div>
                      <label class="form-label text-xs">Last Name</label>
                      <input v-model="newStaff.last_name" type="text" required class="form-input text-sm" />
                    </div>
                  </div>
                  <div>
                    <label class="form-label text-xs">Email</label>
                    <input v-model="newStaff.email" type="email" required class="form-input text-sm" />
                  </div>
                  <div>
                    <label class="form-label text-xs">Phone</label>
                    <input v-model="newStaff.phone" type="tel" class="form-input text-sm" />
                  </div>
                  <div>
                    <label class="form-label text-xs">Role</label>
                    <select v-model="newStaff.role" required class="form-input text-sm">
                      <option value="">Select role…</option>
                      <option value="finance">Finance</option>
                      <option value="naming_committee">Naming Committee</option>
                      <option value="committee_chairman">Committee Chairman</option>
                    </select>
                  </div>
                  <div>
                    <label class="form-label text-xs">Password</label>
                    <input v-model="newStaff.password" type="password" required minlength="8" class="form-input text-sm" />
                  </div>

                  <div class="flex justify-end gap-3 pt-2">
                    <button type="button" class="btn-secondary" @click="showModal = false">Cancel</button>
                    <button type="submit" :disabled="modalLoading" class="btn-primary">
                      {{ modalLoading ? 'Creating…' : 'Create Staff' }}
                    </button>
                  </div>
                </form>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </TransitionRoot>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { PlusIcon } from '@heroicons/vue/24/outline'
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue'
import { authApi } from '@/services/api'

interface StaffUser {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name?: string
  phone?: string
  role: string
  is_active: boolean
}

const staffList = ref<StaffUser[]>([])
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const showModal = ref(false)
const modalLoading = ref(false)
const modalError = ref('')

const newStaff = ref({
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  role: '',
  password: '',
})

async function loadStaff() {
  loading.value = true
  try {
    const { data } = await authApi.listStaff()
    staffList.value = Array.isArray(data) ? data : data.results ?? []
  } finally {
    loading.value = false
  }
}

async function handleCreateStaff() {
  modalError.value = ''
  modalLoading.value = true
  try {
    await authApi.createStaff({ ...newStaff.value })
    successMsg.value = `Staff account for ${newStaff.value.email} created.`
    showModal.value = false
    newStaff.value = { first_name: '', last_name: '', email: '', phone: '', role: '', password: '' }
    await loadStaff()
  } catch (err: unknown) {
    const e = err as { response?: { data?: Record<string, string[]> } }
    const data = e.response?.data
    if (data) {
      modalError.value = Object.entries(data)
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
        .join(' | ')
    } else {
      modalError.value = 'Failed to create staff account.'
    }
  } finally {
    modalLoading.value = false
  }
}

async function deactivateStaff(id: number) {
  if (!confirm('Deactivate this staff account?')) return
  try {
    await authApi.deleteStaff(id)
    successMsg.value = 'Staff account deactivated.'
    await loadStaff()
  } catch {
    errorMsg.value = 'Failed to deactivate.'
  }
}

async function reactivateStaff(id: number) {
  try {
    await authApi.updateStaff(id, { is_active: true })
    successMsg.value = 'Staff account reactivated.'
    await loadStaff()
  } catch {
    errorMsg.value = 'Failed to reactivate.'
  }
}

onMounted(loadStaff)
</script>
