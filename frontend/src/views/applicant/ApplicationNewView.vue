<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <!-- Page header band -->
    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-2xl mx-auto px-4 sm:px-6 py-7">
        <nav class="flex items-center gap-2 text-xs text-slate-400 mb-4">
          <RouterLink to="/applications" class="hover:text-emerald-400 transition-colors">My Applications</RouterLink>
          <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
          <span class="text-slate-300">{{ pageTitle }}</span>
        </nav>
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">{{ pageEyebrow }}</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">{{ pageTitle }}</h1>
        <p class="text-slate-400 text-sm mt-1">{{ pageBlurb }}</p>
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

          <!-- Ward — derived from the locality, never asked for. A locality sits in
               exactly one ward, so asking invites the two answers to disagree. -->
          <div v-if="form.locality">
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">Ward</label>
            <div class="rounded-xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm flex items-center gap-2">
              <span v-if="form.ward" class="text-slate-800 font-medium">{{ WARD_LABELS[form.ward] }}</span>
              <span v-else class="text-slate-500">Will be set from the location you pick on the map.</span>
            </div>
            <p class="mt-1.5 text-xs text-slate-500">
              Determined by your locality — the council assigns wards, so there is nothing to choose.
            </p>
          </div>

          <!-- Street name: free text (new) OR select from registry (validate) -->
          <div v-if="!usesRegistry">
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
              <select v-model="form.registry_street_id" required @change="onRegistryStreetChange"
                      class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all appearance-none">
                <option value="" disabled>
                  {{ form.locality ? 'Select the street from the registry' : 'Choose your locality first' }}
                </option>
                <optgroup v-if="streetsInLocality.length" :label="`Streets in ${form.locality}`">
                  <option v-for="s in streetsInLocality" :key="s.id" :value="s.id">{{ s.name }}</option>
                </optgroup>
                <optgroup v-if="streetsWithoutLocality.length" label="Locality not recorded — check this is your street">
                  <option v-for="s in streetsWithoutLocality" :key="s.id" :value="s.id">{{ s.name }}</option>
                </optgroup>
              </select>
              <div class="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none">
                <ChevronDownIcon class="w-4 h-4 text-slate-400" />
              </div>
            </div>
            <p class="mt-1.5 text-xs text-slate-500">
              <template v-if="form.locality">Only streets in {{ form.locality }} are listed. The one you choose is highlighted on the map automatically.</template>
              <template v-else>Choose your locality above and this list will narrow to the streets in it.</template>
            </p>
            <p v-if="form.locality && !streetsInLocality.length && streetsWithoutLocality.length"
               class="mt-1 text-xs text-amber-700">
              No street in {{ form.locality }} has been recorded yet. The streets below are from the old
              register, which does not record a locality — pick yours only if you are sure it is the one.
            </p>
            <div v-if="validateNote" class="mt-2 rounded-xl border p-3"
                 :class="validateNote.ok ? 'border-emerald-200 bg-emerald-50' : 'border-amber-200 bg-amber-50'">
              <p class="text-xs" :class="validateNote.ok ? 'text-emerald-700' : 'text-amber-700'">{{ validateNote.msg }}</p>
            </div>
          </div>
          <!-- Street type (new applications only) -->
          <div v-if="!usesRegistry">
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
                <p class="text-xs font-medium" :class="streetLocked || pickedRoad ? 'text-emerald-700' : 'text-slate-600'">
                  <template v-if="streetLocked">🔒 Selected street — set from the registry</template>
                  <template v-else-if="pickedRoad">✓ Street selected — tap another to change it</template>
                  <template v-else-if="usesRegistry">Tap the street you selected above</template>
                  <template v-else>Tap the street you want to name</template>
                </p>
                <button type="button" v-if="!streetLocked" @click="locateMe"
                        class="text-xs font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-1">
                  <MapPinIcon class="w-3.5 h-3.5" /> Use my location
                </button>
              </div>
              <div ref="pickerMapEl" class="h-[320px] w-full"
                   :class="streetLocked ? 'cursor-not-allowed' : ''" style="background:#eef2f7"></div>
              <div class="flex items-center gap-4 px-4 py-2 text-[11px] border-t border-slate-100 text-slate-500">
                <span v-if="streetLocked">The location of this street is fixed by the registry and cannot be changed.</span>
                <span v-else-if="pickedRoad">
                  <strong class="text-emerald-700">{{ pickedRoad.name || 'This street' }}</strong>
                  is highlighted end to end. Tap a different road to change it, or tap
                  anywhere else to drop a pin instead.
                </span>
                <span v-else>Zoom in and tap the road your street runs along — it will light up.
                  If your street is not drawn on the map, tap its location to drop a pin.</span>
                <span v-if="pickerLoading || roadsLoading" class="text-slate-400 ml-auto">Loading…</span>
              </div>
            </div>

            <!-- Recognition result -->
            <div v-if="geoState === 'success' && recognized" class="mt-3 rounded-xl p-3"
                 :style="(recognized.is_named && !streetLocked) ? 'background:#fef3c7' : 'background:rgba(5,150,105,0.06)'">
              <p class="text-sm font-bold" :style="(recognized.is_named && !streetLocked) ? 'color:#b45309' : 'color:#047857'">
                <template v-if="streetLocked">✓ Validating {{ selectedRegistryStreet?.name }}</template>
                <template v-else>{{ recognized.is_named ? '⚠ This street is already named' : '✓ Unnamed street selected' }}</template>
              </p>
              <p class="text-xs mt-0.5" :style="(recognized.is_named && !streetLocked) ? 'color:#92400e' : 'color:#065f46'">
                <template v-if="streetLocked">This is the street's own location, taken from the registry. Use the picture below to confirm it.</template>
                <template v-else-if="recognized.is_named">This location is on <strong>{{ recognized.name }}</strong>, which already has a name. Applications are for streets that are not yet named — please pick an amber (unnamed) street.</template>
                <template v-else>You've selected an unnamed street<template v-if="recognized.locality"> in {{ recognized.locality }}</template>. Give it a name below.</template>
              </p>
              <!-- Item 1: street already being pursued by another applicant -->
              <div v-if="streetTaken" class="mt-2 rounded-lg border border-red-200 bg-red-50 p-2.5">
                <p class="text-xs font-bold text-red-700">⚠ This street is taken</p>
                <p class="text-[11px] text-red-600 mt-0.5">{{ streetTaken }}</p>
              </div>
              <p class="text-[11px] font-mono text-slate-500 mt-1">{{ geoCoords.lat }}, {{ geoCoords.lng }}</p>
              <!-- #5: Show street's picture on demand so the applicant can confirm the location -->
              <div class="mt-2">
                <StreetPicture :lat="geoCoords.lat" :lng="geoCoords.lng" :google-enabled="googleEnabled"
                               :height="240" :title="selectedRegistryStreet?.name || form.proposed_street_name" />
              </div>
            </div>
            <div v-else-if="!streetLocked" class="mt-2 text-xs text-slate-400">Tap a point on the map to select the street's location.</div>
          </div>

          <!-- Validate mode: upload the existing document -->
          <div v-if="usesRegistry" class="rounded-xl p-4" style="background: rgba(251,191,36,0.06); border: 1px solid rgba(251,191,36,0.25)">
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              {{ isRenewal ? 'Certificate being renewed' : 'Existing Document / Certificate' }}
              <span class="text-red-500">*</span>
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
            <p class="text-xs text-slate-400 mt-1.5">
              {{ isRenewal
                ? 'Upload the certificate that has expired. The committee checks it against the registry before the Chairman approves the renewal.'
                : 'Upload the document that proves your existing registration. The committee will validate it against the registry.' }}
            </p>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-3 pt-1">
            <button type="submit"
                    :disabled="submitting || !form.locality || geoState !== 'success'
                      || (usesRegistry ? (!form.registry_street_id || !legacyCertFile || wrongStreet)
                                   : (!form.proposed_street_name || !form.street_type || dup?.verdict === 'duplicate' || !!dup?.rename_blocked || !!streetTaken))"
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
import StreetPicture from '@/components/StreetPicture.vue'
import {
  ChevronRightIcon, ChevronDownIcon, InformationCircleIcon,
  MapPinIcon, CheckCircleIcon, ArrowPathIcon, ExclamationCircleIcon,
} from '@heroicons/vue/24/outline'
import { applicationApi, configApi, paymentApi } from '@/services/api'

