<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Admin</p>
            <h1 class="text-white text-2xl font-bold tracking-tight">Staff Management</h1>
            <p class="text-slate-400 text-sm mt-1">Manage staff user accounts and roles</p>
          </div>
          <button class="flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white transition-all"
                  style="background: linear-gradient(135deg, #059669, #047857); box-shadow: 0 4px 14px rgba(5,150,105,0.35)"
                  @click="showModal = true">
            <PlusIcon class="w-4 h-4" />
            Add Staff
          </button>
        </div>
      </div>
    </div>

    <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-5">

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

      <!-- Search bar -->
      <div class="flex items-center gap-3 rounded-2xl p-4" style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 1px 4px rgba(0,0,0,0.05)">
        <svg class="w-4 h-4 text-slate-400 flex-shrink-0 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M17 11A6 6 0 105 11a6 6 0 0012 0z"/>
        </svg>
        <input v-model="searchQuery" type="text" placeholder="Search by name, email, or role…"
               class="flex-1 text-sm text-slate-900 bg-transparent outline-none placeholder-slate-400"
               @input="staffPage = 1" />
        <button v-if="searchQuery" @click="searchQuery = ''; staffPage = 1"
                class="text-xs text-slate-400 hover:text-slate-600 px-2 py-1 transition-colors">Clear</button>
        <span class="text-xs text-slate-400 font-medium pr-1">{{ filteredStaff.length }} of {{ staffList.length }}</span>
      </div>

      <!-- Table card -->
      <div class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
        <div class="px-6 py-5" style="border-bottom: 1px solid #f1f5f9">
          <h2 class="text-sm font-bold text-slate-900">Staff Accounts</h2>
          <p class="text-xs text-slate-500 mt-0.5">{{ filteredStaff.length }} account{{ filteredStaff.length === 1 ? '' : 's' }}</p>
        </div>

        <div v-if="loading" class="flex items-center justify-center py-12">
          <div class="w-8 h-8 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
        </div>
        <div v-else-if="!filteredStaff.length" class="flex flex-col items-center py-12 gap-2">
          <UserGroupIcon class="w-10 h-10 text-slate-300" />
          <p class="text-sm text-slate-500">{{ searchQuery ? 'No staff match your search.' : 'No staff accounts found.' }}</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0">
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Name</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider hidden sm:table-cell">Email</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Role</th>
                <th class="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                <th class="px-5 py-3.5 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(s, i) in pagedStaff" :key="s.id"
                  :style="i < pagedStaff.length - 1 ? 'border-bottom: 1px solid #f8fafc' : ''"
                  class="hover:bg-slate-50/60 transition-colors">
                <td class="px-5 py-4">
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                         style="background: linear-gradient(135deg, #059669, #047857)">
                      {{ ((s.first_name?.[0] || '') + (s.last_name?.[0] || '')).toUpperCase() || '?' }}
                    </div>
                    <span class="font-semibold text-slate-900">{{ s.full_name || `${s.first_name} ${s.last_name}` }}</span>
                  </div>
                </td>
                <td class="px-5 py-4 text-slate-500 hidden sm:table-cell">{{ s.email }}</td>
                <td class="px-5 py-4">
                  <span class="text-xs font-semibold px-2.5 py-1 rounded-full capitalize"
                        style="background: rgba(5,150,105,0.08); color: #059669; border: 1px solid rgba(5,150,105,0.18)">
                    {{ s.role?.replace(/_/g, ' ') }}
                  </span>
                </td>
                <td class="px-5 py-4">
                  <span class="text-xs font-semibold px-2.5 py-1 rounded-full"
                        :class="s.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'">
                    {{ s.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td class="px-5 py-4 text-right">
                  <button v-if="s.is_active"
                          class="text-xs font-semibold text-red-500 hover:text-red-700 transition-colors"
                          @click="deactivateStaff(s.id)">
                    Deactivate
                  </button>
                  <button v-else
                          class="text-xs font-semibold text-emerald-600 hover:text-emerald-700 transition-colors"
                          @click="reactivateStaff(s.id)">
                    Reactivate
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <!-- Pagination -->
          <div v-if="staffTotalPages > 1" class="flex items-center justify-between px-5 py-3.5"
               style="border-top: 1px solid #f1f5f9; background: #f8fafc">
            <p class="text-xs text-slate-500">
              Page {{ staffPage }} of {{ staffTotalPages }} &nbsp;·&nbsp; {{ filteredStaff.length }} total
            </p>
            <div class="flex gap-2">
              <button :disabled="staffPage <= 1"
                      class="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 border border-slate-200 hover:bg-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                      @click="staffPage--">← Prev</button>
              <button :disabled="staffPage >= staffTotalPages"
                      class="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 border border-slate-200 hover:bg-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                      @click="staffPage++">Next →</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Staff Modal -->
    <TransitionRoot appear :show="showModal" as="template">
      <Dialog as="div" class="relative z-50" @close="showModal = false">
        <TransitionChild as="template"
                         enter="duration-200 ease-out" enter-from="opacity-0" enter-to="opacity-100"
                         leave="duration-150 ease-in" leave-from="opacity-100" leave-to="opacity-0">
          <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" />
        </TransitionChild>

        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4">
            <TransitionChild as="template"
                             enter="duration-200 ease-out" enter-from="opacity-0 scale-95" enter-to="opacity-100 scale-100"
                             leave="duration-150 ease-in" leave-from="opacity-100 scale-100" leave-to="opacity-0 scale-95">
              <DialogPanel class="w-full max-w-md rounded-2xl shadow-2xl overflow-hidden" style="background: #fff">
                <div class="px-6 py-5" style="border-bottom: 1px solid #f1f5f9">
                  <DialogTitle class="text-base font-bold text-slate-900">Add Staff Account</DialogTitle>
                  <p class="text-xs text-slate-500 mt-0.5">Create a new staff login for Ibeju-Lekki LGA SNRMS</p>
                </div>

                <transition enter-active-class="transition duration-200 ease-out"
                            enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
                  <div v-if="modalError" class="mx-6 mt-5 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-3.5">
                    <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
                    </svg>
                    <p class="text-sm text-red-700">{{ modalError }}</p>
                  </div>
                </transition>

                <form @submit.prevent="handleCreateStaff" class="px-6 py-5 space-y-4" novalidate>
                  <div class="grid grid-cols-2 gap-3">
                    <div>
                      <label class="block text-sm font-semibold text-slate-700 mb-1.5">First Name <span class="text-red-500">*</span></label>
                      <input v-model="newStaff.first_name" type="text" required
                             class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
                    </div>
                    <div>
                      <label class="block text-sm font-semibold text-slate-700 mb-1.5">Last Name <span class="text-red-500">*</span></label>
                      <input v-model="newStaff.last_name" type="text" required
                             class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
                    </div>
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-1.5">Email Address <span class="text-red-500">*</span></label>
                    <input v-model="newStaff.email" type="email" required
                           class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-1.5">Phone <span class="text-slate-400 font-normal text-xs">(optional)</span></label>
                    <input v-model="newStaff.phone" type="tel" placeholder="+234 800 000 0000"
                           class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-1.5">Role <span class="text-red-500">*</span></label>
                    <select v-model="newStaff.role" required
                            class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
                      <option value="">Select role…</option>
                      <option value="finance">Finance Officer</option>
                      <option value="naming_committee">Naming Committee</option>
                      <option value="committee_chairman">Committee Chairman</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-1.5">Temporary Password <span class="text-red-500">*</span></label>
                    <input v-model="newStaff.password" type="password" required minlength="8"
                           class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
                  </div>

                  <div class="flex justify-end gap-3 pt-1">
                    <button type="button"
                            class="px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-600 border border-slate-200 hover:bg-slate-50 transition-all"
                            @click="showModal = false">
                      Cancel
                    </button>
                    <button type="submit" :disabled="modalLoading"
                            class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60"
                            style="background: linear-gradient(135deg, #059669, #047857)">
                      <svg v-if="modalLoading" class="animate-spin w-4 h-4 opacity-80" viewBox="0 0 24 24" fill="none">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                      </svg>
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
import { ref, computed, onMounted } from 'vue'
import { PlusIcon, UserGroupIcon } from '@heroicons/vue/24/outline'
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
const searchQuery = ref('')
const staffPage = ref(1)
const STAFF_PAGE_SIZE = 15

const filteredStaff = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return staffList.value
  return staffList.value.filter(s =>
    `${s.first_name} ${s.last_name} ${s.full_name ?? ''} ${s.email} ${s.role}`.toLowerCase().includes(q)
  )
})
const staffTotalPages = computed(() => Math.max(1, Math.ceil(filteredStaff.value.length / STAFF_PAGE_SIZE)))
const pagedStaff = computed(() => {
  const start = (staffPage.value - 1) * STAFF_PAGE_SIZE
  return filteredStaff.value.slice(start, start + STAFF_PAGE_SIZE)
})

const newStaff = ref({ first_name: '', last_name: '', email: '', phone: '', role: '', password: '' })

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
    modalError.value = data
      ? Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' · ')
      : 'Failed to create staff account.'
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
