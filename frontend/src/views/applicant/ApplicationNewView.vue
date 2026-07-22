<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <!-- Page header band -->
    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-2xl mx-auto px-4 sm:px-6 py-7">
        <nav class="flex items-center gap-2 text-xs text-slate-400 mb-4">
          <RouterLink to="/applications" class="hover:text-emerald-400 transition-colors">My Applications</RouterLink>
          <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
          <span class="text-slate-300">New Application</span>
        </nav>
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">New Request</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">Street Name Application</h1>
        <p class="text-slate-400 text-sm mt-1">Submit a request to register a new street name in Ibeju-Lekki LGA</p>
      </div>
    </div>

    <div class="max-w-2xl mx-auto px-4 sm:px-6 py-8 space-y-5">

      <!-- Main form card -->
      <div class="rounded-2xl overflow-hidden"
           style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
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
            <p class="mt-1.5 text-xs text-slate-500">Enter the proposed name of the street </p>

            <!-- Live duplicate check -->
            <div v-if="dupChecking" class="mt-2 text-xs text-slate-400">Checking the registry for this name…</div>
            <div v-else-if="dup && dup.verdict === 'duplicate'" class="mt-2 rounded-xl border border-red-200 bg-red-50 p-3">
              <p class="text-sm font-bold text-red-700">This street name already exists.</p>
              <p class="text-xs text-red-600 mt-0.5">
                A street named "{{ form.proposed_street_name }}" is already in the registry{{ dup.name_matches[0]?.locality ? ' at ' + dup.name_matches[0].locality : '' }}. You cannot register a duplicate name.
              </p>
              <ul class="mt-1.5 space-y-0.5">
                <li v-for="m in dup.name_matches.slice(0,3)" :key="m.code" class="text-xs text-red-600">
                  • {{ m.name }} <span class="font-mono text-red-400">{{ m.code }}</span>
                  <span v-if="m.locality"> — {{ m.locality }}</span>
                  <span v-if="m.distance_m != null"> ({{ m.distance_m }}m away)</span>
                </li>
              </ul>
            </div>
            <div v-else-if="dup && dup.verdict === 'possible'" class="mt-2 rounded-xl border border-amber-200 bg-amber-50 p-3">
              <p class="text-sm font-bold text-amber-700">A street with this name exists elsewhere.</p>
              <p class="text-xs text-amber-600 mt-0.5">
                "{{ form.proposed_street_name }}" already exists in another locality. It may still be allowed here, but the committee will review carefully. Setting your locality helps confirm.
              </p>
            </div>
            <div v-else-if="dup && dup.verdict === 'clear' && form.proposed_street_name.length >= 3" class="mt-2 text-xs font-medium" style="color:#059669">
              ✓ No existing street with this name — good to go.
              <span v-if="dup.nearby.length" class="text-slate-400 font-normal">({{ dup.nearby.length }} named street{{ dup.nearby.length > 1 ? 's' : '' }} nearby)</span>
            </div>
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

            <!-- Fee preview -->
            <transition enter-active-class="transition ease-out duration-200"
                        enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0"
                        leave-active-class="transition ease-in duration-100"
                        leave-from-class="opacity-100 translate-y-0" leave-to-class="opacity-0 -translate-y-1">
              <div v-if="form.street_type"
                   class="mt-2 rounded-xl px-4 py-3"
                   style="background: rgba(5,150,105,0.06); border: 1px solid rgba(5,150,105,0.15)">
                <div v-if="feePreview.loading" class="flex items-center gap-2">
                  <div class="w-3.5 h-3.5 rounded-full border-2 border-emerald-300 border-t-emerald-600 animate-spin flex-shrink-0"></div>
                  <span class="text-xs text-emerald-700">Loading fee estimate…</span>
                </div>
                <div v-else-if="feePreview.error" class="text-xs text-red-500">{{ feePreview.error }}</div>
                <div v-else>
                  <p class="text-xs font-bold text-emerald-800 mb-2 flex items-center gap-1.5">
                    <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                    </svg>
                    Estimated Fees
                  </p>
                  <div class="grid grid-cols-2 gap-3">
                    <div class="rounded-lg px-3 py-2" style="background: rgba(255,255,255,0.7)">
                      <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Stage A · Due now</p>
                      <p class="text-sm font-bold text-slate-900">₦{{ formatAmount(feePreview.stageATotal) }}</p>
                      <p class="text-[10px] text-slate-400 mt-0.5">Application processing</p>
                    </div>
                    <div class="rounded-lg px-3 py-2" style="background: rgba(255,255,255,0.7)">
                      <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">
                        {{ isLegacy ? 'Renewal · After approval' : 'Stage C · After approval' }}
                      </p>
                      <p class="text-sm font-bold text-slate-900">₦{{ formatAmount(isLegacy ? feePreview.renewalTotal : feePreview.stageCTotal) }}</p>
                      <p class="text-[10px] text-slate-400 mt-0.5">{{ isLegacy ? 'Legacy renewal fee' : 'Certificate issuance' }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </transition>
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

          <!-- Locality -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              Locality / Town / Estate <span class="text-red-500">*</span>
            </label>
            <input v-model="form.locality" type="text" required list="locality-suggestions"
                   placeholder="e.g. Awoyaya, Bogije, Lakowe, Oribanwa"
                   class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
            <datalist id="locality-suggestions">
              <option v-for="l in localitySuggestions" :key="l" :value="l" />
            </datalist>
            <p class="mt-1.5 text-xs text-slate-500">The community your street is in — used as a second check against duplicate names.</p>
          </div>

          <!-- Geolocation capture -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              Street Location <span class="text-red-500">*</span>
            </label>

            <!-- Map street picker -->
            <div class="rounded-xl overflow-hidden border border-slate-200">
              <div class="px-4 py-2.5 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                <p class="text-xs text-slate-600 font-medium">Click the street you want to name on the map</p>
                <button type="button" @click="locateMe"
                        class="text-xs font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-1">
                  <MapPinIcon class="w-3.5 h-3.5" /> Use my location
                </button>
              </div>
              <div ref="pickerMapEl" class="h-[320px] w-full" style="background:#eef2f7"></div>
              <div class="flex items-center gap-4 px-4 py-2 text-[11px] border-t border-slate-100 text-slate-600">
                <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full" style="background:#059669"></span>Named</span>
                <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full" style="background:#d97706"></span>Unnamed</span>
                <span v-if="pickerLoading" class="text-slate-400 ml-auto">Loading streets…</span>
              </div>
            </div>

            <!-- Recognition result -->
            <div v-if="geoState === 'success' && recognized" class="mt-3 rounded-xl p-3"
                 :style="recognized.is_named ? 'background:#fef3c7' : 'background:rgba(5,150,105,0.06)'">
              <p class="text-sm font-bold" :style="recognized.is_named ? 'color:#b45309' : 'color:#047857'">
                {{ recognized.is_named ? '⚠ This street is already named' : '✓ Unnamed street selected' }}
              </p>
              <p class="text-xs mt-0.5" :style="recognized.is_named ? 'color:#92400e' : 'color:#065f46'">
                <template v-if="recognized.is_named">This location is on <strong>{{ recognized.name }}</strong>, which already has a name. Applications are for streets that are not yet named — please pick an amber (unnamed) street.</template>
                <template v-else>You've selected an unnamed street<template v-if="recognized.locality"> in {{ recognized.locality }}</template>. Give it a name below.</template>
              </p>
              <p class="text-[11px] font-mono text-slate-500 mt-1">{{ geoCoords.lat }}, {{ geoCoords.lng }}</p>
            </div>
            <div v-else class="mt-2 text-xs text-slate-400">Tap a point on the map to select the street's location.</div>
          </div>

          <!-- Legacy registration checkbox (shown after geo is captured) -->
          <transition enter-active-class="transition ease-out duration-200"
                      enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0"
                      leave-active-class="transition ease-in duration-100"
                      leave-from-class="opacity-100 translate-y-0" leave-to-class="opacity-0 -translate-y-1">
            <div v-if="geoState === 'success'"
                 class="rounded-xl p-4"
                 style="background: rgba(251,191,36,0.06); border: 1px solid rgba(251,191,36,0.25)">
              <label class="flex items-start gap-3 cursor-pointer select-none">
                <div class="flex-shrink-0 mt-0.5">
                  <input type="checkbox" v-model="isLegacy"
                         class="w-4 h-4 rounded border-slate-300 text-amber-500 focus:ring-amber-400 focus:ring-offset-0 cursor-pointer" />
                </div>
                <div>
                  <p class="text-sm font-semibold text-slate-800">Have you registered this street and have a certificate before?</p>
                  <p class="text-xs text-slate-500 mt-0.5">
                    Check this if you previously obtained a manual street naming certificate and want to bring your registration into the digital system.
                  </p>
                </div>
              </label>

              <!-- Legacy certificate upload -->
              <transition enter-active-class="transition ease-out duration-200"
                          enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
                <div v-if="isLegacy" class="mt-4 pt-4" style="border-top: 1px solid rgba(251,191,36,0.2)">
                  <label class="block text-sm font-semibold text-slate-700 mb-1.5">
                    Existing Certificate <span class="text-red-500">*</span>
                  </label>
                  <div class="relative">
                    <input type="file" ref="legacyCertInput" accept=".pdf,.jpg,.jpeg,.png"
                           class="hidden" @change="onLegacyCertChange" />
                    <button type="button"
                            class="w-full flex items-center gap-3 rounded-xl border-2 border-dashed px-4 py-3 text-sm transition-colors"
                            :class="legacyCertFile ? 'border-amber-300 bg-amber-50' : 'border-slate-200 bg-slate-50 hover:border-slate-300'"
                            @click="legacyCertInput?.click()">
                      <svg class="w-4 h-4 flex-shrink-0" :class="legacyCertFile ? 'text-amber-500' : 'text-slate-400'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                      </svg>
                      <span :class="legacyCertFile ? 'text-amber-700 font-medium' : 'text-slate-500'">
                        {{ legacyCertFile ? legacyCertFile.name : 'Upload your existing certificate (PDF, JPG, PNG)' }}
                      </span>
                      <span v-if="legacyCertFile"
                            class="ml-auto text-xs text-amber-600 underline hover:text-amber-700"
                            @click.stop="legacyCertFile = null">Remove</span>
                    </button>
                  </div>
                  <p class="text-xs text-slate-400 mt-1.5">
                    After approval, you will pay the <strong>renewal fee</strong> instead of Stage C. Your certificate will be updated with a new expiry date.
                  </p>
                </div>
              </transition>
            </div>
          </transition>

          <!-- Actions -->
          <div class="flex items-center gap-3 pt-1">
            <button type="submit"
                    :disabled="submitting || !form.proposed_street_name || !form.street_type || !form.ward || !form.locality || geoState !== 'success' || (isLegacy && !legacyCertFile) || dup?.verdict === 'duplicate'"
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
import { ref, watch, onMounted, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useRouter, RouterLink } from 'vue-router'
import {
  ChevronRightIcon, ChevronDownIcon, InformationCircleIcon,
  MapPinIcon, CheckCircleIcon, ArrowPathIcon, ExclamationCircleIcon,
} from '@heroicons/vue/24/outline'
import { applicationApi, configApi, paymentApi } from '@/services/api'

interface StreetType { id: number; name: string }

const router = useRouter()
const form = ref({ proposed_street_name: '', street_type: '', ward: '', locality: '', location_description: '' })
const streetTypes = ref<StreetType[]>([])
const streetTypesLoading = ref(false)
const submitting = ref(false)
const errorMessage = ref('')

// --- Duplicate street-name check ---
interface DupMatch { code: string; name: string; locality: string; registration_status: string; distance_m: number | null }
interface DupNearby { code: string; name: string; distance_m: number; same_name: boolean }
const dup = ref<{ verdict: string; name_matches: DupMatch[]; locality_matches: DupMatch[]; nearby: DupNearby[] } | null>(null)
const dupChecking = ref(false)
let dupTimer: ReturnType<typeof setTimeout>

const localitySuggestions = [
  'Awoyaya', 'Bogije', 'Lakowe', 'Oribanwa', 'Eputu', 'Ogunfayo', 'Abijo', 'Ibeju',
  'Lekki Free Zone', 'Orimedu', 'Iwerekun', 'Magbon', 'Ilaje', 'Igando Oloja',
  'Ibeju-Lekki', 'Badore', 'Sangotedo', 'Ajah',
]

const isLegacy = ref(false)
const legacyCertFile = ref<File | null>(null)
const legacyCertInput = ref<HTMLInputElement | null>(null)

function onLegacyCertChange(e: Event) {
  const input = e.target as HTMLInputElement
  legacyCertFile.value = input.files?.[0] ?? null
}

const feePreview = ref({ loading: false, error: '', stageATotal: 0, stageCTotal: 0, renewalTotal: 0 })

function formatAmount(n: number) {
  return new Intl.NumberFormat('en-NG', { minimumFractionDigits: 2 }).format(n)
}

watch(() => form.value.street_type, async (streetTypeId) => {
  if (!streetTypeId) return
  feePreview.value = { loading: true, error: '', stageATotal: 0, stageCTotal: 0, renewalTotal: 0 }
  try {
    const [aRes, cRes, rRes] = await Promise.all([
      paymentApi.getBreakdown('stage_a'),
      paymentApi.getBreakdown('stage_c', streetTypeId),
      paymentApi.getBreakdown('renewal'),
    ])
    feePreview.value = {
      loading: false,
      error: '',
      stageATotal: parseFloat(aRes.data.total) || 0,
      stageCTotal: parseFloat(cRes.data.total) || 0,
      renewalTotal: parseFloat(rRes.data.total) || 0,
    }
  } catch {
    feePreview.value = { loading: false, error: 'Could not load fee estimate.', stageATotal: 0, stageCTotal: 0, renewalTotal: 0 }
  }
})

const geoState = ref<'idle' | 'success'>('idle')
const geoCoords = ref({ lat: '', lng: '', accuracy: '' })

// --- Map street picker ---
interface PickPoint { lat: number; lng: number; is_named: boolean; street_name: string; existing_street_name: string; locality: string }
const pickerMapEl = ref<HTMLElement | null>(null)
const pickerLoading = ref(true)
const recognized = ref<{ is_named: boolean; name: string; locality: string } | null>(null)
let pickerMap: L.Map | null = null
let clickMarker: L.CircleMarker | null = null
const pickPoints: PickPoint[] = []

function inBounds(lat: number, lng: number) {
  return lat >= 6.2 && lat <= 6.85 && lng >= 3.4 && lng <= 4.5
}

function nearest(lat: number, lng: number): { pt: PickPoint; dist: number } | null {
  let best: PickPoint | null = null
  let bestD = Infinity
  for (const p of pickPoints) {
    const dLat = (p.lat - lat) * 111000
    const dLng = (p.lng - lng) * 111000 * Math.cos(lat * Math.PI / 180)
    const d = Math.hypot(dLat, dLng)
    if (d < bestD) { bestD = d; best = p }
  }
  return best ? { pt: best, dist: bestD } : null
}

function selectAt(lat: number, lng: number) {
  geoCoords.value = { lat: lat.toFixed(6), lng: lng.toFixed(6), accuracy: '' }
  form.value.location_description = `${lat.toFixed(6)},${lng.toFixed(6)}`
  geoState.value = 'success'
  if (pickerMap) {
    if (clickMarker) clickMarker.remove()
    clickMarker = L.circleMarker([lat, lng], { radius: 8, color: '#0f172a', weight: 2, fillColor: '#38bdf8', fillOpacity: 0.9 }).addTo(pickerMap)
  }
  // Recognise the nearest surveyed street.
  const near = nearest(lat, lng)
  if (near && near.dist <= 120) {
    recognized.value = {
      is_named: near.pt.is_named,
      name: near.pt.street_name || near.pt.existing_street_name,
      locality: near.pt.locality,
    }
    // Auto-fill locality if empty.
    if (!form.value.locality && near.pt.locality) form.value.locality = near.pt.locality
  } else {
    recognized.value = { is_named: false, name: '', locality: '' }
  }
}

function locateMe() {
  if (!('geolocation' in navigator)) return
  navigator.geolocation.getCurrentPosition((pos) => {
    const lat = pos.coords.latitude, lng = pos.coords.longitude
    if (pickerMap) pickerMap.setView([lat, lng], 17)
    if (inBounds(lat, lng)) selectAt(lat, lng)
  }, () => {}, { enableHighAccuracy: true, timeout: 15000 })
}

async function initPicker() {
  await nextTick()
  if (!pickerMapEl.value) return
  pickerMap = L.map(pickerMapEl.value, { preferCanvas: true, scrollWheelZoom: true })
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap', maxZoom: 19 }).addTo(pickerMap)
  pickerMap.setView([6.465, 3.72], 13)
  pickerMap.on('click', (e: L.LeafletMouseEvent) => selectAt(e.latlng.lat, e.latlng.lng))
  try {
    const { data } = await configApi.getBuildingSurveys()
    const canvas = L.canvas({ padding: 0.5 })
    const bounds: L.LatLngTuple[] = []
    interface RawSurvey { latitude: number; longitude: number; is_named: boolean; street_name: string; existing_street_name: string; locality: string }
    for (const s of data as RawSurvey[]) {
      const lat = Number(s.latitude), lng = Number(s.longitude)
      if (!Number.isFinite(lat) || !inBounds(lat, lng)) continue
      pickPoints.push({ lat, lng, is_named: s.is_named, street_name: s.street_name, existing_street_name: s.existing_street_name, locality: s.locality })
      L.circleMarker([lat, lng], { renderer: canvas, radius: 3.5, color: s.is_named ? '#059669' : '#d97706', fillColor: s.is_named ? '#059669' : '#d97706', fillOpacity: 0.6, weight: 1 }).addTo(pickerMap)
      bounds.push([lat, lng])
    }
    if (bounds.length) pickerMap.fitBounds(L.latLngBounds(bounds).pad(0.05))
  } finally {
    pickerLoading.value = false
  }
}

const nextSteps = [
  'Stage A: your application is saved and the Council Treasurer (Finance Unit) receives your non-refundable processing fees.',
  'Stage B: after payment, the Chieftaincy section validates your royal father\'s recognition letter and the Street Naming Committee screens and interviews you.',
  'Stage C: the Local Government Chairman reviews the committee recommendation and gives the final decision.',
  'After approval, a Stage C certificate issuance fee is required before your certificate is printed.',
  'Stages D-F: signpost installed, street published to Google Maps, and a certificate of naming is issued and tracked for renewal.',
]

function runDuplicateCheck() {
  clearTimeout(dupTimer)
  const name = form.value.proposed_street_name.trim()
  if (name.length < 3) { dup.value = null; return }
  dupTimer = setTimeout(async () => {
    dupChecking.value = true
    try {
      const { data } = await applicationApi.checkDuplicate({
        name,
        locality: form.value.locality,
        latitude: geoCoords.value.lat || undefined,
        longitude: geoCoords.value.lng || undefined,
      })
      dup.value = data
    } catch {
      dup.value = null
    } finally {
      dupChecking.value = false
    }
  }, 500)
}

watch(() => [form.value.proposed_street_name, form.value.locality, geoCoords.value.lat], runDuplicateCheck)

async function handleSubmit() {
  errorMessage.value = ''
  submitting.value = true
  try {
    let payload: FormData | Record<string, unknown>
    if (isLegacy.value && legacyCertFile.value) {
      const fd = new FormData()
      fd.append('proposed_street_name', form.value.proposed_street_name)
      fd.append('street_type', form.value.street_type)
      fd.append('ward', form.value.ward)
      fd.append('locality', form.value.locality)
      fd.append('location_description', form.value.location_description)
      if (geoCoords.value.lat) fd.append('latitude', geoCoords.value.lat)
      if (geoCoords.value.lng) fd.append('longitude', geoCoords.value.lng)
      fd.append('is_legacy', 'true')
      fd.append('legacy_certificate', legacyCertFile.value)
      payload = fd
    } else {
      payload = {
        proposed_street_name: form.value.proposed_street_name,
        street_type: form.value.street_type,
        ward: form.value.ward,
        locality: form.value.locality,
        location_description: form.value.location_description,
        latitude: geoCoords.value.lat || null,
        longitude: geoCoords.value.lng || null,
      }
    }
    const { data } = await applicationApi.create(payload)
    router.push(`/applications/${data.id}`)
  } catch (err: unknown) {
    const e = err as { response?: { data?: Record<string, string[]> } }
    const d = e.response?.data
    errorMessage.value = d
      ? Object.entries(d).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' · ')
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
  initPicker()
})
</script>