interface StreetType { id: number; name: string }

const router = useRouter()
const form = ref({ proposed_street_name: '', street_type: '', ward: '', locality: '', location_description: '', registry_street_id: '' })
interface RegistryStreet {
  id: string
  name: string
  locality?: string
  latitude?: number | string | null
  longitude?: number | string | null
  geometry?: string | null
}
const registryStreets = ref<RegistryStreet[]>([])

// Validation is for a street the applicant already has papers for, so the list is
// narrowed to their locality — picking a same-named street in another town is the
// mistake this prevents. Streets carried over from the old register have no
// locality recorded at all; those are offered separately rather than hidden,
// because they are the ones most often validated.
const sameLocality = (a?: string | null, b?: string | null) => {
  const norm = (x?: string | null) => (x || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
  const x = norm(a), y = norm(b)
  return !!x && !!y && (x === y || x.startsWith(y + ' ') || y.startsWith(x + ' '))
}
const streetsInLocality = computed(() =>
  form.value.locality
    ? registryStreets.value.filter(s => sameLocality(s.locality, form.value.locality))
    : [])
const streetsWithoutLocality = computed(() =>
  form.value.locality
    ? registryStreets.value.filter(s => !(s.locality || '').trim())
    : [])
const selectableStreets = computed(() => [...streetsInLocality.value, ...streetsWithoutLocality.value])
const validateNote = ref<{ ok: boolean; msg: string } | null>(null)
// Validate mode only. When the street chosen in the dropdown has a known location
// the map is LOCKED to it: the location is auto-picked, the street is highlighted,
// and clicks are ignored so nobody can validate one name against another street.
const streetLocked = ref(false)
const selectedRegistryStreet = computed(() =>
  registryStreets.value.find(s => String(s.id) === String(form.value.registry_street_id)) || null)
// Set when a hand-picked location sits on a DIFFERENT named street — blocks submit.
const wrongStreet = ref(false)
let streetPendingId = ''            // chosen before the map finished loading

const normName = (x: string) => (x || '').trim().toLowerCase().replace(/\s+/g, ' ')

/** Width of a point set in metres, along its widest axis. */
function spanMetres(pts: [number, number][]): number {
  const lats = pts.map(p => p[0]), lngs = pts.map(p => p[1])
  const dLat = (Math.max(...lats) - Math.min(...lats)) * 111000
  const dLng = (Math.max(...lngs) - Math.min(...lngs)) * 111000 * Math.cos((lats[0] as number) * Math.PI / 180)
  return Math.max(dLat, dLng)
}

/** Survey points that belong to the named street, matched by name. */
function pointsForStreet(name: string): [number, number][] {
  const want = normName(name)
  if (!want) return []
  return pickPoints
    .filter(p => p.is_named && normName(p.existing_street_name || p.street_name) === want)
    .map(p => [p.lat, p.lng] as [number, number])
}

function checkValidateMatch() {
  if (!usesRegistry.value) { validateNote.value = null; wrongStreet.value = false; return }
  if (streetLocked.value) return          // the location came from the registry itself
  const sid = form.value.registry_street_id
  const lat = parseFloat(geoCoords.value.lat), lng = parseFloat(geoCoords.value.lng)
  if (!sid || Number.isNaN(lat) || Number.isNaN(lng)) { wrongStreet.value = false; return }
  const selected = registryStreets.value.find(s => String(s.id) === String(sid))
  if (!selected) { validateNote.value = null; wrongStreet.value = false; return }
  let nearest: PickPoint | null = null, best = Infinity
  for (const p of pickPoints) {
    if (!p.is_named) continue
    const d = Math.hypot((p.lat - lat) * 111000, (p.lng - lng) * 111000 * Math.cos(lat * Math.PI / 180))
    if (d < best) { best = d; nearest = p }
  }
  if (!nearest || best > 60) {
    // Nothing named nearby: this is an old-register street the survey never saw.
    // Allowed, but flagged — it is the only way to give these streets a location.
    wrongStreet.value = false
    validateNote.value = { ok: false, msg: 'The street selected for validation does not match any initially named street. It will be flagged to the Street Naming Committee Chairman as probably part of the old record.' }
  } else if (normName(nearest.street_name || nearest.existing_street_name) !== normName(selected.name)) {
    // Pointing at someone else's street — refuse it outright.
    wrongStreet.value = true
    validateNote.value = { ok: false, msg: `That location is on ${nearest.street_name || nearest.existing_street_name}, not ${selected.name}. You can only validate the street you selected — choose its own location, or pick the right street from the list.` }
  } else {
    wrongStreet.value = false
    validateNote.value = { ok: true, msg: '\u2713 This location matches the selected street in the registry.' }
  }
}

/** Dropdown changed in validate mode: auto-pick and highlight that street. */
function onRegistryStreetChange() {
  wrongStreet.value = false
  streetLocked.value = false
  clearStreetHighlight()
  clearPickedLocation()          // never carry the previous street's location over
  const selected = registryStreets.value.find(s => String(s.id) === String(form.value.registry_street_id))
  if (!selected) { validateNote.value = null; return }
  if (pickerLoading.value) { streetPendingId = String(selected.id); return }

  // The street's own centre-line if the registry has one — that is the street,
  // where the surveyed buildings are only near it.
  const centreLine = lineOf(selected.geometry)
  if (centreLine) {
    const mid = centreLine[Math.floor(centreLine.length / 2)] as [number, number]
    streetLocked.value = true
    selectAt(mid[0], mid[1])
    drawStreetHighlight(centreLine, selected.name, true)
    validateNote.value = { ok: true, msg: `\u2713 ${selected.name} is selected and drawn on the map. Its location comes from the registry, so it cannot be changed.` }
    return
  }

  // No line on record: fall back to the surveyed extent, then to the centroid.
  // coreCluster drops bad GPS fixes — on a locked map a centroid dragged
  // kilometres off by one stray point is not something the applicant can correct.
  let pts = coreCluster(pointsForStreet(selected.name))
  if (!pts.length) {
    const la = Number(selected.latitude), ln = Number(selected.longitude)
    if (Number.isFinite(la) && Number.isFinite(ln) && inBounds(la, ln)) pts = [[la, ln]]
  }
  // A handful of points scattered over kilometres is a conflict in the survey, not
  // a long road: the centroid would sit where the street isn't, and a locked map
  // gives the applicant no way to correct it. Long roads with many points are fine.
  if (pts.length >= 1 && pts.length < 5 && spanMetres(pts) > 1500) pts = []

  if (!pts.length) {
    // Digitised old-register streets carry no coordinates at all. Nothing to lock
    // onto, so the applicant marks it — checkValidateMatch still refuses a spot
    // that belongs to another named street.
    validateNote.value = { ok: false, msg: `${selected.name} has no reliable location on record yet. Click its location on the map — you cannot select a spot that belongs to a different named street.` }
    return
  }

  const cLat = pts.reduce((a, p) => a + p[0], 0) / pts.length
  const cLng = pts.reduce((a, p) => a + p[1], 0) / pts.length
  streetLocked.value = true
  selectAt(cLat, cLng)                       // fills geoCoords / geoState / description
  drawStreetHighlight(pts, selected.name)
  validateNote.value = { ok: true, msg: `\u2713 ${selected.name} is selected and highlighted on the map. Its location comes from the registry, so it cannot be changed.` }
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
// Renewing a registration that has run out. It walks the same road as a
// validation — pick your street, upload the certificate, the committee looks at
// it — so the two share this screen; only the wording and the fee differ.
const isRenewal = ref(false)
/** Both kinds pick an existing street from the registry and upload a certificate. */
const usesRegistry = computed(() => isLegacy.value || isRenewal.value)

const pageTitle = computed(() =>
  isRenewal.value ? 'Renew Expired Registration'
  : isLegacy.value ? 'Validate Existing Registration'
  : 'Street Name Application')
const pageEyebrow = computed(() =>
  isRenewal.value ? 'Renewal' : isLegacy.value ? 'Existing Registration' : 'New Request')
const pageBlurb = computed(() =>
  isRenewal.value
    ? 'Renew a street name registration that has expired. Choose the street, upload the certificate that ran out, and pay the renewal fee.'
  : isLegacy.value
    ? 'Register a street name that already exists so it is validated and recognised in the system.'
    : 'Submit a request to register a new street name in Ibeju-Lekki Local Government Area')
const route = useRoute()
// "Validate existing registration" enters this form in legacy mode.
if (route.query.mode === 'legacy') isLegacy.value = true
if (route.query.mode === 'renewal') isRenewal.value = true
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
// Passed to <StreetPicture>; only the Street View still needs a server key.
const googleEnabled = ref(false)

// --- Auto-pick ward from locality ---
const WARD_LABELS: Record<string, string> = {
  ward_a: 'Ward A (Ibeju 1)', ward_b: 'Ward B (Ibeju 2)', ward_c1: 'Ward C1 (Orimedu 1)',
  ward_c2: 'Ward C2 (Orimedu 2)', ward_d: 'Ward D (Orimedu 3)', ward_e: 'Ward E (Iwerekun 1)',
  ward_f: 'Ward F (Iwerekun 2)',
}
const localityWards = ref<Record<string, string>>({})
// Every community the council names — the whole list, not only the ones the
// field survey reached. `latitude`/`longitude` is the middle of the place where
// anyone has mapped it; null where nobody has.
interface Community {
  name: string; ward: string
  latitude: number | null; longitude: number | null
  buildings: number; position_from: string
}
const communities = ref<Community[]>([])

// Locality options are built from the SURVEY points themselves, so every option is
// guaranteed to have points on the map to zoom to and a ward to auto-fill.
const localityOptions = ref<string[]>([])
const wardAutoSet = ref(false)
const localityMeta = ref<Record<string, { ward: string; pts: [number, number][] }>>({})

function titleCase(s: string) {
  return s.toLowerCase().replace(/\b\w/g, c => c.toUpperCase())
}
// Enumerator misspellings of real localities. Keyed by the raw survey value in
// UPPERCASE; the points are folded into the correct locality so the typo never
// shows up as its own option. "Abidjan" is a mis-typed "Abijo".
const LOCALITY_CORRECTIONS: Record<string, string> = {
  ABIDJAN: 'Abijo',
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
    let raw = (p.locality || '').trim()
    if (!raw) continue
    raw = LOCALITY_CORRECTIONS[raw.toUpperCase().replace(/\s+/g, ' ')] || raw
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
  // The survey only reached a couple of dozen communities, but an applicant may
  // live in any of them, so the picker is the council's whole list. The surveyed
  // points still drive the zoom wherever they exist.
  const fromCouncil = communities.value.map(c => c.name)
  localityOptions.value = fromCouncil.length ? fromCouncil : opts
  localityMeta.value = meta
}

/** The ward for a locality. The council's own community list is the authority;
 *  the surveyed buildings cover estates and layouts that are not on it. The
 *  server derives this again on submit, so a stale value here cannot be stored. */
function wardForLocality(locality: string): string {
  if (!locality) return ''
  const norm = (x: string) => x.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
  const want = norm(locality)
  const official = localityWards.value
  for (const name of Object.keys(official)) {
    if (norm(name) === want) return official[name] as string
  }
  // "Abijo GRA", "Awoyaya Town" — an official community with a qualifier attached.
  const words = new Set(want.split(' '))
  let best = '', bestLen = 0
  for (const name of Object.keys(official)) {
    const parts = norm(name).split(' ')
    if (parts.every(p => words.has(p)) && norm(name).length > bestLen) {
      best = official[name] as string; bestLen = norm(name).length
    }
  }
  if (best) return best
  return localityMeta.value[locality]?.ward || ''
}

function applyWardFromLocality() {
  const ward = wardForLocality(form.value.locality)
  if (ward) { form.value.ward = ward; wardAutoSet.value = true }
  else { wardAutoSet.value = false }   // the map click will settle it
}

function onLocalityChange() {
  applyWardFromLocality()
  // A street chosen under the previous locality may not be on offer any more.
  if (form.value.registry_street_id
      && !selectableStreets.value.some(s => String(s.id) === String(form.value.registry_street_id))) {
    form.value.registry_street_id = ''
    onRegistryStreetChange()
  }
  if (streetLocked.value) return       // keep the map framed on the locked street
  zoomToLocality()
}

// A handful of survey points carry bad GPS fixes or a mis-typed locality, and they
// sit kilometres from the community they are filed under — fitting the map to every
// point then zooms out to the whole state instead of the locality. Drop the strays:
// keep the points within 3x the 90th-percentile distance from the cluster's median
// centre (at least 800 m, so a genuinely compact locality is never cut). That is
// conservative enough to keep >=99% of the points in every locality we have.
function coreCluster(pts: [number, number][]): [number, number][] {
  if (pts.length < 10) return pts
  const median = (xs: number[]) => {
    const v = [...xs].sort((a, b) => a - b)
    const m = Math.floor(v.length / 2)
    return v.length % 2 ? (v[m] as number) : (((v[m - 1] as number) + (v[m] as number)) / 2)
  }
  const cLat = median(pts.map(p => p[0]))
  const cLng = median(pts.map(p => p[1]))
  const dists = pts.map(p => Math.hypot(
    (p[0] - cLat) * 111000,
    (p[1] - cLng) * 111000 * Math.cos(cLat * Math.PI / 180),
  ))
  const sorted = [...dists].sort((a, b) => a - b)
  const p90 = sorted[Math.floor((sorted.length - 1) * 0.9)] as number
  const cutoff = Math.max(p90 * 3, 800)
  const kept = pts.filter((_, i) => (dists[i] as number) <= cutoff)
  return kept.length >= 5 ? kept : pts
}

function zoomToLocality() {
  const sel = form.value.locality
  if (!pickerMap || !sel) return
  if (!pickPoints.length && !communities.value.length) { pendingZoomLocality = sel; return }
  pickerMap.invalidateSize()   // Leaflet mis-measures a container that was hidden

  // 1. Its own surveyed buildings — the best evidence of where a place is.
  const pts = coreCluster(localityMeta.value[sel]?.pts || [])
  if (pts.length >= 1) {
    pickerMap.fitBounds(L.latLngBounds(pts).pad(0.25), { maxZoom: 16 })
    return
  }

  // 2. No buildings surveyed here: go to the middle of the community.
  const community = communities.value.find(c => c.name === sel)
  if (community?.latitude != null && community.longitude != null) {
    pickerMap.setView([community.latitude, community.longitude], 15)
    return
  }

  // 3. Nobody has mapped it. Show the ward it belongs to, which we do know,
  //    rather than leaving the applicant staring at the whole LGA.
  const ward = community?.ward
  const sameWard = communities.value.filter(
    c => c.ward === ward && c.latitude != null && c.longitude != null)
  if (ward && sameWard.length) {
    pickerMap.fitBounds(
      L.latLngBounds(sameWard.map(c => [c.latitude as number, c.longitude as number])).pad(0.2),
      { maxZoom: 14 })
  }
}

// --- Map street picker ---
interface PickPoint { lat: number; lng: number; is_named: boolean; street_name: string; existing_street_name: string; locality: string; ward: string; photo_url: string }
const pickerMapEl = ref<HTMLElement | null>(null)
const pickerLoading = ref(true)
const recognized = ref<{ is_named: boolean; name: string; locality: string; photo_url: string } | null>(null)
const streetTaken = ref('')  // set when another applicant is already pursuing this street (item 1)
let pickerMap: L.Map | null = null
let streetLabelLayer: L.LayerGroup | null = null
let pendingZoomLocality = ""
let clickMarker: L.CircleMarker | null = null
let streetHighlightLayer: L.LayerGroup | null = null
let streetLineLayer: L.LayerGroup | null = null

// --- The road network: what the applicant actually taps ------------------------
// OpenStreetMap names barely a twentieth of the roads here but has the shape of
// nearly all of them, and 94% of surveyed buildings sit within 60 m of one. So
// the applicant points at the road they live on instead of dropping a pin, and
// sees the whole street light up. Roads are drawn wide and invisible over the
// basemap, which is already showing them — the tap target, not the picture.
interface RoadSegment { id: number; name: string; geometry: string }
const ROAD_IDLE = 0.22          // enough to read as "these are tappable"
const ROAD_HOVER = 0.45
let roadLayer: L.LayerGroup | null = null
let roadsLoadedFor = ''
const roadsInView = ref<{ road: RoadSegment; line: [number, number][] }[]>([])
const pickedRoad = ref<{ id: number; name: string; line: [number, number][] } | null>(null)
const roadsLoading = ref(false)

async function loadRoadsInView() {
  if (!pickerMap) return
  const b = pickerMap.getBounds()
  // One decimal place of slack, so small pans reuse what is already loaded.
  const key = [b.getSouth(), b.getWest(), b.getNorth(), b.getEast()]
    .map(n => n.toFixed(2)).join(',')
  if (key === roadsLoadedFor) return
  if (pickerMap.getZoom() < 14) return       // whole-LGA view: too many to be useful
  roadsLoadedFor = key
  roadsLoading.value = true
  try {
    const bbox = `${b.getSouth()},${b.getWest()},${b.getNorth()},${b.getEast()}`
    const { data } = await configApi.getRoadNetwork(bbox)
    drawRoads(data as RoadSegment[])
  } catch { /* the map still works; the applicant can drop a pin */ }
  finally { roadsLoading.value = false }
}

function drawRoads(roads: RoadSegment[]) {
  if (!pickerMap) return
  if (!roadLayer) roadLayer = L.layerGroup().addTo(pickerMap)
  roadLayer.clearLayers()
  roadsInView.value = []
  for (const road of roads) {
    const line = lineOf(road.geometry)
    if (!line) continue
    roadsInView.value.push({ road, line })
    // Faintly tinted rather than invisible: on a phone there is no hover, so the
    // roads have to *look* tappable or nobody will think to tap them.
    const hit = L.polyline(line, { color: '#0284c7', weight: 12, opacity: ROAD_IDLE })
      .addTo(roadLayer)
    hit.on('mouseover', () => hit.setStyle({ opacity: ROAD_HOVER }))
    hit.on('mouseout', () => {
      if (pickedRoad.value?.id !== road.id) hit.setStyle({ opacity: ROAD_IDLE })
    })
    hit.on('click', (e: L.LeafletMouseEvent) => {
      L.DomEvent.stopPropagation(e)          // tapping a road is not dropping a pin
      pickRoad(road, line)
    })
  }
  // The labels are read off these roads, so they are only right once the roads
  // are here — 'moveend' fires long before this load comes back.
  refreshStreetLabels()
}

/** Identifies a line by its endpoints, so two copies of one road compare equal. */
function lineKey(line: [number, number][] | null): string {
  if (!line || line.length < 2) return ''
  const a = line[0]!, b = line[line.length - 1]!
  return `${a[0].toFixed(6)},${a[1].toFixed(6)}|${b[0].toFixed(6)},${b[1].toFixed(6)}`
}

/** Does this road already carry a name — its own, or one on the register?
 *
 *  Judged on the road the applicant tapped. Reading the nearest surveyed
 *  building instead told people their road was "Agbaje Street" because a
 *  building on the next street over was, and called a plainly labelled road
 *  unnamed because the buildings along it had no name recorded.
 */
function nameOfRoad(road: RoadSegment, line: [number, number][]): string {
  if ((road.name || '').trim()) return road.name.trim()
  // A registered street that was located on this very road carries the road's
  // own line, so the two lines are identical — the surest match there is, and it
  // does not care how far the street's marker point drifted from it.
  const key = lineKey(line)
  if (key) {
    for (const st of registryStreets.value) {
      if (st.geometry && lineKey(lineOf(st.geometry)) === key) return st.name
    }
  }
  // Otherwise fall back to a registry street sitting on this road.
  let best = '', bestD = Infinity
  for (const st of registryStreets.value) {
    if (st.latitude == null || st.longitude == null) continue
    const sLat = Number(st.latitude), sLng = Number(st.longitude)
    for (const [lat, lng] of line) {
      const d = Math.hypot((lat - sLat) * 111000,
                           (lng - sLng) * 111000 * Math.cos(lat * Math.PI / 180))
      if (d < bestD) { bestD = d; best = st.name }
    }
  }
  return bestD <= 40 ? best : ''      // 40 m: on this road, not the next one
}

/** The applicant tapped a road: adopt its whole length as their street. */
function pickRoad(road: RoadSegment, line: [number, number][]) {
  if (streetLocked.value) return
  const mid = line[Math.floor(line.length / 2)] as [number, number]
  selectAt(mid[0], mid[1])
  const existing = nameOfRoad(road, line)
  // selectAt guessed from the nearest building; the road itself knows better.
  recognized.value = { is_named: !!existing, name: existing, locality: '', photo_url: '' }
  drawStreetHighlight(line, existing || form.value.proposed_street_name || 'Selected street', true)
  pickedRoad.value = { id: road.id, name: existing, line }
}

function clearPickedRoad() {
  pickedRoad.value = null
  clearStreetHighlight()
  clearPickedLocation()
}

/** Parse a stored GeoJSON LineString into Leaflet's [lat, lng] order. */
function lineOf(geometry?: string | null): [number, number][] | null {
  if (!geometry) return null
  try {
    const geo = JSON.parse(geometry)
    const coords = geo?.type === 'LineString' ? geo.coordinates
      : geo?.type === 'MultiLineString' ? geo.coordinates.flat() : null
    if (!Array.isArray(coords) || coords.length < 2) return null
    return coords.map((c: number[]) => [c[1] as number, c[0] as number])
  } catch { return null }
}

/** Every registry street we hold a centre-line for, drawn so it can be clicked.
 *  Picking the line is the marking; the pin is only for streets we have no line
 *  for. Buildings are deliberately not drawn — they are not the street. */
function drawRegistryStreetLines() {
  if (!pickerMap || !streetLineLayer) return
  streetLineLayer.clearLayers()
  for (const st of registryStreets.value) {
    const line = lineOf(st.geometry)
    if (!line) continue
    L.polyline(line, { color: '#ffffff', weight: 8, opacity: 0.7 }).addTo(streetLineLayer)
    const poly = L.polyline(line, { color: '#0284c7', weight: 4, opacity: 0.9 })
      .addTo(streetLineLayer)
      .bindTooltip(st.name, { sticky: true })
    poly.on('click', (e: L.LeafletMouseEvent) => {
      L.DomEvent.stopPropagation(e)          // do not also drop a pin underneath
      pickStreetLine(st)
    })
  }
}

/** The applicant clicked a street line on the map. */
function pickStreetLine(street: RegistryStreet) {
  if (usesRegistry.value) {
    // Here the dropdown is the source of truth; clicking the street selects it
    // there so the two can never disagree.
    form.value.registry_street_id = String(street.id)
    onRegistryStreetChange()
    return
  }
  const line = lineOf(street.geometry)
  if (!line) return
  const mid = line[Math.floor(line.length / 2)] as [number, number]
  selectAt(mid[0], mid[1])
  drawStreetHighlight(line, street.name, true)
  pickedStreetName.value = street.name
}
const pickedStreetName = ref('')
const pickPoints: PickPoint[] = []

function clearStreetHighlight() {
  if (streetHighlightLayer) { streetHighlightLayer.remove(); streetHighlightLayer = null }
}

/** Drop a previously picked location, so switching streets can never carry the
 *  old street's coordinates onto the new one. */
function clearPickedLocation() {
  if (clickMarker) { clickMarker.remove(); clickMarker = null }
  geoCoords.value = { lat: '', lng: '', accuracy: '' }
  geoState.value = 'idle'
  recognized.value = null
  form.value.location_description = ''
}

/** Paint the selected registry street on the map and frame it. */
function drawStreetHighlight(pts: [number, number][], name: string, asLine = false) {
  if (!pickerMap) return
  clearStreetHighlight()
  streetHighlightLayer = L.layerGroup().addTo(pickerMap)
  if (asLine && pts.length >= 2) {
    // A real centre-line: draw the street, not a string of beads.
    L.polyline(pts, { color: '#ffffff', weight: 11, opacity: 0.9, interactive: false })
      .addTo(streetHighlightLayer)
    L.polyline(pts, { color: '#047857', weight: 6, opacity: 1, interactive: false })
      .addTo(streetHighlightLayer)
  } else {
    for (const [lat, lng] of pts) {
      L.circleMarker([lat, lng], {
        radius: 7, color: '#047857', weight: 2, fillColor: '#34d399', fillOpacity: 0.85, interactive: false,
      }).addTo(streetHighlightLayer)
    }
  }
  const cLat = pts.reduce((a, p) => a + p[0], 0) / pts.length
  const cLng = pts.reduce((a, p) => a + p[1], 0) / pts.length
  L.marker([cLat, cLng], {
    interactive: false,
    icon: L.divIcon({
      className: 'street-name-label',
      html: `<span style="background:#047857;color:#fff;border-radius:4px;padding:2px 7px;font-size:11px;font-weight:700;white-space:nowrap;box-shadow:0 1px 4px rgba(0,0,0,0.25)">${name.replace(/</g, '')}</span>`,
      iconSize: [0, 0],
    }),
  }).addTo(streetHighlightLayer)
  pickerMap.invalidateSize()
  if (pts.length === 1) pickerMap.setView(pts[0] as L.LatLngTuple, 17)
  else pickerMap.fitBounds(L.latLngBounds(pts).pad(0.4), { maxZoom: 17 })
}

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
  // Item 1: is this street already being pursued by another applicant?
  streetTaken.value = ''
  if (!usesRegistry.value) {
    applicationApi.streetAvailability(lat.toFixed(6), lng.toFixed(6))
      .then(({ data }) => {
        if (data && data.available === false) {
          streetTaken.value = data.reason || 'This street is already being considered for registration by another applicant.'
        }
      })
      .catch(() => {})
  }
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
    if (!form.value.locality && near.pt.locality) {
      form.value.locality = near.pt.locality
      applyWardFromLocality()
    }
    // Last resort for a locality the council's list does not carry: the ward the
    // enumerator recorded for the nearest surveyed building.
    if (!form.value.ward) {
      const w = normalizeWard(near.pt.ward || '')
      if (w) { form.value.ward = w; wardAutoSet.value = true }
    }
  } else {
    recognized.value = { is_named: false, name: '', locality: '', photo_url: '' }
  }
}

