<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <!-- Page header band -->
    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-3xl mx-auto px-4 sm:px-6 py-7">
        <nav class="flex items-center gap-2 text-xs text-slate-400 mb-4">
          <RouterLink to="/applications" class="hover:text-emerald-400 transition-colors">My Applications</RouterLink>
          <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
          <RouterLink :to="`/applications/${route.params.id}`" class="hover:text-emerald-400 transition-colors font-mono">
            APP-{{ route.params.id }}
          </RouterLink>
          <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
          <span class="text-slate-300">Documents</span>
        </nav>
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Documents</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">Required Documents</h1>
        <p class="text-slate-400 text-sm mt-1">Upload all required documents to proceed with your application</p>
      </div>
    </div>

    <div class="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-5">

      <!-- Progress summary -->
      <div class="rounded-2xl px-6 py-5" style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.06)">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold text-slate-500">{{ uploadedCount }} of {{ REQUIRED_DOCS.length }} documents uploaded</span>
          <span v-if="uploadedCount === REQUIRED_DOCS.length" class="text-xs font-bold text-emerald-600">All documents uploaded</span>
          <span v-else class="text-xs font-semibold text-amber-500">{{ REQUIRED_DOCS.length - uploadedCount }} remaining</span>
        </div>
        <div class="w-full h-1.5 rounded-full bg-slate-100 overflow-hidden">
          <div class="h-full rounded-full transition-all duration-500"
               style="background: linear-gradient(90deg, #059669, #34d399)"
               :style="{ width: `${(uploadedCount / REQUIRED_DOCS.length) * 100}%` }"></div>
        </div>
      </div>

      <!-- Global error / success -->
      <transition enter-active-class="transition duration-200 ease-out"
                  enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
        <div v-if="globalError" class="flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 p-4">
          <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
          </svg>
          <p class="text-sm text-red-700">{{ globalError }}</p>
        </div>
      </transition>

      <!-- Required documents checklist -->
      <div class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0">
        <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
          <h2 class="text-sm font-bold text-slate-900">Required Documents</h2>
          <p class="text-xs text-slate-500 mt-0.5">Accepted formats: PDF, JPEG, PNG, DOC, DOCX</p>
        </div>

        <div v-if="loadingDocs" class="flex items-center justify-center py-12">
          <div class="w-7 h-7 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
        </div>

        <ul v-else class="divide-y divide-slate-50">
          <li v-for="req in REQUIRED_DOCS" :key="req.type" class="px-5 py-4">
            <div class="flex items-start gap-4">

              <!-- Status icon -->
              <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5"
                   :style="uploadedFor(req.type)
                     ? 'background: rgba(5,150,105,0.08); border: 1px solid rgba(5,150,105,0.18)'
                     : rejectedFor(req.type) && !uploadedFor(req.type)
                       ? 'background: rgba(220,38,38,0.06); border: 1px solid rgba(220,38,38,0.18)'
                       : 'background: #f8fafc; border: 1px solid #e2e8f0'">
                <CheckCircleIcon v-if="uploadedFor(req.type)" class="w-5 h-5" style="color: #059669" />
                <svg v-else-if="rejectedFor(req.type) && !uploadedFor(req.type)" class="w-5 h-5" style="color: #dc2626" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
                <DocumentArrowUpIcon v-else class="w-5 h-5 text-slate-400" />
              </div>

              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <p class="text-sm font-semibold text-slate-900">{{ req.label }}</p>
                  <span v-if="uploadedFor(req.type)"
                        class="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full"
                        style="background: rgba(5,150,105,0.1); color: #047857">
                    Uploaded
                  </span>
                  <span v-else-if="rejectedFor(req.type) && !uploadedFor(req.type)"
                        class="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full"
                        style="background: rgba(220,38,38,0.08); color: #b91c1c">
                    Rejected — Re-upload Required
                  </span>
                  <span v-else
                        class="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full"
                        style="background: rgba(245,158,11,0.1); color: #b45309">
                    Required
                  </span>
                </div>

                <!-- Rejected notice — hidden once a replacement has been uploaded -->
                <div v-if="rejectedFor(req.type) && !uploadedFor(req.type)" class="mt-2 rounded-xl px-3 py-2.5"
                     style="background: rgba(220,38,38,0.04); border: 1px solid rgba(220,38,38,0.18)">
                  <p class="text-xs font-semibold text-red-600">Document rejected — please re-upload</p>
                  <p v-if="rejectedFor(req.type)!.verification_note"
                     class="text-xs text-red-400 mt-0.5 italic">"{{ rejectedFor(req.type)!.verification_note }}"</p>
                </div>

                <!-- Uploaded file info -->
                <div v-if="uploadedFor(req.type)" class="mt-2 flex items-center gap-3">
                  <div class="flex items-center gap-2 flex-1 min-w-0 rounded-lg px-3 py-2"
                       style="background: #f8fafc; border: 1px solid #e2e8f0">
                    <DocumentIcon class="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                    <span class="text-xs text-slate-600 truncate">{{ uploadedFor(req.type)!.original_filename || req.label }}</span>
                    <span v-if="uploadedFor(req.type)!.is_verified"
                          class="ml-auto text-[10px] font-bold flex-shrink-0"
                          style="color: #059669">Verified</span>
                    <span v-else class="ml-auto text-[10px] text-slate-400 flex-shrink-0">Pending</span>
                  </div>
                  <a v-if="uploadedFor(req.type)!.file_url || uploadedFor(req.type)!.file"
                     :href="uploadedFor(req.type)!.file_url || uploadedFor(req.type)!.file" target="_blank"
                     class="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex-shrink-0">View</a>
                  <button class="text-xs font-semibold text-red-500 hover:text-red-700 flex-shrink-0"
                          @click="handleDelete(uploadedFor(req.type)!.id)">Remove</button>
                </div>

                <!-- Upload area (shown when not yet uploaded) -->
                <div v-else class="mt-2">
                  <label v-if="activeUpload !== req.type"
                         class="flex items-center gap-2.5 px-4 py-2.5 rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 cursor-pointer hover:border-emerald-300 hover:bg-emerald-50/40 transition-colors group">
                    <ArrowUpTrayIcon class="w-4 h-4 text-slate-400 group-hover:text-emerald-500 flex-shrink-0" />
                    <span class="text-xs font-semibold text-slate-500 group-hover:text-emerald-600">
                      {{ pendingFiles[req.type] ? pendingFiles[req.type]!.name : 'Click to select file' }}
                    </span>
                    <input type="file" class="hidden"
                           accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                           @change="(e) => onFileChange(e, req.type)" />
                  </label>

                  <div v-if="pendingFiles[req.type] && activeUpload !== req.type" class="mt-2 flex items-center gap-2">
                    <button class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white transition-all"
                            style="background: linear-gradient(135deg, #059669, #047857)"
                            :disabled="activeUpload === req.type"
                            @click="handleUpload(req.type)">
                      <ArrowUpTrayIcon class="w-3.5 h-3.5" />
                      Upload
                    </button>
                    <button class="px-3 py-2 rounded-xl text-xs font-semibold text-slate-500 border border-slate-200 hover:bg-slate-50"
                            @click="clearPending(req.type)">
                      Clear
                    </button>
                  </div>

                  <!-- Uploading spinner for this doc -->
                  <div v-if="activeUpload === req.type" class="mt-2 flex items-center gap-2">
                    <div class="w-4 h-4 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
                    <span class="text-xs text-slate-500">Uploading…</span>
                  </div>
                </div>
              </div>
            </div>
          </li>
        </ul>
      </div>

      <!-- Proceed to payment CTA — shown when all docs uploaded AND still draft -->
      <transition enter-active-class="transition duration-300 ease-out"
                  enter-from-class="opacity-0 translate-y-2" enter-to-class="opacity-100 translate-y-0">
        <div v-if="uploadedCount === REQUIRED_DOCS.length && appStatus === 'draft'" class="rounded-2xl overflow-hidden"
             style="background: linear-gradient(135deg, #022c22, #064e3b); border: 1px solid rgba(52,211,153,0.2)">
          <div class="px-5 py-5 flex flex-col sm:flex-row sm:items-center gap-4">
            <div class="flex items-center gap-3 flex-1 min-w-0">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                   style="background: rgba(52,211,153,0.15); border: 1px solid rgba(52,211,153,0.25)">
                <CheckCircleIcon class="w-5 h-5" style="color: #34d399" />
              </div>
              <div>
                <p class="text-white text-sm font-bold">All documents uploaded</p>
                <p class="text-emerald-300 text-xs mt-0.5">Click to confirm and proceed to payment</p>
              </div>
            </div>
            <button :disabled="requestingPayment"
                    class="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white flex-shrink-0 transition-all disabled:opacity-60"
                    style="background: linear-gradient(135deg, #059669, #047857); box-shadow: 0 4px 14px rgba(5,150,105,0.4)"
                    @click="handleRequestPayment">
              <svg v-if="requestingPayment" class="animate-spin w-4 h-4 opacity-80" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              <span>{{ requestingPayment ? 'Processing…' : 'Proceed to Payment' }}</span>
              <ChevronRightIcon v-if="!requestingPayment" class="w-4 h-4" />
            </button>
          </div>
          <div v-if="requestPaymentError" class="px-5 pb-4">
            <p class="text-xs text-red-300">{{ requestPaymentError }}</p>
          </div>
        </div>
      </transition>

      <!-- Resubmit CTA — shown when all rejected docs have been re-uploaded and status is awaiting_document_resubmission -->
      <transition enter-active-class="transition duration-300 ease-out"
                  enter-from-class="opacity-0 translate-y-2" enter-to-class="opacity-100 translate-y-0">
        <div v-if="uploadedCount === REQUIRED_DOCS.length && appStatus === 'awaiting_document_resubmission'"
             class="rounded-2xl overflow-hidden"
             style="background: linear-gradient(135deg, #1e1b4b, #312e81); border: 1px solid rgba(129,140,248,0.25)">
          <div class="px-5 py-5 flex flex-col sm:flex-row sm:items-center gap-4">
            <div class="flex items-center gap-3 flex-1 min-w-0">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                   style="background: rgba(129,140,248,0.15); border: 1px solid rgba(129,140,248,0.25)">
                <CheckCircleIcon class="w-5 h-5" style="color: #818cf8" />
              </div>
              <div>
                <p class="text-white text-sm font-bold">Documents re-uploaded</p>
                <p class="text-indigo-300 text-xs mt-0.5">Click to resubmit for committee review</p>
              </div>
            </div>
            <button :disabled="resubmitting"
                    class="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white flex-shrink-0 transition-all disabled:opacity-60"
                    style="background: linear-gradient(135deg, #4f46e5, #4338ca); box-shadow: 0 4px 14px rgba(79,70,229,0.4)"
                    @click="handleResubmit">
              <svg v-if="resubmitting" class="animate-spin w-4 h-4 opacity-80" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              <span>{{ resubmitting ? 'Submitting…' : 'Resubmit for Review' }}</span>
              <ChevronRightIcon v-if="!resubmitting" class="w-4 h-4" />
            </button>
          </div>
          <div v-if="resubmitError" class="px-5 pb-4">
            <p class="text-xs text-red-300">{{ resubmitError }}</p>
          </div>
        </div>
      </transition>

      <!-- Back link -->
      <div class="pb-4">
        <RouterLink :to="`/applications/${route.params.id}`"
                    class="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-slate-700 transition-colors">
          <ChevronLeftIcon class="w-4 h-4" />
          Back to Application
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink, useRouter } from 'vue-router'
import {
  DocumentIcon, DocumentArrowUpIcon, CheckCircleIcon,
  ChevronRightIcon, ChevronLeftIcon, ArrowUpTrayIcon,
} from '@heroicons/vue/24/outline'
import { documentApi, applicationApi } from '@/services/api'


