<template>
  <div class="min-h-screen" style="background:#f1f5f9">
    <div style="background:#0f172a">
      <div class="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Council Treasurer</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">Official Signature</h1>
        <p class="text-slate-400 text-sm mt-1">Upload your e-signature once — it is applied to every generated receipt.</p>
      </div>
    </div>

    <div class="max-w-2xl mx-auto px-4 sm:px-6 py-8">
      <div class="rounded-2xl bg-white border border-slate-200 p-6">
        <div v-if="current.uploaded" class="mb-5 rounded-xl p-3 flex items-center gap-3" style="background:rgba(5,150,105,0.06)">
          <span class="text-emerald-600 text-lg">✓</span>
          <div>
            <p class="text-sm font-semibold text-slate-800">A signature is on file</p>
            <p class="text-xs text-slate-500">{{ current.signatory_name }} · uploaded {{ formatDate(current.uploaded_at) }}. Uploading again replaces it.</p>
          </div>
        </div>

        <label class="block text-sm font-semibold text-slate-700 mb-1.5">Signatory name</label>
        <input v-model="name" class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm mb-4" placeholder="e.g. Hon. Adewale Johnson" />

        <label class="block text-sm font-semibold text-slate-700 mb-1.5">Title</label>
        <input v-model="title" class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm mb-4" placeholder="Council Treasurer, Ibeju-Lekki Local Government Area" />

        <label class="block text-sm font-semibold text-slate-700 mb-1.5">Signature image (PNG with transparent background works best)</label>
        <input type="file" accept="image/png,image/jpeg" @change="onFile" class="block w-full text-sm mb-2" />
        <div v-if="preview" class="mb-4 p-3 rounded-xl border border-slate-100 bg-slate-50 inline-block">
          <img :src="preview" alt="signature preview" style="max-height:70px" />
        </div>

        <p v-if="msg" class="text-sm mb-3" :class="msgOk ? 'text-emerald-600' : 'text-red-500'">{{ msg }}</p>
        <button @click="save" :disabled="!file || busy"
                class="rounded-xl px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-60" style="background:#059669">
          {{ busy ? 'Uploading…' : 'Save signature' }}
        </button>

        <p class="mt-5 text-xs text-slate-400 leading-relaxed">
          Your signature is stored securely on the server and is only ever embedded into verified receipts —
          it is never shared as a separate file, so it cannot be copied to forge a receipt. Each receipt also
          carries a unique serial, a security code, and a QR code that anyone can scan to confirm authenticity.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { receiptApi } from '@/services/api'

const current = ref<{ uploaded: boolean; signatory_name?: string; uploaded_at?: string }>({ uploaded: false })
const name = ref('')
const title = ref('Council Treasurer, Ibeju-Lekki Local Government Area')
const file = ref<File | null>(null)
const preview = ref('')
const busy = ref(false)
const msg = ref('')
const msgOk = ref(false)

function formatDate(d?: string) { return d ? new Date(d).toLocaleDateString() : '' }
function onFile(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0] || null
  file.value = f
  preview.value = f ? URL.createObjectURL(f) : ''
}
async function save() {
  if (!file.value) return
  busy.value = true; msg.value = ''
  try {
    const fd = new FormData()
    fd.append('image', file.value)
    if (name.value) fd.append('signatory_name', name.value)
    if (title.value) fd.append('signatory_title', title.value)
    await receiptApi.uploadSignature(fd)
    msgOk.value = true; msg.value = 'Signature saved. It will appear on all receipts from now on.'
    await load()
  } catch {
    msgOk.value = false; msg.value = 'Upload failed. Please try again.'
  } finally { busy.value = false }
}
async function load() {
  try {
    const { data } = await receiptApi.getSignature()
    current.value = data
    if (data.signatory_name) name.value = data.signatory_name
  } catch { /* ignore */ }
}
onMounted(load)
</script>
