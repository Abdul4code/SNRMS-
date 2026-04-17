<template>
  <div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Profile</h1>

    <!-- Profile info card -->
    <AppCard title="Personal Information" class="mb-5">
      <div v-if="profileError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{{ profileError }}</div>
      <div v-if="profileSuccess" class="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">{{ profileSuccess }}</div>

      <!-- View mode -->
      <template v-if="!editingProfile">
        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <dt class="text-xs text-gray-500 uppercase font-semibold">First Name</dt>
            <dd class="mt-1 text-gray-900">{{ auth.user?.first_name }}</dd>
          </div>
          <div>
            <dt class="text-xs text-gray-500 uppercase font-semibold">Last Name</dt>
            <dd class="mt-1 text-gray-900">{{ auth.user?.last_name }}</dd>
          </div>
          <div>
            <dt class="text-xs text-gray-500 uppercase font-semibold">Email</dt>
            <dd class="mt-1 text-gray-900">{{ auth.user?.email }}</dd>
          </div>
          <div>
            <dt class="text-xs text-gray-500 uppercase font-semibold">Phone</dt>
            <dd class="mt-1 text-gray-900">{{ auth.user?.phone || '—' }}</dd>
          </div>
          <div>
            <dt class="text-xs text-gray-500 uppercase font-semibold">Role</dt>
            <dd class="mt-1">
              <span class="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full capitalize">
                {{ auth.user?.role?.replace(/_/g, ' ') }}
              </span>
            </dd>
          </div>
          <div>
            <dt class="text-xs text-gray-500 uppercase font-semibold">Member Since</dt>
            <dd class="mt-1 text-gray-900">{{ formatDate(auth.user?.created_at) }}</dd>
          </div>
        </dl>
        <div class="mt-4">
          <button class="btn-secondary text-sm" @click="startEditProfile">Edit Profile</button>
        </div>
      </template>

      <!-- Edit mode -->
      <template v-else>
        <form @submit.prevent="saveProfile" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="form-label">First Name</label>
              <input v-model="profileForm.first_name" type="text" required class="form-input" />
            </div>
            <div>
              <label class="form-label">Last Name</label>
              <input v-model="profileForm.last_name" type="text" required class="form-input" />
            </div>
          </div>
          <div>
            <label class="form-label">Phone</label>
            <input v-model="profileForm.phone" type="tel" class="form-input" />
          </div>
          <div class="flex gap-3">
            <button type="submit" :disabled="profileSaving" class="btn-primary text-sm">
              {{ profileSaving ? 'Saving…' : 'Save Changes' }}
            </button>
            <button type="button" class="btn-secondary text-sm" @click="editingProfile = false">Cancel</button>
          </div>
        </form>
      </template>
    </AppCard>

    <!-- Change password card -->
    <AppCard title="Change Password">
      <div v-if="pwdError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{{ pwdError }}</div>
      <div v-if="pwdSuccess" class="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">{{ pwdSuccess }}</div>

      <form @submit.prevent="savePassword" class="space-y-4">
        <div>
          <label class="form-label">Current Password</label>
          <input v-model="pwdForm.old_password" type="password" required class="form-input" />
        </div>
        <div>
          <label class="form-label">New Password</label>
          <input v-model="pwdForm.new_password" type="password" required minlength="8" class="form-input" />
        </div>
        <div>
          <label class="form-label">Confirm New Password</label>
          <input v-model="pwdForm.confirm_password" type="password" required class="form-input" />
          <p v-if="pwdForm.confirm_password && pwdForm.new_password !== pwdForm.confirm_password" class="mt-1 text-xs text-red-600">
            Passwords do not match
          </p>
        </div>
        <button
          type="submit"
          :disabled="pwdSaving || pwdForm.new_password !== pwdForm.confirm_password"
          class="btn-primary text-sm"
        >
          {{ pwdSaving ? 'Updating…' : 'Update Password' }}
        </button>
      </form>
    </AppCard>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppCard from '@/components/AppCard.vue'

const auth = useAuthStore()

// ── Profile edit ─────────────────────────────────────────────────────────────
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

// ── Password change ───────────────────────────────────────────────────────────
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
    pwdError.value =
      e.response?.data?.old_password?.[0] ||
      e.response?.data?.detail ||
      'Failed to update password.'
  } finally {
    pwdSaving.value = false
  }
}

function formatDate(d?: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-NG', { day: 'numeric', month: 'long', year: 'numeric' })
}
</script>
