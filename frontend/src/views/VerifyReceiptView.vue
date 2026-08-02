<template>
  <div class="min-h-screen flex items-center justify-center px-4" style="background:#f1f5f9">
    <div class="w-full max-w-md rounded-2xl bg-white border border-slate-200 p-8 text-center">
      <div class="w-14 h-14 rounded-2xl mx-auto flex items-center justify-center mb-4"
           :style="state === 'valid' ? 'background:#dcfce7' : state === 'invalid' ? 'background:#fee2e2' : 'background:#f1f5f9'">
        <span class="text-2xl">{{ state === 'valid' ? '✓' : state === 'invalid' ? '✕' : '…' }}</span>
      </div>

      <p class="text-xs font-bold tracking-widest uppercase mb-1"
         :style="state === 'valid' ? 'color:#059669' : state === 'invalid' ? 'color:#dc2626' : 'color:#94a3b8'">
        Receipt verification
      </p>

      <template v-if="state === 'loading'">
        <h1 class="text-lg font-bold text-slate-900">Checking…</h1>
      </template>

      <template v-else-if="state === 'valid'">
        <h1 class="text-lg font-bold text-slate-900 mb-1">Authentic receipt</h1>
        <p class="text-xs text-slate-500 mb-5">Issued by Ibeju-Lekki Local Government Area</p>
        <div class="text-left space-y-2 text-sm">
          <div class="flex justify-between"><span class="text-slate-500">Serial</span><span class="font-mono font-semibold">{{ data.serial }}</span></div>
          <div class="flex justify-between"><span class="text-slate-500">Paid by</span><span class="font-semibold">{{ data.payer_name }}</span></div>
          <div class="flex justify-between"><span class="text-slate-500">Street</span><span class="font-semibold">{{ data.street_name }}</span></div>
          <div class="flex justify-between"><span class="text-slate-500">Amount</span><span class="font-semibold" style="color:#059669">₦{{ data.amount }}</span></div>
          <div class="flex justify-between"><span class="text-slate-500">Reference</span><span class="font-mono text-xs">{{ data.reference || '—' }}</span></div>
        </div>
      </template>

      <template v-else>
        <h1 class="text-lg font-bold text-slate-900 mb-1">Not authentic</h1>
        <p class="text-sm text-slate-500">{{ reason || 'This receipt could not be verified. It may have been altered or is not genuine.' }}</p>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { receiptApi } from '@/services/api'

const route = useRoute()
const state = ref<'loading' | 'valid' | 'invalid'>('loading')
const data = ref<Record<string, string>>({})
const reason = ref('')

onMounted(async () => {
  const serial = String(route.params.serial || '')
  const code = String(route.query.code || '')
  try {
    const res = await receiptApi.verify(serial, code)
    if (res.data.valid) { state.value = 'valid'; data.value = res.data }
    else { state.value = 'invalid'; reason.value = res.data.reason }
  } catch (e: unknown) {
    state.value = 'invalid'
    const err = e as { response?: { data?: { reason?: string } } }
    reason.value = err.response?.data?.reason || 'Receipt not found.'
  }
})
</script>
