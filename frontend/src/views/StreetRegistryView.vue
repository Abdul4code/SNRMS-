<template>
  <div class="min-h-screen" style="background: #f1f5f9">
    <div style="background: #0f172a">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Street Registry</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">Ibeju-Lekki Street Map</h1>
        <p class="text-slate-400 text-sm mt-1">Named streets across Ibeju-Lekki Local Government Area. Choose a locality to zoom in.</p>

        <!-- Locality selector — zooms the map to the chosen locality -->
        <div class="mt-4 flex items-center gap-2">
          <label class="text-xs font-semibold text-slate-300">Locality</label>
          <div class="relative">
            <select v-model="selectedLocality" @change="zoomToLocalitySel"
                    class="appearance-none rounded-lg bg-white/10 text-white text-sm px-3 py-2 pr-8 border border-white/15 focus:outline-none focus:ring-2 focus:ring-emerald-500">
              <option value="" style="color:#0f172a">Whole LGA</option>
              <option v-for="l in localities" :key="l" :value="l" style="color:#0f172a">{{ l }}</option>
            </select>
            <ChevronDownIcon class="w-4 h-4 text-white/60 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <!-- Registry metrics — ADMIN ONLY -->
      <div v-if="isStaff && summary" class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="rounded-2xl p-5 bg-white border border-slate-200">
          <p class="text-3xl font-bold tracking-tight" style="color:#059669">{{ summary.named_streets.toLocaleString() }}</p>
          <p class="text-xs text-slate-500 mt-1 font-semibold uppercase tracking-wide">Named streets</p>
        </div>
        <div class="rounded-2xl p-5 bg-white border border-slate-200">
          <p class="text-3xl font-bold tracking-tight" style="color:#d97706">{{ summary.unnamed_streets.toLocaleString() }}</p>
          <p class="text-xs text-slate-500 mt-1 font-semibold uppercase tracking-wide">Unnamed streets</p>
        </div>
        <div class="rounded-2xl p-5 bg-white border border-slate-200">
          <p class="text-3xl font-bold tracking-tight text-slate-900">{{ summary.renaming_in_progress.toLocaleString() }}</p>
          <p class="text-xs text-slate-500 mt-1 font-semibold uppercase tracking-wide">Naming in progress</p>
        </div>
      </div>

      <div class="grid grid-cols-1" :class="isStaff ? 'lg:grid-cols-3 gap-6' : ''">
        <!-- Map -->
        <div :class="isStaff ? 'lg:col-span-2' : ''" class="rounded-2xl overflow-hidden bg-white border border-slate-200">
          <div v-if="loading" class="h-[560px] flex flex-col items-center justify-center gap-3 text-slate-500">
            <div class="w-4 h-4 rounded-full border-2 border-slate-300 border-t-emerald-500 animate-spin"></div>
            <span class="text-sm">Loading map…</span>
          </div>
          <div v-else-if="error" class="h-[560px] flex flex-col items-center justify-center gap-2 text-slate-500 px-6 text-center">
            <p class="text-sm font-semibold text-slate-700">Couldn't load the map.</p>
            <p class="text-xs">{{ error }}</p>
          </div>
          <div v-show="!loading && !error" ref="mapEl" class="h-[560px] w-full"></div>
          <!-- Picture of whichever street was picked from the directory -->
          <div v-if="pictureStreet" class="px-5 py-4 border-t border-slate-100">
            <p class="text-xs font-semibold text-slate-700 mb-2">{{ pictureStreet.name }}</p>
            <StreetPicture :lat="pictureStreet.latitude" :lng="pictureStreet.longitude"
                           :google-enabled="googleReady" :height="240" :title="pictureStreet.name" />
          </div>
          <div v-if="false" class="flex items-center gap-5 px-5 py-3 border-t border-slate-100 text-xs">
            <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full" style="background:#059669"></span><span class="text-slate-600 font-medium">Named</span></span>
            <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full" style="background:#d97706"></span><span class="text-slate-600 font-medium">Unnamed</span></span>
            <span class="text-slate-400 italic ml-auto">Click a dot for details</span>
          </div>
        </div>

        <!-- Street directory — ADMIN ONLY -->
        <div v-if="isStaff" class="rounded-2xl bg-white border border-slate-200 flex flex-col" style="max-height:640px">
          <div class="p-4 border-b border-slate-100">
            <p class="text-sm font-bold text-slate-900 mb-2">Street registry ({{ filteredStreets.length }})</p>
            <input v-model="search" type="text" placeholder="Search a street name…"
                   class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
          </div>
          <div class="overflow-y-auto flex-1 p-2">
            <button v-for="s in filteredStreets" :key="s.code" @click="zoomToStreet(s.code)"
                    class="w-full text-left px-3 py-2 rounded-lg hover:bg-emerald-50 transition-colors group">
              <div class="flex items-center justify-between">
                <span class="text-sm text-slate-700 group-hover:text-emerald-700 truncate">{{ s.name }}</span>
                <span class="text-xs text-slate-400 font-medium ml-2 shrink-0">{{ s.building_count }}</span>
              </div>
              <div class="flex items-center gap-2 mt-0.5">
                <span class="text-[10px] text-slate-400 font-mono">{{ s.code }}</span>
                <span v-if="s.registration_status === 'registered'" class="text-[10px] font-semibold px-1.5 py-0.5 rounded" style="background:#dcfce7;color:#059669">Registered</span>
                <span v-if="s.name_variants > 1" class="text-[10px] text-slate-400">· {{ s.name_variants }} merged</span>
              </div>
            </button>
            <p v-if="filteredStreets.length === 0" class="text-sm text-slate-400 text-center py-6">No streets match "{{ search }}".</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { configApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import StreetPicture from '@/components/StreetPicture.vue'
import { ChevronDownIcon } from '@heroicons/vue/24/outline'

interface Survey {
  kobo_id: number; latitude: number; longitude: number
  existing_street_name: string; is_named: boolean
  street_code: string; street_name: string
  proposed_auto_number: string; locality: string
  photo_url?: string
}
interface Street {
  id: string; name: string; code: string; building_count: number
  name_variants: number; registration_status: string
  latitude?: number | string | null; longitude?: number | string | null
  locality?: string | null
}
interface Summary {
  total_buildings: number; named_streets: number
  unnamed_streets: number; renaming_in_progress: number
}

const auth = useAuthStore()
const isStaff = computed(() => auth.isStaff)

const surveys = ref<Survey[]>([])
const streets = ref<Street[]>([])
const summary = ref<Summary | null>(null)
const loading = ref(true)
const error = ref('')
const search = ref('')
const selectedLocality = ref('')
const localities = computed(() => {
  const set = new Set<string>()
  for (const s of streets.value) { const l = (s.locality || '').trim(); if (l) set.add(l) }
  return Array.from(set).sort((a, b) => a.localeCompare(b))
})
function zoomToLocalitySel() {
  if (!map) return
  const loc = selectedLocality.value.trim().toLowerCase()
  if (!loc) { fitToLGA(); refreshStreetLabels(); return }
  const pts: L.LatLngTuple[] = []
  for (const s of streets.value) {
    if ((s.locality || '').trim().toLowerCase() !== loc) continue
    if (s.latitude != null && s.longitude != null) pts.push([Number(s.latitude), Number(s.longitude)])
  }
  if (pts.length) {
    map.setMinZoom(0)
    map.fitBounds(L.latLngBounds(pts).pad(0.3), { maxZoom: 16 })
  }
}
const mapEl = ref<HTMLElement | null>(null)
const pictureStreet = ref<{ name: string; latitude: number; longitude: number } | null>(null)
const googleReady = ref(false)
configApi.publicSettings().then(r => { googleReady.value = !!r.data.google_maps_enabled }).catch(() => {})
let map: L.Map | null = null
const markers = new Map<number, L.CircleMarker>()

const NAMED = '#059669'
const UNNAMED = '#d97706'

function inBounds(lat: number, lng: number) {
  return lat >= 6.2 && lat <= 6.85 && lng >= 3.4 && lng <= 4.5
}

const filteredStreets = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return streets.value
  return streets.value.filter(s => s.name.toLowerCase().includes(q) || s.code.toLowerCase().includes(q))
})

