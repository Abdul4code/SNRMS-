<template>
  <div class="min-h-screen" style="background: #f1f5f9">
    <div style="background: #0f172a">
      <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Registry Management</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">Manage Streets</h1>
        <p class="text-slate-400 text-sm mt-1">Merge duplicates, rename, or split streets to perfect the registry.</p>
      </div>
    </div>

    <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-4">
      <div v-if="notice" class="rounded-xl px-4 py-3 text-sm" :style="noticeStyle">{{ notice }}</div>

      <!-- Toolbar -->
      <div class="flex flex-wrap items-center gap-3">
        <input v-model="search" @input="onSearch" type="text" placeholder="Search streets…"
               class="flex-1 min-w-[200px] rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" />
        <button v-if="selected.size >= 2" @click="openMerge"
                class="rounded-xl px-4 py-2.5 text-sm font-semibold text-white" style="background:#059669">
          Merge {{ selected.size }} streets
        </button>
        <span v-if="selected.size >= 1" class="text-xs text-slate-500">{{ selected.size }} selected</span>
      </div>

      <!-- Merge panel -->
      <div v-if="mergeOpen" class="rounded-2xl bg-white border border-emerald-200 p-4 space-y-3">
        <p class="text-sm font-bold text-slate-900">Merge into which street?</p>
        <p class="text-xs text-slate-500">All buildings from the others move into the one you choose; the rest are deleted.</p>
        <div class="space-y-1.5">
          <label v-for="s in selectedStreets" :key="s.id" class="flex items-center gap-2 text-sm">
            <input type="radio" name="mergeTarget" :value="s.id" v-model="mergeTarget" class="accent-emerald-600" />
            <span class="font-medium text-slate-800">{{ s.name }}</span>
            <span class="text-xs text-slate-400">{{ s.code }} · {{ s.building_count }} bldgs</span>
          </label>
        </div>
        <div class="flex gap-2 pt-1">
          <button @click="doMerge" :disabled="!mergeTarget || busy"
                  class="rounded-lg px-3.5 py-2 text-sm font-semibold text-white disabled:opacity-60" style="background:#059669">
            {{ busy ? 'Merging…' : 'Confirm merge' }}
          </button>
          <button @click="mergeOpen = false" class="rounded-lg px-3.5 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100">Cancel</button>
        </div>
      </div>

      <!-- Split panel -->
      <div v-if="splitStreetObj" class="rounded-2xl bg-white border border-amber-200 p-4 space-y-3">
        <p class="text-sm font-bold text-slate-900">Split "{{ splitStreetObj.name }}"</p>
        <p class="text-xs text-slate-500">Tick the buildings that belong to a different street, name it, and create it.</p>
        <input v-model="splitName" type="text" placeholder="New street name (e.g. Owolabi Close)"
               class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500" />
        <div class="max-h-52 overflow-y-auto border border-slate-100 rounded-xl divide-y divide-slate-50">
          <label v-for="b in splitBuildings" :key="b.kobo_id" class="flex items-center gap-2 px-3 py-1.5 text-sm hover:bg-slate-50">
            <input type="checkbox" :value="b.kobo_id" v-model="splitPicked" class="accent-amber-600" />
            <span class="text-slate-700">{{ b.proposed_auto_number || '—' }}</span>
            <span class="text-xs text-slate-400">{{ b.locality }}</span>
          </label>
          <p v-if="splitBuildings.length === 0" class="text-xs text-slate-400 px-3 py-3">Loading buildings…</p>
        </div>
        <div class="flex gap-2">
          <button @click="doSplit" :disabled="!splitName || splitPicked.length === 0 || busy"
                  class="rounded-lg px-3.5 py-2 text-sm font-semibold text-white disabled:opacity-60" style="background:#d97706">
            {{ busy ? 'Splitting…' : `Move ${splitPicked.length} to new street` }}
          </button>
          <button @click="splitStreetObj = null" class="rounded-lg px-3.5 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100">Cancel</button>
        </div>
      </div>

      <!-- Street list -->
      <div class="rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div v-for="s in streets" :key="s.id" class="flex items-center gap-3 px-4 py-2.5 border-b border-slate-50 last:border-0 hover:bg-slate-50">
          <input type="checkbox" :checked="selected.has(s.id)" @change="toggle(s.id)" class="accent-emerald-600" />
          <div class="flex-1 min-w-0">
            <div v-if="editingId === s.id" class="flex items-center gap-2">
              <input v-model="editName" type="text" class="rounded-lg border border-slate-200 px-2 py-1 text-sm w-56" />
              <button @click="doRename(s)" class="text-xs font-semibold text-emerald-700">Save</button>
              <button @click="editingId = ''" class="text-xs text-slate-400">Cancel</button>
            </div>
            <div v-else class="truncate">
              <span class="text-sm font-medium text-slate-800">{{ s.name }}</span>
              <span v-if="s.registration_status === 'registered'" class="ml-2 text-[10px] font-semibold px-1.5 py-0.5 rounded" style="background:#dcfce7;color:#059669">Registered</span>
            </div>
            <p class="text-[11px] text-slate-400 font-mono">{{ s.code }} · {{ s.building_count }} bldgs<span v-if="s.name_variants > 1"> · {{ s.name_variants }} merged</span></p>
          </div>
          <button @click="startRename(s)" class="text-xs text-slate-500 hover:text-emerald-700 px-2 py-1">Rename</button>
          <button @click="startSplit(s)" class="text-xs text-slate-500 hover:text-amber-700 px-2 py-1">Split</button>
        </div>
        <p v-if="streets.length === 0 && !loading" class="text-sm text-slate-400 text-center py-8">No streets found.</p>
        <p v-if="loading" class="text-sm text-slate-400 text-center py-8">Loading…</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { configApi } from '@/services/api'

