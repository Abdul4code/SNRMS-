<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <!-- Page header band -->
    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-2xl mx-auto px-4 sm:px-6 py-7">
        <nav class="flex items-center gap-2 text-xs text-slate-400 mb-4">
          <RouterLink to="/applications" class="hover:text-emerald-400 transition-colors">My Applications</RouterLink>
          <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
          <span class="text-slate-300">{{ isLegacy ? 'Validate Existing Registration' : 'New Application' }}</span>
        </nav>
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">{{ isLegacy ? 'Existing Registration' : 'New Request' }}</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">{{ isLegacy ? 'Validate Existing Registration' : 'Street Name Application' }}</h1>
        <p class="text-slate-400 text-sm mt-1">{{ isLegacy ? 'Register a street name that already exists so it is validated and recognised in the system.' : 'Submit a request to register a new street name in Ibeju-Lekki Local Government Area' }}</p>
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

          <!-- Locality -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              Locality / Town / Estate <span class="text-red-500">*</span>
            </label>
            <div class="relative">
              <select v-model="form.locality" required @change="onLocalityChange"
                      class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 pr-10 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all appearance-none">
                <option value="" disabled>Select your locality — the map will zoom to it</option>
                <option v-for="l in localityOptions" :key="l" :value="l">{{ l }}</option>
              </select>
              <ChevronDownIcon class="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
            <p class="mt-1.5 text-xs text-slate-500">Selecting your locality zooms the map to it and sets the ward automatically.</p>
          </div>

          <!-- Ward -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              Ward <span class="text-red-500">*</span>
            </label>
            <div class="relative">
              <select v-model="form.ward" required
                      class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 pr-10 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all appearance-none">
                <option value="" disabled>Select the ward</option>
                <option v-for="(label, code) in WARD_LABELS" :key="code" :value="code">{{ label }}</option>
              </select>
              <ChevronDownIcon class="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
            <p class="mt-1.5 text-xs" :class="wardAutoSet ? 'text-emerald-600' : 'text-slate-500'">
              {{ wardAutoSet ? '✓ Ward set automatically from your locality — change it if needed.' : 'Set automatically from your locality; you can also choose it here.' }}
            </p>
          </div>

          <!-- Street name: free text (new) OR select from registry (validate) -->
          <div v-if="!isLegacy">
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              Proposed Street Name <span class="text-red-500">*</span>
            </label>
            <input v-model="form.proposed_street_name" type="text" required
                   placeholder="e.g. Chief Bola Tinubu Boulevard"
                   class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
            <p class="mt-1.5 text-xs text-slate-500">Enter the proposed name of the street </p>

            <!-- Live duplicate check -->
            <div v-if="dupChecking" class="mt-2 text-xs text-slate-400">Checking the registry for this name…</div>
            <div v-else-if="dup && dup.rename_blocked" class="mt-2 rounded-xl border border-red-200 bg-red-50 p-3">
              <p class="text-sm font-bold text-red-700">This street cannot be renamed yet.</p>
              <p class="text-xs text-red-600 mt-0.5">
                "{{ dup.rename_blocked.name }}" is registered here until {{ formatExpiry(dup.rename_blocked.expires_at) }}.
                A street can only be renamed after its current registration expires (if it is not renewed).
              </p>
            </div>
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

          <div v-else>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              Select Street Name <span class="text-red-500">*</span>
            </label>
            <div class="relative">
              <select v-model="form.registry_street_id" required
                      class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all appearance-none">
                <option value="" disabled>Select the street from the registry</option>
                <option v-for="s in registryStreets" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
              <div class="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none">
                <ChevronDownIcon class="w-4 h-4 text-slate-400" />
              </div>
            </div>
            <p class="mt-1.5 text-xs text-slate-500">Choose the existing street you want to validate, then upload your documents and select its location below.</p>
            <div v-if="validateNote" class="mt-2 rounded-xl border p-3"
                 :class="validateNote.ok ? 'border-emerald-200 bg-emerald-50' : 'border-amber-200 bg-amber-50'">
              <p class="text-xs" :class="validateNote.ok ? 'text-emerald-700' : 'text-amber-700'">{{ validateNote.msg }}</p>
            </div>
          </div>
          <!-- Street type (new applications only) -->
          <div v-if="!isLegacy">
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
                  <div class="grid grid-cols-1 gap-3">
                    <div class="rounded-lg px-3 py-2" style="background: rgba(255,255,255,0.7)">
                      <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Application fee · Due now</p>
                      <p class="text-sm font-bold text-slate-900">₦{{ formatAmount(feePreview.stageATotal) }}</p>
                      <p class="text-[10px] text-slate-400 mt-0.5">Payable to begin processing</p>
                    </div>
                    <p class="text-[11px] text-slate-500">
                      The certificate fee (if your application is approved) will be communicated after the Local Government Chairman's approval.
                    </p>
                  </div>
                </div>
              </div>
            </transition>
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
              <div class="flex items-center gap-4 px-4 py-2 text-[11px] border-t border-slate-100 text-slate-500">
                <span>Zoom in and click the exact location of your street.</span>
                <span v-if="pickerLoading" class="text-slate-400 ml-auto">Loading…</span>
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
              <!-- #5: Show street's picture on demand so the applicant can confirm the location -->
              <div class="mt-2">
                <button type="button" v-if="!showPicture" @click="revealPicture"
                        class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white" style="background:#0f172a">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                  Show street's picture
                </button>
                <div v-else>
                  <!-- Google Street View (ground-level) when a key is configured -->
                  <img v-if="streetViewSrc" :src="streetViewSrc" alt="Street view at this location"
                       class="w-full rounded-lg border border-slate-200 mb-2" style="max-height:240px;object-fit:cover"
                       @error="onStreetViewError" />
                  <!-- Satellite / aerial view of the exact spot — always available, no key needed -->
                  <div ref="pictureMapEl" class="w-full rounded-lg border border-slate-200 overflow-hidden" style="height:240px"></div>
                  <p class="text-[10px] text-slate-400 mt-0.5">
                    {{ streetViewSrc ? 'Google Street View plus a satellite view of the exact spot.' : 'Satellite/aerial view of the exact spot you selected.' }}
                  </p>
                  <button type="button" @click="hidePicture" class="mt-1 text-[11px] text-slate-400 underline">Hide picture</button>
                </div>
              </div>
            </div>
            <div v-else class="mt-2 text-xs text-slate-400">Tap a point on the map to select the street's location.</div>
          </div>

          <!-- Validate mode: upload the existing document -->
          <div v-if="isLegacy" class="rounded-xl p-4" style="background: rgba(251,191,36,0.06); border: 1px solid rgba(251,191,36,0.25)">
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              Existing Document / Certificate <span class="text-red-500">*</span>
            </label>
            <div class="relative">
              <input type="file" ref="legacyCertInput" accept=".pdf,.jpg,.jpeg,.png" class="hidden" @change="onLegacyCertChange" />
              <button type="button"
                      class="w-full flex items-center gap-3 rounded-xl border-2 border-dashed px-4 py-3 text-sm transition-colors"
                      :class="legacyCertFile ? 'border-amber-300 bg-amber-50' : 'border-slate-200 bg-slate-50 hover:border-slate-300'"
                      @click="legacyCertInput?.click()">
                <svg class="w-4 h-4 flex-shrink-0" :class="legacyCertFile ? 'text-amber-500' : 'text-slate-400'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                </svg>
                <span :class="legacyCertFile ? 'text-amber-700 font-medium' : 'text-slate-500'">
                  {{ legacyCertFile ? legacyCertFile.name : 'Upload your existing certificate / document (PDF, JPG, PNG)' }}
                </span>
                <span v-if="legacyCertFile" class="ml-auto text-xs text-amber-600 underline hover:text-amber-700" @click.stop="legacyCertFile = null">Remove</span>
              </button>
            </div>
            <p class="text-xs text-slate-400 mt-1.5">Upload the document that proves your existing registration. The committee will validate it against the registry.</p>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-3 pt-1">
            <button type="submit"
                    :disabled="submitting || !form.locality || !form.ward || geoState !== 'success'
                      || (isLegacy ? (!form.registry_street_id || !legacyCertFile)
                                   : (!form.proposed_street_name || !form.street_type || dup?.verdict === 'duplicate' || !!dup?.rename_blocked))"
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
import { ref, watch, computed, onMounted, onUnmounted, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import {
  ChevronRightIcon, ChevronDownIcon, InformationCircleIcon,
  MapPinIcon, CheckCircleIcon, ArrowPathIcon, ExclamationCircleIcon,
} from '@heroicons/vue/24/outline'
import { applicationApi, configApi, paymentApi } from '@/services/api'

interface StreetType { id: number; name: string }

const router = useRouter()
const form = ref({ proposed_street_name: '', street_type: '', ward: '', locality: '', location_description: '', registry_street_id: '' })
const registryStreets = ref<{ id: string; name: string; latitude?: number | string | null; longitude?: number | string | null }[]>([])
const validateNote = ref<{ ok: boolean; msg: string } | null>(null)

function checkValidateMatch() {
  if (!isLegacy.value) { validateNote.value = null; return }
  const sid = form.value.registry_street_id
  const lat = parseFloat(geoCoords.value.lat), lng = parseFloat(geoCoords.value.lng)
  if (!sid || Number.isNaN(lat) || Number.isNaN(lng)) { validateNote.value = null; return }
  const selected = registryStreets.value.find(s => String(s.id) === String(sid))
  if (!selected) { validateNote.value = null; return }
  let nearest: PickPoint | null = null, best = Infinity
  for (const p of pickPoints) {
    if (!p.is_named) continue
    const d = Math.hypot((p.lat - lat) * 111000, (p.lng - lng) * 111000 * Math.cos(lat * Math.PI / 180))
    if (d < best) { best = d; nearest = p }
  }
  const norm = (x: string) => (x || '').trim().toLowerCase().replace(/\s+/g, ' ')
  if (!nearest || best > 60) {
    validateNote.value = { ok: false, msg: 'The street selected for validation does not match any initially named street. It will be flagged to the Street Naming Committee Chairman as probably part of the old record.' }
  } else if (norm(nearest.street_name || nearest.existing_street_name) !== norm(selected.name)) {
    validateNote.value = { ok: false, msg: 'The name you wish to validate does not match the name already in the database at this location.' }
  } else {
    validateNote.value = { ok: true, msg: '\u2713 This location matches the selected street in the registry.' }
  }
}
const streetTypes = ref<StreetType[]>([])
const streetTypesLoading = ref(false)
const submitting = ref(false)
const errorMessage = ref('')

// --- Duplicate street-name check ---
interface DupMatch { code: string; name: string; locality: string; registration_status: string; distance_m: number | null }
interface DupNearby { code: string; name: string; distance_m: number; same_name: boolean }
const dup = ref<{ verdict: string; name_matches: DupMatch[]; locality_matches: DupMatch[]; nearby: DupNearby[]; rename_blocked?: { name: string; reference: string; expires_at: string } | null } | null>(null)
const dupChecking = ref(false)
let dupTimer: ReturnType<typeof setTimeout>

const isLegacy = ref(false)
const route = useRoute()
// "Validate existing registration" enters this form in legacy mode.
if (route.query.mode === 'legacy') isLegacy.value = true
const legacyCertFile = ref<File | null>(null)
const legacyCertInput = ref<HTMLInputElement | null>(null)

function onLegacyCertChange(e: Event) {
  const input = e.target as HTMLInputElement
  legacyCertFile.value = input.files?.[0] ?? null
}

const feePreview = ref({ loading: false, error: '', stageATotal: 0, stageCTotal: 0, renewalTotal: 0 })

function formatExpiry(d?: string) {
  return d ? new Date(d).toLocaleDateString('en-NG', { year: 'numeric', month: 'long', day: 'numeric' }) : ''
}
function formatAmount(n: number) {
  return new Intl.NumberFormat('en-NG', { minimumFractionDigits: 2 }).format(n)
}

watch(() => form.value.street_type, async (streetTypeId) => {
  if (!streetTypeId) return
  feePreview.value = { loading: true, error: '', stageATotal: 0, stageCTotal: 0, renewalTotal: 0 }
  try {
    // Only the application (Stage A) fee is shown to the applicant. The Stage C /
    // certificate amount is withheld until the Chairman approves the application.
    const aRes = await paymentApi.getBreakdown('stage_a')
    feePreview.value = {
      loading: false, error: '',
      stageATotal: parseFloat(aRes.data.total) || 0,
      stageCTotal: 0, renewalTotal: 0,
    }
  } catch {
    feePreview.value = { loading: false, error: 'Could not load fee estimate.', stageATotal: 0, stageCTotal: 0, renewalTotal: 0 }
  }
})

const geoState = ref<'idle' | 'success'>('idle')
const geoCoords = ref({ lat: '', lng: '', accuracy: '' })
const streetViewSrc = ref('')
const googleEnabled = ref(false)
const showPicture = ref(false)
const pictureMapEl = ref<HTMLElement | null>(null)
let pictureMap: L.Map | null = null
function revealPicture() {
  const lat = parseFloat(geoCoords.value.lat), lng = parseFloat(geoCoords.value.lng)
  if (Number.isNaN(lat) || Number.isNaN(lng)) return
  if (googleEnabled.value) streetViewSrc.value = configApi.streetViewUrl(lat, lng)
  showPicture.value = true
  nextTick(() => {
    if (pictureMap) { pictureMap.remove(); pictureMap = null }
    if (!pictureMapEl.value) return
    pictureMap = L.map(pictureMapEl.value, { zoomControl: true, attributionControl: false, dragging: true, scrollWheelZoom: false })
    // Esri World Imagery — free satellite/aerial tiles, no API key required.
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19 }).addTo(pictureMap)
    pictureMap.setView([lat, lng], 18)
    L.circleMarker([lat, lng], { radius: 8, color: '#f59e0b', weight: 3, fillColor: '#f59e0b', fillOpacity: 0.5 }).addTo(pictureMap)
    setTimeout(() => pictureMap?.invalidateSize(), 120)
  })
}
function hidePicture() {
  if (pictureMap) { pictureMap.remove(); pictureMap = null }
  showPicture.value = false
}
function onStreetViewError() { streetViewSrc.value = '' }

