<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <!-- Page header band -->
    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-2xl mx-auto px-4 sm:px-6 py-5">
        <nav class="flex items-center gap-2 text-xs text-slate-400 mb-3">
          <RouterLink to="/applications" class="hover:text-emerald-400 transition-colors">My Applications</RouterLink>
          <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
          <span class="text-slate-300">New Application</span>
        </nav>
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1">New Request</p>
        <h1 class="text-white text-xl font-bold tracking-tight">Street Name Application</h1>
        <p class="text-slate-400 text-sm mt-0.5">Submit a request to register a new street name in Ibeju-Lekki LGA</p>
      </div>
    </div>

    <div class="max-w-2xl mx-auto px-4 sm:px-6 py-6 space-y-4">

      <!-- Main form card -->
      <div class="rounded-2xl overflow-hidden"
           style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
        <div class="px-6 py-5" style="border-bottom: 1px solid #f1f5f9">
          <h2 class="text-base font-bold text-slate-900">Application Details</h2>
          <p class="text-xs text-slate-500 mt-0.5">All fields marked with * are required</p>
        </div>

        <!-- Error -->
        <transition enter-active-class="transition duration-200 ease-out"
                    enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
          <div v-if="errorMessage"
               class="mx-6 mt-5 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-4">
            <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
            </svg>
            <p class="text-sm text-red-700">{{ errorMessage }}</p>
          </div>
        </transition>

        <form @submit.prevent="handleSubmit" class="px-6 py-5 space-y-5" novalidate>

          <!-- Proposed street name -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              Proposed Street Name <span class="text-red-500">*</span>
            </label>
            <input v-model="form.proposed_street_name" type="text" required
                   placeholder="e.g. Chief Bola Tinubu Boulevard"
                   class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
            <p class="mt-1.5 text-xs text-slate-500">Enter the full proposed name including the street designation (Street, Avenue, etc.)</p>
          </div>

          <!-- Street type -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              Street Type <span class="text-red-500">*</span>
            </label>
            <div class="relative">
              <select v-model="form.street_type" required
                      :disabled="streetTypesLoading"
                      class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all appearance-none disabled:opacity-60">
                <option value="" disabled>{{ streetTypesLoading ? 'Loading…' : 'Select a street type' }}</option>
                <option v-for="st in streetTypes" :key="st.id" :value="st.id">
                  {{ st.name }}
                </option>
              </select>
              <div class="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none">
                <ChevronDownIcon class="w-4 h-4 text-slate-400" />
              </div>
            </div>
          </div>

          <!-- Ward -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              Ward <span class="text-red-500">*</span>
            </label>
            <div class="relative">
              <select v-model="form.ward" required
                      class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all appearance-none">
                <option value="" disabled>Select a ward</option>
                <option value="ward_a">Ward A - Central</option>
                <option value="ward_b">Ward B - North</option>
                <option value="ward_c">Ward C - South</option>
              </select>
              <div class="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none">
                <ChevronDownIcon class="w-4 h-4 text-slate-400" />
              </div>
            </div>
          </div>

          <!-- Geolocation capture -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              Street Location <span class="text-red-500">*</span>
            </label>

            <!-- Idle state -->
            <div v-if="geoState === 'idle'" class="rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 p-6 flex flex-col items-center gap-3">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background: rgba(5,150,105,0.08); border: 1px solid rgba(5,150,105,0.15)">
                <MapPinIcon class="w-5 h-5" style="color: #059669" />
              </div>
              <div class="text-center">
                <p class="text-sm font-semibold text-slate-700">Capture GPS Location</p>
                <p class="text-xs text-slate-500 mt-0.5">Use your device's GPS to pinpoint the street location</p>
              </div>
              <button type="button"
                      class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all"
                      style="background: linear-gradient(135deg, #059669, #047857); box-shadow: 0 4px 14px rgba(5,150,105,0.3)"
                      @click="captureLocation">
                <MapPinIcon class="w-4 h-4" />
                Capture My Location
              </button>
              <p v-if="!geoSupported" class="text-xs text-red-500">Geolocation is not supported by your browser.</p>
            </div>

            <!-- Loading state -->
            <div v-else-if="geoState === 'loading'" class="rounded-xl border border-slate-200 bg-slate-50 p-6 flex flex-col items-center gap-3">
              <div class="w-10 h-10 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
              <p class="text-sm text-slate-600 font-medium">Acquiring your location…</p>
              <p class="text-xs text-slate-400">Please allow location access if prompted</p>
            </div>

            <!-- Success state -->
            <div v-else-if="geoState === 'success'" class="rounded-xl overflow-hidden" style="border: 1px solid rgba(5,150,105,0.2); background: rgba(5,150,105,0.04)">
              <div class="flex items-center gap-3 px-4 py-3" style="border-bottom: 1px solid rgba(5,150,105,0.12)">
                <div class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style="background: rgba(5,150,105,0.15)">
                  <CheckCircleIcon class="w-4 h-4" style="color: #059669" />
                </div>
                <p class="text-sm font-semibold" style="color: #047857">Location Captured</p>
                <button type="button" class="ml-auto text-xs font-semibold text-slate-400 hover:text-slate-600 transition-colors flex items-center gap-1" @click="resetGeo">
                  <ArrowPathIcon class="w-3.5 h-3.5" />
                  Re-capture
                </button>
              </div>
              <div class="px-4 py-3 grid grid-cols-3 gap-3">
                <div class="text-center">
                  <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Latitude</p>
                  <p class="text-sm font-mono font-semibold text-slate-800">{{ geoCoords.lat }}</p>
                </div>
                <div class="text-center">
                  <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Longitude</p>
                  <p class="text-sm font-mono font-semibold text-slate-800">{{ geoCoords.lng }}</p>
                </div>
                <div class="text-center">
                  <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Accuracy</p>
                  <p class="text-sm font-mono font-semibold text-slate-800">±{{ geoCoords.accuracy }}m</p>
                </div>
              </div>
            </div>

            <!-- Error state -->
            <div v-else-if="geoState === 'error'" class="rounded-xl border border-red-100 bg-red-50 p-5 flex flex-col items-center gap-3">
              <div class="w-9 h-9 rounded-xl flex items-center justify-center" style="background: rgba(239,68,68,0.1)">
                <ExclamationCircleIcon class="w-5 h-5 text-red-500" />
              </div>
              <div class="text-center">
                <p class="text-sm font-semibold text-red-700">Location Access Failed</p>
                <p class="text-xs text-red-500 mt-0.5">{{ geoError }}</p>
              </div>
              <button type="button"
                      class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold border border-red-200 bg-white text-red-600 hover:bg-red-50 transition-all"
                      @click="captureLocation">
                <ArrowPathIcon class="w-4 h-4" />
                Try Again
              </button>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-3 pt-1">
            <button type="submit"
                    :disabled="submitting || !form.proposed_street_name || !form.street_type || !form.ward || geoState !== 'success'"
                    class="flex items-center justify-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold text-white transition-all active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed"
                    style="background: linear-gradient(135deg, #059669, #047857); box-shadow: 0 4px 16px rgba(5,150,105,0.3)">
              <svg v-if="submitting" class="animate-spin w-4 h-4 opacity-80" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              <span>{{ submitting ? 'Submitting…' : 'Create Application' }}</span>
            </button>
            <RouterLink to="/applications"
                        class="flex items-center px-5 py-3 rounded-xl text-sm font-semibold text-slate-600 border border-slate-200 hover:bg-slate-50 transition-all">
              Cancel
            </RouterLink>
          </div>
        </form>
      </div>

      <!-- What happens next -->
      <div class="rounded-2xl p-5"
           style="background: linear-gradient(135deg, #050f1e, #0a1a2e); border: 1px solid rgba(255,255,255,0.08)">
        <div class="flex items-center gap-2.5 mb-4">
          <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
               style="background: rgba(5,150,105,0.18); border: 1px solid rgba(52,211,153,0.2)">
            <InformationCircleIcon class="w-4 h-4" style="color: #34d399" />
          </div>
          <h3 class="text-white text-sm font-semibold">What happens next?</h3>
        </div>
        <ol class="space-y-3">
          <li v-for="(step, i) in nextSteps" :key="i" class="flex items-start gap-3">
            <span class="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold mt-0.5"
                  style="background: rgba(5,150,105,0.2); color: #34d399; border: 1px solid rgba(52,211,153,0.25)">
              {{ i + 1 }}
            </span>
            <p class="text-slate-400 text-xs leading-relaxed">{{ step }}</p>
          </li>
        </ol>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import {
  ChevronRightIcon, ChevronDownIcon, InformationCircleIcon,
  MapPinIcon, CheckCircleIcon, ArrowPathIcon, ExclamationCircleIcon,
} from '@heroicons/vue/24/outline'
import { applicationApi, configApi } from '@/services/api'

