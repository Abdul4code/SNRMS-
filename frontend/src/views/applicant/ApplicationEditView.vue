<template>
  <div class="min-h-screen" style="background:#f1f5f9">
    <!-- Header band -->
    <div style="background:#0a1628; border-bottom:1px solid rgba(255,255,255,0.06)">
      <div class="max-w-2xl mx-auto px-4 sm:px-6 py-7">
        <nav class="flex items-center gap-2 text-xs text-slate-400 mb-4">
          <RouterLink to="/applications" class="hover:text-emerald-400 transition-colors">My Applications</RouterLink>
          <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
          <RouterLink :to="`/applications/${id}`" class="hover:text-emerald-400 transition-colors font-mono">Application</RouterLink>
          <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
          <span class="text-slate-300">Edit</span>
        </nav>
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Edit</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">Edit Application</h1>
        <p class="text-slate-400 text-sm mt-1">You can change these details until a payment is made.</p>
      </div>
    </div>

    <div class="max-w-2xl mx-auto px-4 sm:px-6 py-8">
      <div v-if="loading" class="flex flex-col items-center justify-center py-16 gap-3">
        <div class="w-9 h-9 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
        <p class="text-sm text-slate-500">Loading application…</p>
      </div>

      <!-- Locked (already paid) -->
      <div v-else-if="!editable" class="rounded-2xl p-6 text-center" style="background:#fff; border:1px solid #e2e8f0">
        <p class="text-sm font-bold text-slate-800">This application can no longer be edited</p>
        <p class="text-xs text-slate-500 mt-1 mb-4">A payment has already been made, so its details are locked.</p>
        <RouterLink :to="`/applications/${id}`" class="inline-flex items-center justify-center px-5 py-2.5 rounded-xl text-sm font-semibold text-white" style="background:#059669">Back to application</RouterLink>
      </div>

      <div v-else class="rounded-2xl overflow-hidden" style="background:#fff; border:1px solid #e2e8f0; box-shadow:0 2px 8px rgba(0,0,0,0.06)">
        <div class="px-6 py-5" style="border-bottom:1px solid #f1f5f9">
          <h2 class="text-base font-bold text-slate-900">Application Details</h2>
        </div>

        <div v-if="errorMessage" class="mx-6 mt-5 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-4">
          <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/></svg>
          <p class="text-sm text-red-700">{{ errorMessage }}</p>
        </div>

        <form @submit.prevent="handleSubmit" class="px-6 py-5 space-y-5" novalidate>
          <!-- Street name -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">Proposed Street Name <span class="text-red-500">*</span></label>
            <input v-if="!isLegacy" v-model="form.proposed_street_name" type="text" required
                   placeholder="e.g. Chief Bola Tinubu Boulevard"
                   class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white" />
            <div v-else class="rounded-xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm text-slate-700">
              {{ form.proposed_street_name }}
              <span class="block text-xs text-slate-400 mt-0.5">The name of a validated street can't be changed here.</span>
            </div>
          </div>

          <!-- Street type -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">Street Type <span class="text-red-500">*</span></label>
            <div class="relative">
              <select v-model="form.street_type" required
                      class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 pr-10 text-sm appearance-none focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white">
                <option value="" disabled>Select a street type</option>
                <option v-for="t in streetTypes" :key="t.id" :value="t.id">{{ t.name }}</option>
              </select>
              <ChevronDownIcon class="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
            <p class="mt-1.5 text-xs text-slate-500">The street type sets the Stage C (street-name) fee.</p>
          </div>

          <!-- Locality -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">Locality / Town / Estate <span class="text-red-500">*</span></label>
            <div class="relative">
              <select v-model="form.locality" required
                      class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 pr-10 text-sm appearance-none focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white">
                <option value="" disabled>Select your locality</option>
                <option v-for="l in localityOptions" :key="l" :value="l">{{ l }}</option>
              </select>
              <ChevronDownIcon class="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
            <p class="mt-1.5 text-xs text-slate-500">To change the location on the map, withdraw this application and create a new one.</p>
          </div>

          <div class="flex gap-3 pt-1">
            <button type="submit" :disabled="submitting || !form.proposed_street_name || !form.street_type || !form.locality"
                    class="flex items-center justify-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold text-white disabled:opacity-60"
                    style="background:linear-gradient(135deg,#059669,#047857)">
              {{ submitting ? 'Saving…' : 'Save changes' }}
            </button>
            <RouterLink :to="`/applications/${id}`" class="flex items-center px-5 py-3 rounded-xl text-sm font-semibold text-slate-600 border border-slate-200 hover:bg-slate-50">Cancel</RouterLink>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { ChevronRightIcon, ChevronDownIcon } from '@heroicons/vue/24/outline'
import { applicationApi, configApi } from '@/services/api'

const route = useRoute()
const router = useRouter()
const id = route.params.id as string

const EDITABLE = ['draft', 'submitted', 'awaiting_stage_a_payment']

const loading = ref(true)
const submitting = ref(false)
const editable = ref(true)
const isLegacy = ref(false)
const errorMessage = ref('')

const form = ref({ proposed_street_name: '', street_type: '' as string | number, locality: '', ward: '' })
const streetTypes = ref<{ id: string | number; name: string }[]>([])
const communityToWard = ref<Record<string, string>>({})
const localityOptions = computed(() => {
  const set = new Set(Object.keys(communityToWard.value))
  if (form.value.locality) set.add(form.value.locality)  // keep the current value selectable
  return Array.from(set).sort((a, b) => a.localeCompare(b))
})

onMounted(async () => {
  try {
    const [appRes, stRes, lwRes] = await Promise.all([
      applicationApi.get(id),
      configApi.listStreetTypes().catch(() => ({ data: [] })),
      configApi.getLocalityWards().catch(() => ({ data: { community_to_ward: {} } })),
    ])
    const app = appRes.data
    editable.value = EDITABLE.includes(app.status)
    isLegacy.value = !!app.is_legacy
    form.value = {
      proposed_street_name: app.proposed_street_name || '',
      street_type: app.street_type || '',
      locality: app.locality || '',
      ward: app.ward || '',
    }
    const st = stRes.data
    streetTypes.value = Array.isArray(st) ? st : (st.results ?? [])
    communityToWard.value = lwRes.data.community_to_ward || {}
  } catch {
    errorMessage.value = 'Could not load this application.'
  } finally {
    loading.value = false
  }
})

async function handleSubmit() {
  errorMessage.value = ''
  submitting.value = true
  try {
    const payload: Record<string, unknown> = {
      street_type: form.value.street_type,
      locality: form.value.locality,
      // Re-derive the ward from the chosen locality when we know it; otherwise keep the existing one.
      ward: communityToWard.value[form.value.locality] || form.value.ward,
    }
    if (!isLegacy.value) payload.proposed_street_name = form.value.proposed_street_name
    await applicationApi.update(id, payload)
    router.push(`/applications/${id}`)
  } catch (err: unknown) {
    const e = err as { response?: { data?: Record<string, string[]> | { detail?: string } } }
    const d = e.response?.data
    if (d && typeof d === 'object' && !Array.isArray(d)) {
      errorMessage.value = Object.entries(d).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' · ')
    } else {
      errorMessage.value = 'Could not save your changes. Please try again.'
    }
  } finally {
    submitting.value = false
  }
}
</script>