function locateMe() {
  if (streetLocked.value) return
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
  pickerMap.on('click', (e: L.LeafletMouseEvent) => {
    // Validate mode with a registry location: the street is fixed, ignore clicks.
    if (streetLocked.value) return
    // A click that misses every road: keep the pin as the fallback, exactly as
    // before. Taps that land on a road are handled by the road layer itself.
    pickedRoad.value = null
    clearStreetHighlight()
    selectAt(e.latlng.lat, e.latlng.lng)
  })
  streetLabelLayer = L.layerGroup().addTo(pickerMap)
  streetLineLayer = L.layerGroup().addTo(pickerMap)
  pickerMap.on('zoomend moveend', refreshStreetLabels)
  pickerMap.on('zoomend moveend', loadRoadsInView)
  drawRegistryStreetLines()
  loadRoadsInView()
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
    // A street chosen while the map was still loading can now be located.
    if (streetPendingId) { streetPendingId = ''; onRegistryStreetChange() }
  }
}

// Overlay existing street names (from the survey records) as labels, so the
// applicant can see the names of nearby streets on the auto-zoomed map.
/** Name labels, placed on the road they belong to.
 *
 *  These used to be drawn at the centre of a cluster of surveyed buildings, which
 *  put the label between roads rather than on one — so a label and the road under
 *  it could disagree about the name. A label now sits on the road that carries it,
 *  and says exactly what tapping that road will say.
 */
