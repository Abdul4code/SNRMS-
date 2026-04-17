<template>
  <div>
    <!-- Compact map with expand button overlay -->
    <div v-if="coords" class="relative">
      <div ref="mapEl" class="w-full rounded-xl overflow-hidden" style="height: 300px; z-index: 0;"></div>
      <button
        class="absolute top-2 right-2 z-[400] flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold shadow-md transition-all hover:scale-105 active:scale-95"
        style="background: rgba(255,255,255,0.92); color: #0f172a; border: 1px solid rgba(0,0,0,0.1); backdrop-filter: blur(4px)"
        @click="openModal"
      >
        <ArrowsPointingOutIcon class="w-3.5 h-3.5" />
        Expand
      </button>
    </div>
    <div v-else class="flex flex-col items-center py-10 gap-2">
      <MapPinIcon class="w-8 h-8 text-slate-300" />
      <p class="text-sm text-slate-500">No location data available for this application.</p>
    </div>

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
              class="relative w-full max-w-5xl rounded-2xl overflow-hidden flex flex-col"
              style="height: 82vh; background: #fff; box-shadow: 0 25px 60px rgba(0,0,0,0.4)"
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
                  <p class="text-xs text-slate-400 font-mono">{{ coords?.[0].toFixed(6) }}, {{ coords?.[1].toFixed(6) }}</p>
                </div>
                <button
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-600 border border-slate-200 hover:bg-slate-50 transition-colors"
                  @click="closeModal"
                >
                  <ArrowsPointingInIcon class="w-3.5 h-3.5" />
                  Close
                </button>
              </div>
              <!-- Modal map fills remaining height -->
              <div ref="modalMapEl" class="flex-1 w-full"></div>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { MapPinIcon, ArrowsPointingOutIcon, ArrowsPointingInIcon } from '@heroicons/vue/24/outline'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

// Fix Leaflet's default icon path resolution with Vite bundler
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({ iconUrl: markerIcon, iconRetinaUrl: markerIcon2x, shadowUrl: markerShadow })

const props = defineProps<{ locationDescription?: string; streetName?: string }>()

const mapEl = ref<HTMLElement | null>(null)
const modalMapEl = ref<HTMLElement | null>(null)
const showModal = ref(false)

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

function buildPopup(isModal = false): string {
  if (!coords.value) return ''
  const name = props.streetName ? `<strong>${props.streetName}</strong><br/>` : ''
  const coordStr = `<small>${coords.value[0].toFixed(6)}, ${coords.value[1].toFixed(6)}</small>`
  return isModal ? `${name}${coordStr}` : coordStr
}

function initMap(el: HTMLElement, zoom: number, scrollWheel: boolean): L.Map {
  const m = L.map(el, { scrollWheelZoom: scrollWheel }).setView(coords.value!, zoom)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(m)
  L.marker(coords.value!).addTo(m).bindPopup(buildPopup(scrollWheel)).openPopup()
  return m
}

onMounted(() => {
  if (!coords.value || !mapEl.value) return
  map = initMap(mapEl.value, 16, false)
})

async function openModal() {
  showModal.value = true
  // Wait for Teleport + Transition to render the modal DOM
  await nextTick()
  await nextTick()
  if (coords.value && modalMapEl.value && !modalMap) {
    modalMap = initMap(modalMapEl.value, 17, true)
  }
  // Prevent body scroll while modal is open
  document.body.style.overflow = 'hidden'
}

function closeModal() {
  showModal.value = false
  document.body.style.overflow = ''
  // Destroy modal map so it re-initialises cleanly if reopened
  modalMap?.remove()
  modalMap = null
}

// Keyboard ESC to close
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