interface Street {
  id: string; name: string; code: string; building_count: number
  name_variants: number; registration_status: string
}
interface Bldg { kobo_id: number; proposed_auto_number: string; locality: string }

const streets = ref<Street[]>([])
const loading = ref(true)
const busy = ref(false)
const search = ref('')
const selected = ref<Set<string>>(new Set())
const notice = ref('')
const noticeOk = ref(true)

const editingId = ref('')
const editName = ref('')
const mergeOpen = ref(false)
const mergeTarget = ref('')
const splitStreetObj = ref<Street | null>(null)
const splitBuildings = ref<Bldg[]>([])
const splitPicked = ref<number[]>([])
const splitName = ref('')

const noticeStyle = computed(() =>
  noticeOk.value ? 'background:#dcfce7;color:#059669' : 'background:#fee2e2;color:#b91c1c')
const selectedStreets = computed(() => streets.value.filter(s => selected.value.has(s.id)))

let searchTimer: ReturnType<typeof setTimeout>
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 300)
}

async function load() {
  loading.value = true
  try {
    const { data } = await configApi.getStreets(search.value ? { search: search.value } : {})
    streets.value = data as Street[]
  } finally {
    loading.value = false
  }
}

function flash(msg: string, ok = true) {
  notice.value = msg; noticeOk.value = ok
  setTimeout(() => { notice.value = '' }, 4000)
}

function toggle(id: string) {
  const s = new Set(selected.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selected.value = s
}

function openMerge() {
  mergeTarget.value = selectedStreets.value[0]?.id ?? ''
  mergeOpen.value = true
}
async function doMerge() {
  busy.value = true
  try {
    const sources = [...selected.value].filter(id => id !== mergeTarget.value)
    await configApi.mergeStreets(mergeTarget.value, sources)
    flash(`Merged ${sources.length} street(s).`)
    selected.value = new Set(); mergeOpen.value = false
    await load()
  } catch { flash('Merge failed.', false) } finally { busy.value = false }
}

function startRename(s: Street) { editingId.value = s.id; editName.value = s.name }
async function doRename(s: Street) {
  busy.value = true
  try {
    await configApi.updateStreet(s.id, { name: editName.value })
    editingId.value = ''
    flash('Renamed.')
    await load()
  } catch { flash('Rename failed.', false) } finally { busy.value = false }
}

async function startSplit(s: Street) {
  splitStreetObj.value = s; splitPicked.value = []; splitName.value = ''; splitBuildings.value = []
  const { data } = await configApi.getStreetBuildings(s.id)
  splitBuildings.value = data as Bldg[]
}
async function doSplit() {
  if (!splitStreetObj.value) return
  busy.value = true
  try {
    await configApi.splitStreet(splitStreetObj.value.id, splitName.value, splitPicked.value)
    flash(`Moved ${splitPicked.value.length} building(s) to "${splitName.value}".`)
    splitStreetObj.value = null
    await load()
  } catch { flash('Split failed.', false) } finally { busy.value = false }
}

onMounted(load)
</script>