// --- Auto-pick ward from locality ---
const WARD_LABELS: Record<string, string> = {
  ward_a: 'Ward A (Ibeju 1)', ward_b: 'Ward B (Ibeju 2)', ward_c1: 'Ward C1 (Orimedu 1)',
  ward_c2: 'Ward C2 (Orimedu 2)', ward_d: 'Ward D (Orimedu 3)', ward_e: 'Ward E (Iwerekun 1)',
  ward_f: 'Ward F (Iwerekun 2)',
}
const localityWards = ref<Record<string, string>>({})
const communities = ref<string[]>([])

// Locality options are built from the SURVEY points themselves, so every option is
// guaranteed to have points on the map to zoom to and a ward to auto-fill.
const localityOptions = ref<string[]>([])
const wardAutoSet = ref(false)
const localityMeta = ref<Record<string, { ward: string; pts: [number, number][] }>>({})

function titleCase(s: string) {
  return s.toLowerCase().replace(/\b\w/g, c => c.toUpperCase())
}
// Map the messy survey ward strings (e.g. "B", "Ward E", "Ibeju 1", "N/A") to the
// canonical ward codes. Junk values return '' and are ignored in the vote.
function normalizeWard(raw: string): string {
  const s = (raw || '').trim().toLowerCase().replace(/\s+/g, ' ')
  if (!s) return ''
  const code = s.replace(/^ward\s*/, '').replace(/\s+/g, '')
  const direct: Record<string, string> = {
    a: 'ward_a', b: 'ward_b', c1: 'ward_c1', c2: 'ward_c2', d: 'ward_d', e: 'ward_e', f: 'ward_f',
  }
  if (direct[code]) return direct[code]
  if (/ibeju\s*(1|i)\b/.test(s)) return 'ward_a'
  if (/ibeju\s*(2|ii)\b/.test(s)) return 'ward_b'
  if (/orimedu\s*1/.test(s)) return 'ward_c1'
  if (/orimedu\s*2/.test(s)) return 'ward_c2'
  if (/orimedu\s*3/.test(s)) return 'ward_d'
  if (/iwerekun\s*1/.test(s)) return 'ward_e'
  if (/iwerekun\s*2/.test(s)) return 'ward_f'
  return ''
}