interface Doc {
  id: string
  document_type: string
  document_type_display?: string
  original_filename?: string
  file?: string
  file_url?: string
  is_verified?: boolean
  is_rejected?: boolean
  verification_note?: string
}

const REQUIRED_DOCS = [
  { type: 'nin_verification_slip', label: 'NIN Verification Slip' },
  { type: 'passport_photograph', label: 'Passport Photograph' },
  { type: 'royal_fathers_recognition_letter', label: 'Royal Fathers Recognition Letter' },
  { type: 'survey_property_document', label: 'Survey Property Document' },
]

const route = useRoute()
const router = useRouter()
const documents = ref<Doc[]>([])
const appStatus = ref('')
const loadingDocs = ref(false)
const activeUpload = ref<string | null>(null)
const globalError = ref('')
const pendingFiles = ref<Record<string, File | null>>({})
const requestingPayment = ref(false)
const requestPaymentError = ref('')
const resubmitting = ref(false)
const resubmitError = ref('')

const uploadedCount = computed(() =>
  REQUIRED_DOCS.filter(r => uploadedFor(r.type)).length
)

function uploadedFor(type: string): Doc | undefined {
  return documents.value.find(d => d.document_type === type && !d.is_rejected)
}

function rejectedFor(type: string): Doc | undefined {
  return documents.value.find(d => d.document_type === type && d.is_rejected)
}