function popupHtml(s: Survey): string {
  const name = s.is_named ? (s.street_name || s.existing_street_name) : 'Unnamed street'
  const number = s.proposed_auto_number ? `No. ${s.proposed_auto_number}` : ''
  const photo = s.photo_url
    ? `<img src="${s.photo_url}" alt="street" style="width:180px;height:110px;object-fit:cover;border-radius:6px;margin-bottom:6px" onerror="this.style.display='none'"/><br/>`
    : ''
  return `<div style="font-size:12px;line-height:1.4">${photo}<strong>${name}</strong><br/>${s.street_code ? '<span style="color:#059669;font-family:monospace">' + s.street_code + '</span><br/>' : ''}${number ? number + '<br/>' : ''}<span style="color:#64748b">${s.locality || 'Ibeju-Lekki'}</span></div>`
}

// Ibeju-Lekki LGA administrative extent — the map is always locked to this.
let labelLayer: L.LayerGroup | null = null
const LGA_BOUNDS = L.latLngBounds([[6.385, 3.63], [6.520, 4.10]])

function fitToLGA() {
  if (!map) return
  map.fitBounds(LGA_BOUNDS)
  map.setMaxBounds(LGA_BOUNDS.pad(0.15))
  map.setMinZoom(map.getZoom())
}