function rebuildLocalityIndex() {
  const groups: Record<string, { display: string; wards: Record<string, number>; pts: [number, number][] }> = {}
  for (const p of pickPoints) {
    const raw = (p.locality || '').trim()
    if (!raw) continue
    const key = raw.toUpperCase().replace(/\s+/g, ' ')
    if (!groups[key]) groups[key] = { display: titleCase(raw), wards: {}, pts: [] }
    groups[key].pts.push([p.lat, p.lng])
    const w = normalizeWard(p.ward || '')  // only count VALID ward codes
    if (w) groups[key].wards[w] = (groups[key].wards[w] || 0) + 1
  }
  const meta: Record<string, { ward: string; pts: [number, number][] }> = {}
  const opts: string[] = []
  for (const key of Object.keys(groups)) {
    const g = groups[key]
    if (!g || g.pts.length < 2) continue  // skip stray single points / typos
    const ward = Object.keys(g.wards).sort((a, b) => (g.wards[b] ?? 0) - (g.wards[a] ?? 0))[0] || ''
    meta[g.display] = { ward, pts: g.pts }
    opts.push(g.display)
  }
  opts.sort((a, b) => a.localeCompare(b))
  localityOptions.value = opts
  localityMeta.value = meta
}

function onLocalityChange() {
  const meta = localityMeta.value[form.value.locality]
  // Prefer the ward derived from the locality's points; if none could be derived,
  // keep whatever the applicant already chose so they can set it manually.
  if (meta && meta.ward) { form.value.ward = meta.ward; wardAutoSet.value = true }
  else { wardAutoSet.value = false }
  zoomToLocality()
}

