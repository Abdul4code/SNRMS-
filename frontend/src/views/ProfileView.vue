<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <!-- Header band -->
    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Account</p>
        <div class="flex items-center gap-4">
          <div class="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold text-white flex-shrink-0"
               style="background: linear-gradient(135deg, #059669, #047857); box-shadow: 0 4px 14px rgba(5,150,105,0.4)">
            {{ initials }}
          </div>
          <div>
            <h1 class="text-white text-2xl font-bold tracking-tight">{{ auth.user?.full_name }}</h1>
            <div class="flex items-center gap-2 mt-1.5">
              <span class="text-xs font-semibold px-2 py-0.5 rounded-full"
                    style="background: rgba(5,150,105,0.2); color: #34d399; border: 1px solid rgba(52,211,153,0.25)">
                {{ roleLabel }}
              </span>
              <span class="text-slate-400 text-xs">·</span>
              <span class="text-slate-400 text-xs">Member since {{ formatDate(auth.user?.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-2xl mx-auto px-4 sm:px-6 py-8 space-y-5">

      <!-- Personal info card -->
      <div class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
        <div class="px-6 py-5 flex items-center justify-between" style="border-bottom: 1px solid #f1f5f9">
          <h2 class="text-sm font-bold text-slate-900">Personal Information</h2>
          <button v-if="!editingProfile" class="text-xs font-semibold text-emerald-600 hover:text-emerald-700 transition-colors"
                  @click="startEditProfile">
            Edit
          </button>
        </div>

        <!-- Alerts -->
        <transition enter-active-class="transition duration-200 ease-out"
                    enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
          <div v-if="profileError" class="mx-5 mt-5 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-3.5">
            <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
            </svg>
            <p class="text-sm text-red-700">{{ profileError }}</p>
          </div>
        </transition>
        <transition enter-active-class="transition duration-200 ease-out"
                    enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
          <div v-if="profileSuccess" class="mx-5 mt-5 flex items-start gap-3 rounded-xl border border-emerald-100 bg-emerald-50 p-3.5">
            <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/>
            </svg>
            <p class="text-sm text-emerald-700">{{ profileSuccess }}</p>
          </div>
        </transition>

        <!-- View mode -->
        <template v-if="!editingProfile">
          <dl class="p-5 grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">First Name</dt>
              <dd class="text-sm font-semibold text-slate-900">{{ auth.user?.first_name }}</dd>
            </div>
            <div>
              <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Last Name</dt>
              <dd class="text-sm font-semibold text-slate-900">{{ auth.user?.last_name }}</dd>
            </div>
            <div>
              <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Email Address</dt>
              <dd class="text-sm text-slate-700">{{ auth.user?.email }}</dd>
            </div>
            <div>
              <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Phone Number</dt>
              <dd class="text-sm text-slate-700">{{ auth.user?.phone || '—' }}</dd>
            </div>
          </dl>
        </template>

        <!-- Edit mode -->
        <template v-else>
          <form @submit.prevent="saveProfile" class="p-5 space-y-4" novalidate>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1.5">First Name <span class="text-red-500">*</span></label>
                <input v-model="profileForm.first_name" type="text" required
                       class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
              </div>
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1.5">Last Name <span class="text-red-500">*</span></label>
                <input v-model="profileForm.last_name" type="text" required
                       class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
              </div>
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1.5">Phone Number</label>
              <input v-model="profileForm.phone" type="tel" placeholder="+234 800 000 0000"
                     class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
            </div>
            <div class="flex gap-3">
              <button type="submit" :disabled="profileSaving"
                      class="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60"
                      style="background: linear-gradient(135deg, #059669, #047857)">
                <svg v-if="profileSaving" class="animate-spin w-4 h-4 opacity-80" viewBox="0 0 24 24" fill="none">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                {{ profileSaving ? 'Saving…' : 'Save Changes' }}
              </button>
              <button type="button"
                      class="px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-600 border border-slate-200 hover:bg-slate-50 transition-all"
                      @click="editingProfile = false">
                Cancel
              </button>
            </div>
          </form>
        </template>
      </div>

      <!-- Change password card -->
      <div class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
        <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
          <h2 class="text-sm font-bold text-slate-900">Change Password</h2>
        </div>

        <transition enter-active-class="transition duration-200 ease-out"
                    enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
          <div v-if="pwdError" class="mx-5 mt-5 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-3.5">
            <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
            </svg>
            <p class="text-sm text-red-700">{{ pwdError }}</p>
          </div>
        </transition>
        <transition enter-active-class="transition duration-200 ease-out"
                    enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
          <div v-if="pwdSuccess" class="mx-5 mt-5 flex items-start gap-3 rounded-xl border border-emerald-100 bg-emerald-50 p-3.5">
            <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/>
            </svg>
            <p class="text-sm text-emerald-700">{{ pwdSuccess }}</p>
          </div>
        </transition>

        <form @submit.prevent="savePassword" class="p-5 space-y-4" novalidate>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">Current Password <span class="text-red-500">*</span></label>
            <input v-model="pwdForm.old_password" type="password" required
                   class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
          </div>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">New Password <span class="text-red-500">*</span></label>
            <input v-model="pwdForm.new_password" type="password" required minlength="8"
                   class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
          </div>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">Confirm New Password <span class="text-red-500">*</span></label>
            <input v-model="pwdForm.confirm_password" type="password" required
                   :class="['block w-full rounded-xl border bg-slate-50 px-4 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:border-transparent focus:bg-white transition-all',
                            pwdForm.confirm_password && pwdForm.new_password !== pwdForm.confirm_password
                              ? 'border-red-300 focus:ring-red-400'
                              : 'border-slate-200 focus:ring-emerald-500']"/>
            <p v-if="pwdForm.confirm_password && pwdForm.new_password !== pwdForm.confirm_password"
               class="mt-1 text-xs text-red-500">Passwords do not match</p>
          </div>
          <button type="submit"
                  :disabled="pwdSaving || pwdForm.new_password !== pwdForm.confirm_password || !pwdForm.old_password"
                  class="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                  style="background: linear-gradient(135deg, #059669, #047857)">
            <svg v-if="pwdSaving" class="animate-spin w-4 h-4 opacity-80" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            {{ pwdSaving ? 'Updating…' : 'Update Password' }}
          </button>
        </form>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const initials = computed(() => {
  const u = auth.user
  if (!u) return '?'
  if (u.first_name && u.last_name) return (u.first_name[0] + u.last_name[0]).toUpperCase()
  return (u.email?.[0] ?? '?').toUpperCase()
})

const roleLabel = computed(() => {
  const map: Record<string, string> = {
    applicant: 'Applicant',
    finance: 'Finance Officer',
    naming_committee: 'Naming Committee',
    committee_chairman: 'Committee Chairman',
  }
  return map[auth.user?.role ?? ''] ?? auth.user?.role ?? ''
})

const editingProfile = ref(false)
const profileSaving = ref(false)
const profileError = ref('')
const profileSuccess = ref('')
const profileForm = ref({ first_name: '', last_name: '', phone: '' })

function startEditProfile() {
  profileForm.value = {
    first_name: auth.user?.first_name ?? '',
    last_name: auth.user?.last_name ?? '',
    phone: auth.user?.phone ?? '',
  }
  editingProfile.value = true
  profileError.value = ''
  profileSuccess.value = ''
}

async function saveProfile() {
  profileError.value = ''
  profileSaving.value = true
  try {
    await auth.updateProfile({ ...profileForm.value })
    profileSuccess.value = 'Profile updated successfully.'
    editingProfile.value = false
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    profileError.value = e.response?.data?.detail || 'Failed to update profile.'
  } finally {
    profileSaving.value = false
  }
}

const pwdSaving = ref(false)
const pwdError = ref('')
const pwdSuccess = ref('')
const pwdForm = ref({ old_password: '', new_password: '', confirm_password: '' })

async function savePassword() {
  if (pwdForm.value.new_password !== pwdForm.value.confirm_password) return
  pwdError.value = ''
  pwdSaving.value = true
  try {
    await auth.changePassword({
      old_password: pwdForm.value.old_password,
      new_password: pwdForm.value.new_password,
    })
    pwdSuccess.value = 'Password updated successfully.'
    pwdForm.value = { old_password: '', new_password: '', confirm_password: '' }
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string; old_password?: string[] } } }
    pwdError.value = e.response?.data?.old_password?.[0] || e.response?.data?.detail || 'Failed to update password.'
  } finally {
    pwdSaving.value = false
  }
}

function formatDate(d?: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-NG', { day: 'numeric', month: 'long', year: 'numeric' })
}
</script>