function refreshStreetLabels() {
  if (!pickerMap || !streetLabelLayer) return
  streetLabelLayer.clearLayers()
  if (pickerMap.getZoom() < 15) return  // only when zoomed in enough to be readable
  const b = pickerMap.getBounds()
  const placed: Record<string, { lat: number; lng: number }> = {}
  for (const { road, line } of roadsInView.value) {
    const name = nameOfRoad(road, line)
    if (!name) continue
    const mid = line[Math.floor(line.length / 2)] as [number, number]
    if (!b.contains(mid as L.LatLngTuple)) continue
    if (placed[name]) continue          // one label per name keeps it readable
    placed[name] = { lat: mid[0], lng: mid[1] }
  }
  for (const name of Object.keys(placed).slice(0, 60)) {
    const at = placed[name]!
    L.marker([at.lat, at.lng], {
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
    if (usesRegistry.value && legacyCertFile.value) {
      const selected = registryStreets.value.find(s => String(s.id) === String(form.value.registry_street_id))
      const fd = new FormData()
      // In validate mode the name comes from the selected registry street.
      fd.append('proposed_street_name', selected?.name || '')
      fd.append('registry_street_id', String(form.value.registry_street_id))
      fd.append('street_type', form.value.street_type || '')
      fd.append('ward', form.value.ward)
      if (pickedRoad.value) fd.append('street_line', JSON.stringify({
        type: 'LineString',
        coordinates: pickedRoad.value.line.map(([la, ln]) => [ln, la]),
      }))
      fd.append('locality', form.value.locality)
      fd.append('location_description', form.value.location_description)
      if (geoCoords.value.lat) fd.append('latitude', geoCoords.value.lat)
      if (geoCoords.value.lng) fd.append('longitude', geoCoords.value.lng)
      // A renewal and a validation are different kinds of application, and the
      // council counts them apart.
      fd.append('is_legacy', isLegacy.value ? 'true' : 'false')
      fd.append('is_renewal_request', isRenewal.value ? 'true' : 'false')
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
        // The street's own line, when the applicant tapped a road rather than
        // dropping a pin — this is the shape the register has always lacked.
        street_line: pickedRoad.value
          ? JSON.stringify({ type: 'LineString',
                             coordinates: pickedRoad.value.line.map(([la, ln]) => [ln, la]) })
          : '',
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
  configApi.getLocalityWards().then(r => { localityWards.value = r.data.community_to_ward || {} }).catch(() => {})
  configApi.getCommunities().then(r => {
    communities.value = r.data as Community[]
    rebuildLocalityIndex()          // the picker is the council's list
    if (form.value.locality) zoomToLocality()
  }).catch(() => {})
  configApi.publicSettings().then(r => { googleEnabled.value = !!r.data.google_maps_enabled }).catch(() => {})
  // Loaded whichever mode this is: validation needs the list, and a new
  // application needs the lines to be visible and clickable on the map.
  configApi.getStreets().then(r => {
    registryStreets.value = (r.data as RegistryStreet[]).slice()
      .sort((a, b) => a.name.localeCompare(b.name))
    drawRegistryStreetLines()
    refreshStreetLabels()          // a road's name may come from this list
  }).catch(() => {})
  initPicker()
})

// The new-application and validate flows share this route, so navigating between
// them (or re-entering) reuses this component instance. Re-initialise on every
// entry so the map always rebuilds and re-zooms to the selected locality.
watch(() => route.fullPath, async () => {
  if (route.name !== 'application-new' && !route.path.startsWith('/applications/new')) return
  isLegacy.value = route.query.mode === 'legacy'
  isRenewal.value = route.query.mode === 'renewal'
  // reset the form for a clean entry
  form.value = { proposed_street_name: '', street_type: '', ward: '', locality: '', location_description: '', registry_street_id: '' }
  geoCoords.value = { lat: '', lng: '', accuracy: '' }
  recognized.value = null
  streetTaken.value = ''
  validateNote.value = null
  streetLocked.value = false
  wrongStreet.value = false
  streetPendingId = ''
  clearStreetHighlight()
  legacyCertFile.value = null
  pickPoints.length = 0
  pendingZoomLocality = ''
  if (pickerMap) { pickerMap.remove(); pickerMap = null }
  pickerLoading.value = true
  if (!registryStreets.value.length) {
    configApi.getStreets().then(r => {
      registryStreets.value = (r.data as RegistryStreet[]).slice()
        .sort((a, b) => a.name.localeCompare(b.name))
      drawRegistryStreetLines()
      refreshStreetLabels()
    }).catch(() => {})
  }
  await initPicker()
})

onUnmounted(() => { if (pickerMap) { pickerMap.remove(); pickerMap = null } })
</script>