function zoomToLocality() {
  const sel = form.value.locality
  if (!pickerMap || !sel) return
  if (!pickPoints.length) { pendingZoomLocality = sel; return }
  const meta = localityMeta.value[sel]
  const pts = meta?.pts || []
  if (pts.length >= 1) {
    // Leaflet mis-measures if the container was resized/hidden — fix before fitting.
    pickerMap.invalidateSize()
    pickerMap.fitBounds(L.latLngBounds(pts).pad(0.25), { maxZoom: 16 })
  }
}

// --- Map street picker ---
interface PickPoint { lat: number; lng: number; is_named: boolean; street_name: string; existing_street_name: string; locality: string; ward: string; photo_url: string }
const pickerMapEl = ref<HTMLElement | null>(null)
const pickerLoading = ref(true)
const recognized = ref<{ is_named: boolean; name: string; locality: string; photo_url: string } | null>(null)
let pickerMap: L.Map | null = null
let streetLabelLayer: L.LayerGroup | null = null
let pendingZoomLocality = ""
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
  if (pictureMap) { pictureMap.remove(); pictureMap = null }
  showPicture.value = false
  streetViewSrc.value = ''
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
      photo_url: near.pt.photo_url || '',
    }
    // Auto-fill locality if empty.
    if (!form.value.locality && near.pt.locality) form.value.locality = near.pt.locality
  } else {
    recognized.value = { is_named: false, name: '', locality: '', photo_url: '' }
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
  streetLabelLayer = L.layerGroup().addTo(pickerMap)
  pickerMap.on('zoomend moveend', refreshStreetLabels)
  try {
    const { data } = await configApi.getBuildingSurveys()
    const bounds: L.LatLngTuple[] = []
    interface RawSurvey { latitude: number; longitude: number; is_named: boolean; street_name: string; existing_street_name: string; locality: string; ward: string; photo_url: string }
    for (const s of data as RawSurvey[]) {
      const lat = Number(s.latitude), lng = Number(s.longitude)
      if (!Number.isFinite(lat) || !inBounds(lat, lng)) continue
      // Points are kept in memory for snapping/recognition, but NOT drawn on the
      // map — the applicant shouldn't be confused by the survey dots.
      pickPoints.push({ lat, lng, is_named: s.is_named, street_name: s.street_name, existing_street_name: s.existing_street_name, locality: s.locality, ward: (s as any).ward || '', photo_url: s.photo_url })
      bounds.push([lat, lng])
    }
    if (bounds.length) pickerMap.fitBounds(L.latLngBounds(bounds).pad(0.05))
  } finally {
    pickerLoading.value = false
    rebuildLocalityIndex()
    refreshStreetLabels()
    // If a locality was chosen before points finished loading, zoom now.
    if (pendingZoomLocality || form.value.locality) { pendingZoomLocality = ''; zoomToLocality() }
  }
}

