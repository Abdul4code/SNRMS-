<template>
  <div v-if="hasCoords">
    <button v-if="!shown" type="button" @click="reveal"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white"
            style="background:#0f172a">
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
      Show street's picture
    </button>

    <div v-else>
      <!-- Google Street View still photo — only when a server key is configured. -->
      <img v-if="stillSrc" :src="stillSrc" alt="Street view at this location"
           class="w-full rounded-lg border border-slate-200 mb-2"
           :style="{ maxHeight: height + 'px', objectFit: 'cover' }"
           @error="stillSrc = ''" />
      <!-- Satellite/aerial view — Esri tiles, no API key needed, so this always works. -->
      <div ref="mapEl" class="w-full rounded-lg border border-slate-200 overflow-hidden"
           :style="{ height: height + 'px' }"></div>
      <p class="text-[10px] text-slate-400 mt-0.5">
        {{ stillSrc ? 'Google Street View plus a satellite view of the exact spot.'
                    : 'Satellite/aerial view of the exact spot.' }}
      </p>
      <div class="flex items-center gap-3 mt-1.5 flex-wrap">
        <button type="button" @click="viewerOpen = true"
                class="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-700 hover:text-blue-800">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
          Open in Google Street View
        </button>
        <a :href="`https://www.google.com/maps/search/?api=1&query=${lat},${lng}`"
           target="_blank" rel="noopener"
           class="text-[11px] font-semibold text-slate-500 hover:text-slate-700">Open in Google Maps ↗</a>
        <button type="button" @click="hide" class="text-[11px] text-slate-400 underline ml-auto">Hide picture</button>
      </div>

      <!-- Interactive Street View, inline in a modal — no page redirect. -->
      <Teleport to="body">
        <div v-if="viewerOpen" class="fixed inset-0 z-[9999] flex items-center justify-center p-4"
             style="background:rgba(15,23,42,0.72)" @click.self="viewerOpen = false">
          <div class="bg-white rounded-2xl overflow-hidden w-full max-w-3xl flex flex-col"
               style="box-shadow:0 20px 60px rgba(0,0,0,0.35); max-height:90vh">
            <div class="flex items-center justify-between px-4 py-3 flex-shrink-0" style="border-bottom:1px solid #f1f5f9">
              <div>
                <p class="text-sm font-bold text-slate-900">{{ title || 'Street View' }}</p>
                <p class="text-[11px] font-mono text-slate-400">{{ lat }}, {{ lng }}</p>
              </div>
              <button type="button" @click="viewerOpen = false" class="text-slate-400 hover:text-slate-600 p-1">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            </div>
            <iframe v-if="embedUrl" :src="embedUrl" class="w-full" style="height:60vh; border:0"
                    loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"></iframe>
            <div class="px-4 py-2 flex-shrink-0 text-right" style="border-top:1px solid #f1f5f9">
              <a :href="`https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lng}`"
                 target="_blank" rel="noopener" class="text-[11px] text-blue-600 hover:underline">Open full screen in Google Maps ↗</a>
            </div>
          </div>
        </div>
      </Teleport>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * "Show street's picture" for any point on any map, applicant or staff side.
 *
 * Three ways of seeing a place, in order of what is actually available:
 *   1. Satellite/aerial tiles (Esri) — needs no API key, so this always renders.
 *   2. A Google Street View still — only when the server has a Maps key; the
 *      proxy 404s without one, and the <img> error handler drops it silently.
 *   3. Interactive Street View in a modal — uses Google's Embed API with a key,
 *      and falls back to the keyless embed, so it works with no key at all.
 *
 * (3) is the reason this is a shared component: the staff pages used to offer
 * only (2), which shows nothing on a deployment without a key.
 */
import { computed, nextTick, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { configApi } from '@/services/api'

const props = withDefaults(defineProps<{
  lat?: number | string | null
  lng?: number | string | null
  /** Server has a Google Maps key — pass through from config/public-settings. */
  googleEnabled?: boolean
  /** Height of the satellite panel and the still, in pixels. */
  height?: number
  /** Shown as the modal heading, e.g. the street name. */
  title?: string
}>(), { googleEnabled: false, height: 240, title: '' })

const GMAPS_EMBED_KEY = import.meta.env.VITE_GOOGLE_MAPS_KEY || ''

const shown = ref(false)
const viewerOpen = ref(false)
const stillSrc = ref('')
const mapEl = ref<HTMLElement | null>(null)
let picMap: L.Map | null = null

const lat = computed(() => Number(props.lat))
const lng = computed(() => Number(props.lng))
const hasCoords = computed(() => Number.isFinite(lat.value) && Number.isFinite(lng.value))

const embedUrl = computed(() => {
  if (!hasCoords.value) return ''
  return GMAPS_EMBED_KEY
    ? `https://www.google.com/maps/embed/v1/streetview?key=${GMAPS_EMBED_KEY}&location=${lat.value},${lng.value}&fov=80`
    : `https://maps.google.com/maps?q=&layer=c&cbll=${lat.value},${lng.value}&cbp=11,0,0,0,0&output=svembed`
})

async function reveal() {
  if (!hasCoords.value) return
  if (props.googleEnabled) stillSrc.value = configApi.streetViewUrl(lat.value, lng.value)
  shown.value = true
  await nextTick()
  if (picMap) { picMap.remove(); picMap = null }
  if (!mapEl.value) return
  picMap = L.map(mapEl.value, { attributionControl: false, scrollWheelZoom: false })
  // Esri World Imagery — free satellite/aerial tiles, no API key required.
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { maxZoom: 19 }).addTo(picMap)
  picMap.setView([lat.value, lng.value], 18)
  L.circleMarker([lat.value, lng.value],
    { radius: 8, color: '#f59e0b', weight: 3, fillColor: '#f59e0b', fillOpacity: 0.5 }).addTo(picMap)
  setTimeout(() => picMap?.invalidateSize(), 120)
}

function hide() {
  if (picMap) { picMap.remove(); picMap = null }
  shown.value = false
  viewerOpen.value = false
  stillSrc.value = ''
}

// Moving to a different place closes the old picture rather than leaving a
// satellite view of somewhere else on screen.
watch(() => [props.lat, props.lng], () => { if (shown.value) hide() })

defineExpose({ hide })
</script>
