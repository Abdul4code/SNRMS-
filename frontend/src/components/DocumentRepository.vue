<template>
  <div class="rounded-2xl overflow-hidden" style="background:#fff;border:1px solid #e2e8f0">
    <div class="px-5 py-4 flex items-center justify-between" style="border-bottom:1px solid #f1f5f9">
      <div class="flex items-center gap-2.5">
        <div class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style="background:rgba(5,150,105,0.08);border:1px solid rgba(5,150,105,0.15)">
          <svg class="w-4 h-4" style="color:#059669" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10a2 2 0 002 2h12a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H6a2 2 0 00-2 2z"/></svg>
        </div>
        <div>
          <h2 class="text-sm font-bold text-slate-900">Document Repository</h2>
          <p class="text-[11px] text-slate-400" v-if="applicantName">All records for {{ applicantName }}</p>
        </div>
      </div>
      <button @click="load" class="text-xs text-slate-500 hover:text-slate-700">Refresh</button>
    </div>
    <div class="p-4">
      <p v-if="loading" class="text-xs text-slate-400 py-4 text-center">Loading records…</p>
      <p v-else-if="!items.length" class="text-xs text-slate-400 py-4 text-center">No documents on file yet.</p>
      <div v-else class="space-y-4">
        <div v-for="(group, cat) in grouped" :key="cat">
          <p class="text-[11px] font-bold uppercase tracking-wide text-slate-400 mb-1.5">{{ cat }}</p>
          <ul class="space-y-1.5">
            <li v-for="(it, i) in group" :key="cat + i"
                class="flex items-center justify-between gap-3 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2">
              <div class="min-w-0">
                <p class="text-sm text-slate-800 font-medium truncate">{{ it.title }}</p>
                <p class="text-[11px] text-slate-400">
                  {{ formatDate(it.date) }}<span v-if="it.amount"> · ₦{{ formatAmount(it.amount) }}</span>
                  <span v-if="it.verified" class="text-emerald-600 ml-1">✓ verified</span>
                </p>
              </div>
              <div class="flex items-center gap-2 flex-shrink-0">
                <a v-if="it.download_url" :href="it.download_url" target="_blank" rel="noopener"
                   class="inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-semibold border border-slate-200 text-slate-600 hover:bg-slate-100">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                  View
                </a>
                <a v-if="it.download_url" :href="it.download_url" target="_blank" rel="noopener" download
                   class="inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-semibold text-white" style="background:#059669">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                  Download
                </a>
                <span v-if="!it.download_url" class="text-[11px] text-slate-400">Not available</span>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { applicationApi } from '@/services/api'

interface RepoItem {
  category: string; title: string; kind: string; filename?: string
  download_url: string | null; date?: string; amount?: number; serial?: string; verified?: boolean
}

const props = defineProps<{ applicationId: string | number }>()
const items = ref<RepoItem[]>([])
const applicantName = ref('')
const loading = ref(false)

const grouped = computed(() => {
  const order = ['Submitted by applicant', 'Issued by Council', 'Receipt', 'Certificate']
  const g: Record<string, RepoItem[]> = {}
  for (const it of items.value) { (g[it.category] ||= []).push(it) }
  const out: Record<string, RepoItem[]> = {}
  for (const k of order) if (g[k]) out[k] = g[k] as RepoItem[]
  for (const k of Object.keys(g)) if (!out[k]) out[k] = g[k] as RepoItem[]
  return out
})

async function load() {
  if (!props.applicationId) return
  loading.value = true
  try {
    const { data } = await applicationApi.repository(props.applicationId)
    items.value = data.items || []
    applicantName.value = data.applicant?.name || ''
  } catch { items.value = [] }
  finally { loading.value = false }
}

function formatDate(d?: string) {
  if (!d) return ''
  try { return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) } catch { return '' }
}
function formatAmount(n?: number) { return (n || 0).toLocaleString('en-NG') }

onMounted(load)
watch(() => props.applicationId, load)
</script>
