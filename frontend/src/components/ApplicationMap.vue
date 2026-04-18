<template>
  <div>
    <div v-if="hasMapData" class="relative">
      <!-- Map -->
      <div ref="mapEl" class="w-full rounded-xl overflow-hidden" style="height: 300px; z-index: 0;"></div>

      <!-- Top-right controls -->
      <div class="absolute top-2 right-2 z-[400] flex gap-1.5">
        <button
          class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold shadow-md transition-all hover:scale-105 active:scale-95"
          style="background: rgba(255,255,255,0.92); color: #0f172a; border: 1px solid rgba(0,0,0,0.1); backdrop-filter: blur(4px)"
          @click="openModal"
        >
          <ArrowsPointingOutIcon class="w-3.5 h-3.5" />
          Expand
        </button>
      </div>

      <!-- Loading badge -->
      <div v-if="surveysLoading"
           class="absolute bottom-2 left-2 z-[400] flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs"
           style="background: rgba(255,255,255,0.92); border: 1px solid rgba(0,0,0,0.1)">
        <div class="w-3 h-3 rounded-full border border-slate-300 border-t-emerald-500 animate-spin"></div>
        <span class="text-slate-600">Loading buildings…</span>
      </div>

      <!-- Legend -->
      <div v-if="allSurveys.length && !surveysLoading"
           class="absolute bottom-2 left-2 z-[400] flex flex-col gap-1 px-2.5 py-2 rounded-lg text-xs"
           style="background: rgba(255,255,255,0.92); border: 1px solid rgba(0,0,0,0.1); backdrop-filter: blur(4px)">
        <div v-if="matchedSurveys.length" class="flex items-center gap-1.5">
          <span class="w-3 h-3 rounded-full flex-shrink-0" style="background: #059669; border: 1.5px solid #047857"></span>
          <span class="text-slate-700 font-medium">{{ streetName || 'Proposed street' }} ({{ matchedSurveys.length }})</span>
        </div>
        <div v-if="otherSurveys.length" class="flex items-center gap-1.5">
          <span class="w-3 h-3 rounded-full flex-shrink-0" style="background: #94a3b8; border: 1.5px solid #64748b"></span>
          <span class="text-slate-700 font-medium">Other buildings ({{ otherSurveys.length }})</span>
        </div>
        <div v-if="coords" class="flex items-center gap-1.5">
          <span class="w-3 h-3 rounded-sm flex-shrink-0" style="background: #1d4ed8; border: 1.5px solid #1e40af"></span>
          <span class="text-slate-700 font-medium">Application pin</span>
        </div>
        <div class="flex items-center gap-1.5 mt-0.5 pt-0.5" style="border-top: 1px solid #e2e8f0">
          <span class="text-slate-400 italic">Click a building to view details</span>
        </div>
      </div>
    </div>

    <div v-else class="flex flex-col items-center py-10 gap-2">
      <MapPinIcon class="w-8 h-8 text-slate-300" />
      <p class="text-sm text-slate-500">No location data available for this application.</p>
    </div>

    <!-- Building detail panel — shown when a marker is clicked -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-1"
    >
      <div
        v-if="selectedBuilding"
        class="mt-3 rounded-xl overflow-hidden"
        style="border: 1px solid #e2e8f0; background: #fff"
      >
        <div class="flex items-center justify-between px-4 py-3" style="border-bottom: 1px solid #f1f5f9">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  :style="isMatched(selectedBuilding) ? 'background:#059669' : 'background:#94a3b8'"></span>
            <p class="text-sm font-bold text-slate-900">{{ selectedBuilding.proposed_street_name }}</p>
            <span v-if="selectedBuilding.proposed_auto_number"
                  class="text-xs font-mono font-semibold px-1.5 py-0.5 rounded"
                  style="background: #f1f5f9; color: #475569">
              No. {{ selectedBuilding.proposed_auto_number }}
            </span>
          </div>
          <button @click="selectedBuilding = null" class="text-slate-400 hover:text-slate-600 transition-colors">
            <XMarkIcon class="w-4 h-4" />
          </button>
        </div>

        <div class="flex gap-0" style="min-height: 160px">
          <!-- Photo -->
          <div class="flex-shrink-0 w-52" style="border-right: 1px solid #f1f5f9">
            <div v-if="selectedBuilding.photo_url" class="relative h-full" style="min-height:160px">
              <img
                :src="selectedBuilding.photo_url"
                class="w-full h-full object-cover"
                style="min-height:160px; max-height:200px"
                alt="Building frontage"
                @error="photoError = true"
              />
              <div v-if="photoError"
                   class="absolute inset-0 flex flex-col items-center justify-center gap-1"
                   style="background: #f8fafc">
                <PhotoIcon class="w-8 h-8 text-slate-300" />
                <span class="text-xs text-slate-400">Photo unavailable</span>
              </div>
              <a
                v-if="!photoError"
                :href="selectedBuilding.photo_url"
                target="_blank"
                class="absolute bottom-2 right-2 flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold"
                style="background: rgba(0,0,0,0.55); color: #fff; backdrop-filter: blur(2px)"
              >
                <ArrowTopRightOnSquareIcon class="w-3 h-3" />
                Full size
              </a>
            </div>
            <div v-else class="flex flex-col items-center justify-center h-full gap-2 p-4" style="min-height:160px; background:#f8fafc">
              <PhotoIcon class="w-8 h-8 text-slate-300" />
              <span class="text-xs text-slate-400 text-center">No photo captured</span>
            </div>
          </div>

          <!-- Details -->
          <div class="flex-1 p-4 flex flex-col justify-between gap-3">
            <dl class="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
              <div v-if="selectedBuilding.building_use">
                <dt class="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Use</dt>
                <dd class="text-slate-700 font-medium capitalize mt-0.5">{{ selectedBuilding.building_use }}</dd>
              </div>
              <div v-if="selectedBuilding.building_type">
                <dt class="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Type</dt>
                <dd class="text-slate-700 font-medium capitalize mt-0.5">
                  {{ selectedBuilding.building_type === 'others'
                    ? (selectedBuilding.building_type_other || 'Others')
                    : selectedBuilding.building_type.replace(/_/g, ' ') }}
                </dd>
              </div>
              <div v-if="selectedBuilding.number_of_floors">
                <dt class="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Floors</dt>
                <dd class="text-slate-700 font-medium mt-0.5">{{ selectedBuilding.number_of_floors }}</dd>
              </div>
              <div v-if="selectedBuilding.occupancy_type">
                <dt class="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Occupancy</dt>
                <dd class="text-slate-700 font-medium capitalize mt-0.5">{{ selectedBuilding.occupancy_type.replace(/_/g, ' ') }}</dd>
              </div>
              <div v-if="selectedBuilding.locality" class="col-span-2">
                <dt class="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Location</dt>
                <dd class="text-slate-700 font-medium mt-0.5">
                  {{ selectedBuilding.locality }}{{ selectedBuilding.ward ? ' · Ward ' + selectedBuilding.ward : '' }}
                </dd>
              </div>
            </dl>

            <!-- Street View link -->
            <a
              :href="`https://maps.google.com/?cbll=${selectedBuilding.latitude},${selectedBuilding.longitude}&cbp=12,0,,0,5&layer=c`"
              target="_blank"
              rel="noopener"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold self-start transition-all hover:scale-105"
              style="background: linear-gradient(135deg, #1d4ed8, #1e40af); color: #fff"
            >
              <MapIcon class="w-3.5 h-3.5" />
              Open in Google Street View
              <ArrowTopRightOnSquareIcon class="w-3 h-3 opacity-70" />
            </a>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Fullscreen modal -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="showModal"
          class="fixed inset-0 z-[1000] flex items-center justify-center p-4"
          style="background: rgba(0,0,0,0.65); backdrop-filter: blur(2px)"
          @click.self="closeModal"
        >
          <Transition
            enter-active-class="transition duration-200 ease-out"
            enter-from-class="opacity-0 scale-95"
            enter-to-class="opacity-100 scale-100"
            leave-active-class="transition duration-150 ease-in"
            leave-from-class="opacity-100 scale-100"
            leave-to-class="opacity-0 scale-95"
          >
            <div
              v-if="showModal"
              class="relative w-full max-w-6xl rounded-2xl overflow-hidden flex flex-col"
              style="height: 88vh; background: #fff; box-shadow: 0 25px 60px rgba(0,0,0,0.4)"
            >
              <!-- Modal header -->
              <div class="flex items-center gap-3 px-5 py-3.5 flex-shrink-0"
                   style="border-bottom: 1px solid #e2e8f0; background: #fff">
                <div class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                     style="background: rgba(5,150,105,0.08); border: 1px solid rgba(5,150,105,0.15)">
                  <MapPinIcon class="w-4 h-4" style="color: #059669" />
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-bold text-slate-900 truncate">{{ streetName || 'Street Location' }}</p>
                  <p v-if="coords" class="text-xs text-slate-400 font-mono">
                    {{ coords[0].toFixed(6) }}, {{ coords[1].toFixed(6) }}
                  </p>
                </div>
                <div v-if="allSurveys.length" class="flex items-center gap-4 mr-3 flex-shrink-0">
                  <div v-if="matchedSurveys.length" class="flex items-center gap-1.5">
                    <span class="w-2.5 h-2.5 rounded-full" style="background:#059669"></span>
                    <span class="text-xs text-slate-500">{{ streetName }} ({{ matchedSurveys.length }})</span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="w-2.5 h-2.5 rounded-full" style="background:#94a3b8"></span>
                    <span class="text-xs text-slate-500">Others ({{ otherSurveys.length }})</span>
                  </div>
                </div>
                <button
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-600 border border-slate-200 hover:bg-slate-50 transition-colors flex-shrink-0"
                  @click="closeModal"
                >
                  <ArrowsPointingInIcon class="w-3.5 h-3.5" />
                  Close
                </button>
              </div>

              <!-- Modal body: map + street view panel side by side -->
              <div class="flex flex-1 min-h-0">
                <!-- Map -->
                <div ref="modalMapEl" class="flex-1 min-w-0"></div>

                <!-- Street view panel in modal -->
                <Transition
                  enter-active-class="transition duration-200 ease-out"
                  enter-from-class="opacity-0 translate-x-4"
                  enter-to-class="opacity-100 translate-x-0"
                  leave-active-class="transition duration-150 ease-in"
                  leave-from-class="opacity-100 translate-x-0"
                  leave-to-class="opacity-0 translate-x-4"
                >
                  <div
                    v-if="selectedBuilding"
                    class="flex-shrink-0 flex flex-col overflow-y-auto"
                    style="width: 300px; border-left: 1px solid #e2e8f0; background: #fff"
                  >
                    <!-- Panel header -->
                    <div class="flex items-center justify-between px-4 py-3 flex-shrink-0"
                         style="border-bottom: 1px solid #f1f5f9">
                      <div>
                        <p class="text-sm font-bold text-slate-900 leading-tight">
                          {{ selectedBuilding.proposed_street_name }}
                        </p>
                        <p v-if="selectedBuilding.proposed_auto_number" class="text-xs text-slate-500 font-mono mt-0.5">
                          No. {{ selectedBuilding.proposed_auto_number }}
                        </p>
                      </div>
                      <button @click="selectedBuilding = null" class="text-slate-400 hover:text-slate-600 ml-2">
                        <XMarkIcon class="w-4 h-4" />
                      </button>
                    </div>

                    <!-- Building photo -->
                    <div class="flex-shrink-0" style="height: 200px; background: #f8fafc">
                      <img
                        v-if="selectedBuilding.photo_url && !photoError"
                        :src="selectedBuilding.photo_url"
                        class="w-full h-full object-cover"
                        alt="Building frontage"
                        @error="photoError = true"
                      />
                      <div v-else class="flex flex-col items-center justify-center h-full gap-2">
                        <PhotoIcon class="w-10 h-10 text-slate-300" />
                        <span class="text-xs text-slate-400">
                          {{ selectedBuilding.photo_url ? 'Photo unavailable' : 'No photo captured' }}
                        </span>
                      </div>
                    </div>

                    <!-- Building details -->
                    <div class="p-4 flex flex-col gap-4 flex-1">
                      <dl class="space-y-2.5 text-xs">
                        <div v-if="selectedBuilding.building_use" class="flex justify-between">
                          <dt class="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Use</dt>
                          <dd class="text-slate-700 font-medium capitalize">{{ selectedBuilding.building_use }}</dd>
                        </div>
                        <div v-if="selectedBuilding.building_type" class="flex justify-between">
                          <dt class="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Type</dt>
                          <dd class="text-slate-700 font-medium capitalize">
                            {{ selectedBuilding.building_type === 'others'
                              ? (selectedBuilding.building_type_other || 'Others')
                              : selectedBuilding.building_type.replace(/_/g, ' ') }}
                          </dd>
                        </div>
                        <div v-if="selectedBuilding.number_of_floors" class="flex justify-between">
                          <dt class="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Floors</dt>
                          <dd class="text-slate-700 font-medium">{{ selectedBuilding.number_of_floors }}</dd>
                        </div>
                        <div v-if="selectedBuilding.number_of_flats" class="flex justify-between">
                          <dt class="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Flats</dt>
                          <dd class="text-slate-700 font-medium">{{ selectedBuilding.number_of_flats }}</dd>
                        </div>
                        <div v-if="selectedBuilding.number_of_shops" class="flex justify-between">
                          <dt class="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Shops</dt>
                          <dd class="text-slate-700 font-medium">{{ selectedBuilding.number_of_shops }}</dd>
                        </div>
                        <div v-if="selectedBuilding.occupancy_type" class="flex justify-between">
                          <dt class="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Occupancy</dt>
                          <dd class="text-slate-700 font-medium capitalize">
                            {{ selectedBuilding.occupancy_type.replace(/_/g, ' ') }}
                          </dd>
                        </div>
                        <div v-if="selectedBuilding.locality" class="flex justify-between">
                          <dt class="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Locality</dt>
                          <dd class="text-slate-700 font-medium">{{ selectedBuilding.locality }}</dd>
                        </div>
                        <div v-if="selectedBuilding.ward" class="flex justify-between">
                          <dt class="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Ward</dt>
                          <dd class="text-slate-700 font-medium">{{ selectedBuilding.ward }}</dd>
                        </div>
                        <div class="flex justify-between">
                          <dt class="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Coordinates</dt>
                          <dd class="text-slate-500 font-mono text-[10px]">
                            {{ selectedBuilding.latitude.toFixed(5) }}, {{ selectedBuilding.longitude.toFixed(5) }}
                          </dd>
                        </div>
                      </dl>

                      <!-- Actions -->
                      <div class="flex flex-col gap-2 mt-auto">
                        <a
                          :href="`https://maps.google.com/?cbll=${selectedBuilding.latitude},${selectedBuilding.longitude}&cbp=12,0,,0,5&layer=c`"
                          target="_blank"
                          rel="noopener"
                          class="flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all hover:opacity-90"
                          style="background: linear-gradient(135deg, #1d4ed8, #1e40af); color: #fff"
                        >
                          <MapIcon class="w-3.5 h-3.5" />
                          Google Street View
                          <ArrowTopRightOnSquareIcon class="w-3 h-3 opacity-70" />
                        </a>
                        <a
                          v-if="selectedBuilding.photo_url"
                          :href="selectedBuilding.photo_url"
                          target="_blank"
                          rel="noopener"
                          class="flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all hover:opacity-90"
                          style="background: #f1f5f9; color: #334155; border: 1px solid #e2e8f0"
                        >
                          <PhotoIcon class="w-3.5 h-3.5" />
                          View Full Photo
                          <ArrowTopRightOnSquareIcon class="w-3 h-3 opacity-50" />
                        </a>
                      </div>
                    </div>
                  </div>
                </Transition>
              </div>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import {
  MapPinIcon, ArrowsPointingOutIcon, ArrowsPointingInIcon,
  XMarkIcon, PhotoIcon, MapIcon, ArrowTopRightOnSquareIcon,
} from '@heroicons/vue/24/outline'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
import { configApi } from '@/services/api'

delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({ iconUrl: markerIcon, iconRetinaUrl: markerIcon2x, shadowUrl: markerShadow })

interface SurveyBuilding {
  kobo_id: number
  latitude: number
  longitude: number
  proposed_street_name: string
  proposed_auto_number: string
  building_use: string
  building_type: string
  building_type_other: string
  locality: string
  ward: string
  number_of_floors: number | null
  number_of_flats: number | null
  number_of_shops: number | null
  occupancy_type: string
  photo_url: string
}

const props = defineProps<{
  locationDescription?: string
  streetName?: string
  proposedStreetName?: string
}>()

const mapEl = ref<HTMLElement | null>(null)
const modalMapEl = ref<HTMLElement | null>(null)
const showModal = ref(false)
const allSurveys = ref<SurveyBuilding[]>([])
const surveysLoading = ref(false)
const selectedBuilding = ref<SurveyBuilding | null>(null)
const photoError = ref(false)

let map: L.Map | null = null
let modalMap: L.Map | null = null

const coords = computed<[number, number] | null>(() => {
  const raw = props.locationDescription?.trim()
  if (!raw) return null
  const match = raw.match(/^(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)$/)
  if (!match) return null
  const lat = parseFloat(match[1])
  const lng = parseFloat(match[2])
  if (isNaN(lat) || isNaN(lng)) return null
  return [lat, lng]
})

