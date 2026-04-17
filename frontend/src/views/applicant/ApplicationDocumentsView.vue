<template>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <nav class="text-sm text-gray-500 mb-6 flex items-center gap-2">
      <RouterLink to="/applications" class="hover:text-blue-600">My Applications</RouterLink>
      <span>/</span>
      <RouterLink :to="`/applications/${route.params.id}`" class="hover:text-blue-600">
        #{{ route.params.id }}
      </RouterLink>
      <span>/</span>
      <span class="text-gray-900">Documents</span>
    </nav>

    <AppCard title="Application Documents">
      <!-- Error / Success -->
      <div v-if="errorMsg" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{{ errorMsg }}</div>
      <div v-if="successMsg" class="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">{{ successMsg }}</div>

      <!-- Upload form -->
      <div class="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl">
        <h4 class="text-sm font-semibold text-blue-800 mb-3">Upload Document</h4>
        <form @submit.prevent="handleUpload" class="space-y-3">
          <div>
            <label class="form-label text-xs">Document Type</label>
            <input v-model="upload.document_type" type="text" required class="form-input text-sm" placeholder="e.g. Proof of Identity, Survey Plan" />
          </div>
          <div>
            <label class="form-label text-xs">File</label>
            <input
              ref="fileInput"
              type="file"
              required
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
              class="block w-full text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-100 file:text-blue-700 hover:file:bg-blue-200"
              @change="onFileChange"
            />
          </div>
          <button type="submit" :disabled="uploading" class="btn-primary text-sm">
            {{ uploading ? 'Uploading…' : 'Upload Document' }}
          </button>
        </form>
      </div>

      <!-- Documents list -->
      <div v-if="loadingDocs" class="flex justify-center py-8">
        <div class="animate-spin w-6 h-6 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
      <div v-else-if="!documents.length" class="text-center py-8 text-gray-500 text-sm">
        No documents uploaded yet.
      </div>
      <ul v-else class="space-y-2">
        <li
          v-for="doc in documents"
          :key="doc.id"
          class="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
        >
          <div class="flex items-center gap-3">
            <DocumentIcon class="w-5 h-5 text-gray-400" />
            <div>
              <p class="text-sm font-medium text-gray-900">{{ doc.document_type_display || doc.document_type }}</p>
              <p v-if="doc.is_verified" class="text-xs text-green-600 mt-0.5">Verified</p>
              <p v-else class="text-xs text-gray-400 mt-0.5">Pending verification</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <a v-if="doc.file" :href="doc.file" target="_blank" class="text-blue-600 hover:underline text-xs">View</a>
            <button
              class="text-red-500 hover:text-red-700 text-xs"
              @click="handleDelete(doc.id)"
            >
              Delete
            </button>
          </div>
        </li>
      </ul>
    </AppCard>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { DocumentIcon } from '@heroicons/vue/24/outline'
import { documentApi } from '@/services/api'
import AppCard from '@/components/AppCard.vue'

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
    errorMsg.value = e.response?.data?.detail || 'Upload failed.'
  } finally {
    uploading.value = false
  }
}

async function handleDelete(id: number) {
  if (!confirm('Delete this document?')) return
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