function onFileChange(e: Event, type: string) {
  const target = e.target as HTMLInputElement
  pendingFiles.value = { ...pendingFiles.value, [type]: target.files?.[0] ?? null }
  globalError.value = ''
}

function clearPending(type: string) {
  pendingFiles.value = { ...pendingFiles.value, [type]: null }
}

async function loadDocs() {
  loadingDocs.value = true
  try {
    const [docsRes, appRes] = await Promise.all([
      documentApi.list(route.params.id as string),
      applicationApi.get(route.params.id as string).catch(() => null),
    ])
    documents.value = Array.isArray(docsRes.data) ? docsRes.data : docsRes.data.results ?? []
    if (appRes?.data) appStatus.value = appRes.data.status
  } finally {
    loadingDocs.value = false
  }
}

async function handleUpload(type: string) {
  const file = pendingFiles.value[type]
  if (!file) return
  globalError.value = ''
  resubmitError.value = ''
  activeUpload.value = type
  try {
    const fd = new FormData()
    fd.append('application_id', route.params.id as string)
    fd.append('document_type', type)
    fd.append('file', file)
    await documentApi.upload(fd)
    pendingFiles.value = { ...pendingFiles.value, [type]: null }
    await loadDocs()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    globalError.value = e.response?.data?.detail || 'Upload failed. Please try again.'
  } finally {
    activeUpload.value = null
  }
}

async function handleDelete(id: string) {
  if (!confirm('Remove this document?')) return
  globalError.value = ''
  try {
    await documentApi.delete(id)
    await loadDocs()
  } catch {
    globalError.value = 'Failed to remove document.'
  }
}

async function handleRequestPayment() {
  requestPaymentError.value = ''
  requestingPayment.value = true
  try {
    await applicationApi.requestPayment(route.params.id as string)
    router.push(`/applications/${route.params.id}/payment`)
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    requestPaymentError.value = e.response?.data?.detail || 'Failed to proceed. Please try again.'
    requestingPayment.value = false
  }
}

async function handleResubmit() {
  resubmitError.value = ''
  resubmitting.value = true
  try {
    await applicationApi.resubmitDocuments(route.params.id as string)
    router.push(`/applications/${route.params.id}`)
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    resubmitError.value = e.response?.data?.detail || 'Failed to resubmit. Please try again.'
    resubmitting.value = false
  }
}

onMounted(loadDocs)
</script>