interface StreetType { id: number; name: string }

const router = useRouter()
const form = ref({ proposed_street_name: '', street_type: '', ward: '', location_description: '' })
const streetTypes = ref<StreetType[]>([])
const streetTypesLoading = ref(false)
const submitting = ref(false)
const errorMessage = ref('')

const geoSupported = 'geolocation' in navigator
const geoState = ref<'idle' | 'loading' | 'success' | 'error'>('idle')
const geoError = ref('')
const geoCoords = ref({ lat: '', lng: '', accuracy: '' })

function captureLocation() {
  if (!geoSupported) return
  geoState.value = 'loading'
  geoError.value = ''
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude.toFixed(6)
      const lng = pos.coords.longitude.toFixed(6)
      const acc = Math.round(pos.coords.accuracy)
      geoCoords.value = { lat, lng, accuracy: String(acc) }
      form.value.location_description = `${lat},${lng}`
      geoState.value = 'success'
    },
    (err) => {
      const messages: Record<number, string> = {
        1: 'Location access was denied. Please allow location permission in your browser settings.',
        2: 'Location unavailable. Make sure GPS is enabled on your device.',
        3: 'Location request timed out. Please try again.',
      }
      geoError.value = messages[err.code] ?? 'Unable to determine location.'
      geoState.value = 'error'
    },
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
  )
}

function resetGeo() {
  geoState.value = 'idle'
  geoCoords.value = { lat: '', lng: '', accuracy: '' }
  form.value.location_description = ''
}

const nextSteps = [
  'Your application is saved and reviewed by the finance team for Stage A processing fees.',
  'Upon payment confirmation, the naming committee formally evaluates your proposed street name.',
  'The Committee Chairman reviews the committee recommendation and gives a final decision.',
  'After approval, a Stage C certificate issuance fee is required before your certificate is printed.',
  'Your street name is officially registered and a certificate of naming is issued.',
]

async function handleSubmit() {
  errorMessage.value = ''
  submitting.value = true
  try {
    const { data } = await applicationApi.create({
      proposed_street_name: form.value.proposed_street_name,
      street_type: form.value.street_type,
      ward: form.value.ward,
      location_description: form.value.location_description,
    })
    router.push(`/applications/${data.id}`)
  } catch (err: unknown) {
    const e = err as { response?: { data?: Record<string, string[]> } }
    const data = e.response?.data
    errorMessage.value = data
      ? Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' · ')
      : 'Failed to create application. Please try again.'
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