const matchedSurveys = computed(() => {
  if (!props.proposedStreetName) return []
  const term = props.proposedStreetName.toLowerCase().trim()
  return allSurveys.value.filter(s =>
    s.proposed_street_name.toLowerCase().includes(term)
  )
})

const otherSurveys = computed(() => {
  if (!props.proposedStreetName) return allSurveys.value
  const matched = new Set(matchedSurveys.value.map(s => s.kobo_id))
  return allSurveys.value.filter(s => !matched.has(s.kobo_id))
})

const hasMapData = computed(() => !!coords.value || allSurveys.value.length > 0)

function isMatched(s: SurveyBuilding): boolean {
  return matchedSurveys.value.some(m => m.kobo_id === s.kobo_id)
}

async function loadSurveys() {
  if (!props.proposedStreetName) return
  surveysLoading.value = true
  try {
    const res = await configApi.getBuildingSurveys()
    const data = res.data
    allSurveys.value = (Array.isArray(data) ? data : (data.results ?? [])).filter(
      (s: SurveyBuilding) => s.latitude != null && s.longitude != null
    )
  } catch {
    // map still works without survey overlay
  } finally {
    surveysLoading.value = false
  }
}

function selectBuilding(s: SurveyBuilding) {
  photoError.value = false
  selectedBuilding.value = s
}