// Overlay existing street names (from the survey records) as labels, so the
// applicant can see the names of nearby streets on the auto-zoomed map.
function refreshStreetLabels() {
  if (!pickerMap || !streetLabelLayer) return
  streetLabelLayer.clearLayers()
  if (pickerMap.getZoom() < 15) return  // only when zoomed in enough to be readable
  const b = pickerMap.getBounds()
  const groups: Record<string, { lat: number; lng: number; n: number }> = {}
  for (const p of pickPoints) {
    const name = (p.existing_street_name || p.street_name || '').trim()
    if (!name || !p.is_named) continue
    if (!b.contains([p.lat, p.lng] as L.LatLngTuple)) continue
    const g = groups[name] || (groups[name] = { lat: 0, lng: 0, n: 0 })
    g.lat += p.lat; g.lng += p.lng; g.n += 1
  }
  const names = Object.keys(groups)
  for (const name of names.slice(0, 60)) {  // cap to keep the map readable
    const g = groups[name]!
    L.marker([g.lat / g.n, g.lng / g.n], {
      interactive: false,
      icon: L.divIcon({
        className: 'street-name-label',
        html: `<span style="background:rgba(255,255,255,0.82);border:1px solid #cbd5e1;border-radius:4px;padding:1px 5px;font-size:10px;font-weight:600;color:#334155;white-space:nowrap;box-shadow:0 1px 2px rgba(0,0,0,0.1)">${name.replace(/</g, '')}</span>`,
        iconSize: [0, 0],
      }),
    }).addTo(streetLabelLayer)
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
watch(() => [form.value.registry_street_id, geoCoords.value.lat, geoCoords.value.lng], checkValidateMatch)

async function handleSubmit() {
  errorMessage.value = ''
  submitting.value = true
  try {
    let payload: FormData | Record<string, unknown>
    if (isLegacy.value && legacyCertFile.value) {
      const selected = registryStreets.value.find(s => String(s.id) === String(form.value.registry_street_id))
      const fd = new FormData()
      // In validate mode the name comes from the selected registry street.
      fd.append('proposed_street_name', selected?.name || '')
      fd.append('registry_street_id', String(form.value.registry_street_id))
      fd.append('street_type', form.value.street_type || '')
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
  configApi.getLocalityWards().then(r => { localityWards.value = r.data.community_to_ward || {}; communities.value = Object.keys(r.data.community_to_ward || {}).sort() }).catch(() => {})
  configApi.publicSettings().then(r => { googleEnabled.value = !!r.data.google_maps_enabled }).catch(() => {})
  if (isLegacy.value) {
    configApi.getStreets().then(r => {
      registryStreets.value = (r.data as typeof registryStreets.value).slice().sort((a, b) => a.name.localeCompare(b.name))
    }).catch(() => {})
  }
  initPicker()
})

// The new-application and validate flows share this route, so navigating between
// them (or re-entering) reuses this component instance. Re-initialise on every
// entry so the map always rebuilds and re-zooms to the selected locality.
watch(() => route.fullPath, async () => {
  if (route.name !== 'application-new' && !route.path.startsWith('/applications/new')) return
  isLegacy.value = route.query.mode === 'legacy'
  // reset the form for a clean entry
  form.value = { proposed_street_name: '', street_type: '', ward: '', locality: '', location_description: '', registry_street_id: '' }
  geoCoords.value = { lat: '', lng: '', accuracy: '' }
  recognized.value = null
  validateNote.value = null
  streetViewSrc.value = ''
  if (pictureMap) { pictureMap.remove(); pictureMap = null }
  showPicture.value = false
  legacyCertFile.value = null
  pickPoints.length = 0
  pendingZoomLocality = ''
  if (pickerMap) { pickerMap.remove(); pickerMap = null }
  pickerLoading.value = true
  if (isLegacy.value && !registryStreets.value.length) {
    configApi.getStreets().then(r => {
      registryStreets.value = (r.data as typeof registryStreets.value).slice().sort((a, b) => a.name.localeCompare(b.name))
    }).catch(() => {})
  }
  await initPicker()
})

onUnmounted(() => { if (pickerMap) { pickerMap.remove(); pickerMap = null } if (pictureMap) { pictureMap.remove(); pictureMap = null } })
</script>
