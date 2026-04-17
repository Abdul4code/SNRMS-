<template>
  <div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Breadcrumb -->
    <nav class="text-sm text-gray-500 mb-6 flex items-center gap-2">
      <RouterLink to="/applications" class="hover:text-blue-600">My Applications</RouterLink>
      <span>/</span>
      <span class="text-gray-900">New Application</span>
    </nav>

    <div class="bg-white rounded-xl border border-gray-200 p-8">
      <h1 class="text-xl font-bold text-gray-900 mb-1">New Street Name Application</h1>
      <p class="text-sm text-gray-500 mb-6">Submit a request to register a new street name in Ibeju-Lekki LGA.</p>

      <!-- Error -->
      <div v-if="errorMessage" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
        {{ errorMessage }}
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-5">
        <div>
          <label class="form-label">Proposed Street Name <span class="text-red-500">*</span></label>
          <input
            v-model="form.proposed_street_name"
            type="text"
            required
            class="form-input"
            placeholder="e.g. Bola Ahmed Tinubu Street"
          />
          <p class="mt-1 text-xs text-gray-500">Enter the full proposed name for the street.</p>
        </div>

        <div>
          <label class="form-label">Street Type <span class="text-red-500">*</span></label>
          <select v-model="form.street_type" required class="form-input">
            <option value="" disabled>Select a street type…</option>
            <option v-for="st in streetTypes" :key="st.id" :value="st.id">
              {{ st.name }}
            </option>
          </select>
          <p v-if="streetTypesLoading" class="mt-1 text-xs text-gray-400">Loading street types…</p>
        </div>

        <div>
          <label class="form-label">Location Description <span class="text-red-500">*</span></label>
          <textarea
            v-model="form.location_description"
            rows="4"
            required
            class="form-input resize-none"
            placeholder="Describe the location — nearby landmarks, coordinates, neighbourhood, etc."
          />
        </div>

        <div class="flex items-center gap-3 pt-2">
          <button type="submit" :disabled="submitting" class="btn-primary">
            <span v-if="submitting">Submitting…</span>
            <span v-else>Create Application</span>
          </button>
          <RouterLink to="/applications" class="btn-secondary">Cancel</RouterLink>
        </div>
      </form>
    </div>

    <!-- Info box -->
    <div class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-xl text-sm text-blue-700">
      <p class="font-medium mb-1">What happens next?</p>
      <ol class="list-decimal list-inside space-y-1 text-blue-600">
        <li>Your application is saved as a draft. Review and submit it.</li>
        <li>A Stage A processing fee will be required upon submission.</li>
        <li>The naming committee will review your application.</li>
        <li>The Chairman approves or rejects the committee recommendation.</li>
        <li>A Stage C issuance fee is required before the certificate is issued.</li>
      </ol>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { applicationApi, configApi } from '@/services/api'

interface StreetType { id: number; name: string }

const router = useRouter()
const form = ref({ proposed_street_name: '', street_type: '', location_description: '' })
const streetTypes = ref<StreetType[]>([])
const streetTypesLoading = ref(false)
const submitting = ref(false)
const errorMessage = ref('')

async function handleSubmit() {
  errorMessage.value = ''
  submitting.value = true
  try {
    const { data } = await applicationApi.create({
      proposed_street_name: form.value.proposed_street_name,
      street_type: form.value.street_type,
      location_description: form.value.location_description,
    })
    router.push(`/applications/${data.id}`)
  } catch (err: unknown) {
    const e = err as { response?: { data?: Record<string, string[]> } }
    const data = e.response?.data
    if (data) {
      const msgs = Object.entries(data)
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
        .join(' | ')
      errorMessage.value = msgs
    } else {
      errorMessage.value = 'Failed to create application. Please try again.'
    }
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  streetTypesLoading.value = true
  try {
    const { data } = await configApi.listStreetTypes()
    streetTypes.value = Array.isArray(data) ? data : data.results ?? []
  } finally {
    streetTypesLoading.value = false
  }
})
</script>
