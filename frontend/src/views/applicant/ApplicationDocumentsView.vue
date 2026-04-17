<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <!-- Page header band -->
    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-3xl mx-auto px-4 sm:px-6 py-5">
        <nav class="flex items-center gap-2 text-xs text-slate-400 mb-3">
          <RouterLink to="/applications" class="hover:text-emerald-400 transition-colors">My Applications</RouterLink>
          <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
          <RouterLink :to="`/applications/${route.params.id}`" class="hover:text-emerald-400 transition-colors font-mono">
            APP-{{ route.params.id }}
          </RouterLink>
          <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
          <span class="text-slate-300">Documents</span>
        </nav>
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1">Documents</p>
        <h1 class="text-white text-xl font-bold tracking-tight">Application Documents</h1>
        <p class="text-slate-400 text-sm mt-0.5">Upload and manage your supporting documents</p>
      </div>
    </div>

    <div class="max-w-3xl mx-auto px-4 sm:px-6 py-6 space-y-4">

      <!-- Upload card -->
      <div class="rounded-2xl overflow-hidden"
           style="background: #fff; border: 1px solid #e2e8f0">
        <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
          <h2 class="text-sm font-bold text-slate-900">Upload Document</h2>
          <p class="text-xs text-slate-500 mt-0.5">Accepted formats: PDF, JPG, PNG, DOC, DOCX</p>
        </div>

        <!-- Success / error -->
        <transition enter-active-class="transition duration-200 ease-out"
                    enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
          <div v-if="errorMsg" class="mx-5 mt-5 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-3.5">
            <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
            </svg>
            <p class="text-sm text-red-700">{{ errorMsg }}</p>
          </div>
        </transition>
        <transition enter-active-class="transition duration-200 ease-out"
                    enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
          <div v-if="successMsg" class="mx-5 mt-5 flex items-start gap-3 rounded-xl border border-emerald-100 bg-emerald-50 p-3.5">
            <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/>
            </svg>
            <p class="text-sm text-emerald-700">{{ successMsg }}</p>
          </div>
        </transition>

        <form @submit.prevent="handleUpload" class="px-5 py-5 space-y-4" novalidate>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              Document Type <span class="text-red-500">*</span>
            </label>
            <input v-model="upload.document_type" type="text" required
                   placeholder="e.g. Survey Plan, Proof of Identity, Community Letter"
                   class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white transition-all"/>
          </div>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              File <span class="text-red-500">*</span>
            </label>
            <!-- File drop zone -->
            <label class="flex flex-col items-center justify-center gap-3 p-6 rounded-xl border-2 border-dashed cursor-pointer transition-colors"
                   :class="selectedFile ? 'border-emerald-300 bg-emerald-50' : 'border-slate-200 hover:border-slate-300 bg-slate-50'">
              <div v-if="selectedFile" class="flex items-center gap-2.5">
                <div class="w-9 h-9 rounded-lg flex items-center justify-center"
                     style="background: rgba(5,150,105,0.1); border: 1px solid rgba(5,150,105,0.2)">
                  <DocumentIcon class="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <p class="text-sm font-semibold text-slate-900">{{ selectedFile.name }}</p>
                  <p class="text-xs text-slate-500">{{ (selectedFile.size / 1024).toFixed(1) }} KB</p>
                </div>
              </div>
              <div v-else class="flex flex-col items-center gap-2">
                <ArrowUpTrayIcon class="w-8 h-8 text-slate-400" />
                <div class="text-center">
                  <p class="text-sm font-semibold text-slate-700">Click to select a file</p>
                  <p class="text-xs text-slate-400 mt-0.5">PDF, JPG, PNG, DOC, DOCX</p>
                </div>
              </div>
              <input ref="fileInput" type="file" required class="hidden"
                     accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                     @change="onFileChange" />
            </label>
          </div>
          <button type="submit"
                  :disabled="uploading || !selectedFile || !upload.document_type"
                  class="flex items-center justify-center gap-2 w-full px-5 py-3 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                  style="background: linear-gradient(135deg, #059669, #047857); box-shadow: 0 4px 16px rgba(5,150,105,0.25)">
            <svg v-if="uploading" class="animate-spin w-4 h-4 opacity-80" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            <ArrowUpTrayIcon v-else class="w-4 h-4 opacity-80" />
            {{ uploading ? 'Uploading…' : 'Upload Document' }}
          </button>
        </form>
      </div>

      <!-- Documents list card -->
      <div class="rounded-2xl overflow-hidden"
           style="background: #fff; border: 1px solid #e2e8f0">
        <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
          <h2 class="text-sm font-bold text-slate-900">Uploaded Documents</h2>
          <p class="text-xs text-slate-500 mt-0.5">{{ documents.length }} document{{ documents.length === 1 ? '' : 's' }}</p>
        </div>

        <div v-if="loadingDocs" class="flex items-center justify-center py-12">
          <div class="w-7 h-7 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
        </div>

        <div v-else-if="!documents.length" class="flex flex-col items-center py-12 gap-2">
          <DocumentIcon class="w-9 h-9 text-slate-300" />
          <p class="text-sm text-slate-500">No documents uploaded yet.</p>
        </div>

        <ul v-else class="divide-y divide-slate-50">
          <li v-for="doc in documents" :key="doc.id" class="flex items-center gap-4 px-5 py-4">
            <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                 :style="doc.is_verified ? 'background: rgba(5,150,105,0.08); border: 1px solid rgba(5,150,105,0.18)' : 'background: #f8fafc; border: 1px solid #e2e8f0'">
              <DocumentIcon class="w-5 h-5" :style="doc.is_verified ? 'color: #059669' : 'color: #94a3b8'" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold text-slate-900 truncate">{{ doc.document_type_display || doc.document_type }}</p>
              <p class="text-xs mt-0.5" :class="doc.is_verified ? 'text-emerald-600' : 'text-slate-400'">
                {{ doc.is_verified ? '✓ Verified' : 'Pending verification' }}
              </p>
            </div>
            <div class="flex items-center gap-3 flex-shrink-0">
              <a v-if="doc.file" :href="doc.file" target="_blank"
                 class="text-xs font-semibold text-emerald-600 hover:text-emerald-700 transition-colors">
                View
              </a>
              <button class="text-xs font-semibold text-red-500 hover:text-red-700 transition-colors"
                      @click="handleDelete(doc.id)">
                Delete
              </button>
            </div>
          </li>
        </ul>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { DocumentIcon, ChevronRightIcon, ArrowUpTrayIcon } from '@heroicons/vue/24/outline'
import { documentApi } from '@/services/api'

interface Doc { id: number; document_type: string; document_type_display?: string; file?: string; is_verified?: boolean }

const route = useRoute()
const documents = ref<Doc[]>([])
const loadingDocs = ref(false)
const uploading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const upload = ref({ document_type: '' })
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  selectedFile.value = target.files?.[0] ?? null
  errorMsg.value = ''
  successMsg.value = ''
}

async function loadDocs() {
  loadingDocs.value = true
  try {
    const { data } = await documentApi.list(route.params.id as string)
    documents.value = Array.isArray(data) ? data : data.results ?? []
  } finally {
    loadingDocs.value = false
  }
}

async function handleUpload() {
  if (!selectedFile.value) return
  errorMsg.value = ''
  successMsg.value = ''
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('application', route.params.id as string)
    fd.append('document_type', upload.value.document_type)
    fd.append('file', selectedFile.value)
    await documentApi.upload(fd)
    upload.value.document_type = ''
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
    successMsg.value = 'Document uploaded successfully.'
    await loadDocs()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    errorMsg.value = e.response?.data?.detail || 'Upload failed. Please try again.'
  } finally {
    uploading.value = false
  }
}

async function handleDelete(id: number) {
  if (!confirm('Delete this document?')) return
  errorMsg.value = ''
  successMsg.value = ''
  try {
    await documentApi.delete(id)
    successMsg.value = 'Document deleted.'
    await loadDocs()
  } catch {
    errorMsg.value = 'Failed to delete document.'
  }
}

onMounted(loadDocs)
</script>