function addSurveyMarkers(m: L.Map) {
  // Grey circles for non-matching buildings
  for (const s of otherSurveys.value) {
    L.circleMarker([s.latitude, s.longitude], {
      radius: 5,
      fillColor: '#94a3b8',
      color: '#64748b',
      weight: 1,
      opacity: 0.7,
      fillOpacity: 0.55,
    }).addTo(m).on('click', () => selectBuilding(s))
  }

  // Emerald circles for matched buildings
  for (const s of matchedSurveys.value) {
    L.circleMarker([s.latitude, s.longitude], {
      radius: 9,
      fillColor: '#059669',
      color: '#047857',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.9,
    }).addTo(m).on('click', () => selectBuilding(s))
  }
}

function initMap(el: HTMLElement, scrollWheel: boolean): L.Map {
  const m = L.map(el, { scrollWheelZoom: scrollWheel })

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(m)

  addSurveyMarkers(m)

  if (coords.value) {
    L.marker(coords.value)
      .addTo(m)
      .bindPopup(
        (props.streetName ? `<strong>${props.streetName}</strong><br/>` : '') +
        `<small>${coords.value[0].toFixed(6)}, ${coords.value[1].toFixed(6)}</small>`
      )
  }

  // Always centre on the application location first
  if (coords.value) {
    m.setView(coords.value, 16)
  } else if (matchedSurveys.value.length > 0) {
    const group = L.featureGroup(
      matchedSurveys.value.map(s => L.circleMarker([s.latitude, s.longitude]))
    )
    m.fitBounds(group.getBounds(), { padding: [40, 40], maxZoom: 17 })
  } else if (allSurveys.value.length > 0) {
    const group = L.featureGroup(
      allSurveys.value.map(s => L.circleMarker([s.latitude, s.longitude]))
    )
    m.fitBounds(group.getBounds(), { padding: [40, 40], maxZoom: 15 })
  } else {
    m.setView([6.465, 3.665], 13)
  }

  return m
}

onMounted(async () => {
  await loadSurveys()
  if (!mapEl.value || !hasMapData.value) return
  map = initMap(mapEl.value, false)
})

async function openModal() {
  showModal.value = true
  await nextTick()
  await nextTick()
  if (modalMapEl.value && !modalMap && hasMapData.value) {
    modalMap = initMap(modalMapEl.value, true)
  }
  document.body.style.overflow = 'hidden'
}

function closeModal() {
  showModal.value = false
  document.body.style.overflow = ''
  modalMap?.remove()
  modalMap = null
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && showModal.value) closeModal()
}

onMounted(() => window.addEventListener('keydown', onKeydown))

onUnmounted(() => {
  map?.remove()
  map = null
  modalMap?.remove()
  modalMap = null
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>
