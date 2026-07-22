<template>
  <div class="min-h-screen" style="background: #f1f5f9">
    <div style="background: #0f172a">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Street Registry</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">Ibeju-Lekki Street Map</h1>
        <p class="text-slate-400 text-sm mt-1">Surveyed buildings across the LGA — named in green, unnamed in amber.</p>
      </div>
    </div>

    <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <!-- Registry metrics — ADMIN ONLY -->
      <div v-if="isStaff && summary" class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="rounded-2xl p-5 bg-white border border-slate-200">
          <p class="text-3xl font-bold tracking-tight text-slate-900">{{ summary.total_buildings.toLocaleString() }}</p>
          <p class="text-xs text-slate-500 mt-1 font-semibold uppercase tracking-wide">Buildings</p>
        </div>
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
          <div v-if="!loading && !error" class="flex items-center gap-5 px-5 py-3 border-t border-slate-100 text-xs">
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

interface Survey {
  kobo_id: number; latitude: number; longitude: number
  existing_street_name: string; is_named: boolean
  street_code: string; street_name: string
  proposed_auto_number: string; locality: string
}
interface Street {
  id: string; name: string; code: string; building_count: number
  name_variants: number; registration_status: string
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
const mapEl = ref<HTMLElement | null>(null)
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
  return `<div style="font-size:12px;line-height:1.4"><strong>${name}</strong><br/>${s.street_code ? '<span style="color:#059669;font-family:monospace">' + s.street_code + '</span><br/>' : ''}${number ? number + '<br/>' : ''}<span style="color:#64748b">${s.locality || 'Ibeju-Lekki'}</span></div>`
}

function drawMarkers() {
  if (!map) return
  const canvas = L.canvas({ padding: 0.5 })
  const pts: L.LatLngExpression[] = []
  for (const s of surveys.value) {
    const marker = L.circleMarker([s.latitude, s.longitude], {
      renderer: canvas, radius: 4,
      color: s.is_named ? NAMED : UNNAMED, fillColor: s.is_named ? NAMED : UNNAMED,
      fillOpacity: 0.7, weight: 1,
    }).bindPopup(popupHtml(s))
    marker.addTo(map)
    markers.set(s.kobo_id, marker)
    pts.push([s.latitude, s.longitude])
  }
  if (pts.length) map.fitBounds(L.latLngBounds(pts as L.LatLngTuple[]).pad(0.05))
}

function zoomToStreet(code: string) {
  if (!map) return
  const members = surveys.value.filter(s => s.street_code === code)
  const pts = members.map(s => [s.latitude, s.longitude] as L.LatLngTuple)
  if (!pts.length) return
  map.fitBounds(L.latLngBounds(pts).pad(0.3), { maxZoom: 17 })
  if (members[0]) markers.get(members[0].kobo_id)?.openPopup()
}

onMounted(async () => {
  try {
    const surveyRes = await configApi.getBuildingSurveys()
    surveys.value = (surveyRes.data as Survey[]).filter(s => s.latitude != null && s.longitude != null && inBounds(Number(s.latitude), Number(s.longitude)))
    if (isStaff.value) {
      const [streetRes, summaryRes] = await Promise.all([configApi.getStreets(), configApi.getStreetSummary()])
      streets.value = streetRes.data as Street[]
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
  map.setView([6.465, 3.665], 12)
  drawMarkers()
})

onUnmounted(() => { map?.remove(); map = null })
</script>