function zoomToStreet(code: string) {
  const st = streets.value.find(s => s.code === code) as unknown as
    { name: string; latitude?: number | null; longitude?: number | null } | undefined
  // Offer a picture of the picked street. Half the registry is digitised from the
  // old register and carries no coordinates, so there is nothing to show for those.
  pictureStreet.value = (st && st.latitude != null && st.longitude != null)
    ? { name: st.name, latitude: Number(st.latitude), longitude: Number(st.longitude) }
    : null
  if (!map || !pictureStreet.value) return
  map.setView([pictureStreet.value.latitude, pictureStreet.value.longitude], 17)
}

onMounted(async () => {
  try {
    const streetRes = await configApi.getStreets()
    streets.value = streetRes.data as Street[]
    if (isStaff.value) {
      const summaryRes = await configApi.getStreetSummary()
      summary.value = summaryRes.data as Summary
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Request failed'
    loading.value = false
    return
  }
  loading.value = false
  await nextTick()
  if (!mapEl.value) return
  map = L.map(mapEl.value, { preferCanvas: true, scrollWheelZoom: true })
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors', maxZoom: 19,
  }).addTo(map)
  fitToLGA()
  labelLayer = L.layerGroup().addTo(map)
  map.on('zoomend moveend', refreshStreetLabels)
  refreshStreetLabels()
})

function refreshStreetLabels() {
  if (!map || !labelLayer) return
  labelLayer.clearLayers()
  // Only show labels at street level to avoid clutter at the LGA-wide view.
  if (map.getZoom() < 15) return
  const bounds = map.getBounds()
  for (const st of streets.value) {
    const lat = st.latitude != null ? Number(st.latitude) : null
    const lng = st.longitude != null ? Number(st.longitude) : null
    if (lat == null || lng == null || Number.isNaN(lat) || Number.isNaN(lng) || !st.name) continue
    if (!bounds.contains([lat, lng])) continue
    L.marker([lat, lng], {
      icon: L.divIcon({
        className: 'street-label',
        html: `<span>${st.name.replace(/</g, '&lt;')}</span>`,
        iconSize: [0, 0],
      }),
      interactive: false, keyboard: false,
    }).addTo(labelLayer)
  }
}

onUnmounted(() => { map?.remove(); map = null })
</script>

<style>
.street-label span {
  display: inline-block;
  transform: translate(-50%, -50%);
  white-space: nowrap;
  font-size: 11px;
  font-weight: 700;
  color: #0f172a;
  text-shadow: 0 0 3px #fff, 0 0 3px #fff, 0 0 3px #fff, 0 0 3px #fff;
  pointer-events: none;
}
</style>
