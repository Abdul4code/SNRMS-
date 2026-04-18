<template>
  <span :class="badgeClasses" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  submitted: 'bg-blue-100 text-blue-700',
  awaiting_stage_a_payment: 'bg-yellow-100 text-yellow-700',
  awaiting_stage_a_payment_confirmation: 'bg-orange-100 text-orange-700',
  awaiting_stage_c_payment: 'bg-yellow-100 text-yellow-700',
  awaiting_stage_c_payment_confirmation: 'bg-orange-100 text-orange-700',
  awaiting_renewal_payment: 'bg-yellow-100 text-yellow-700',
  awaiting_renewal_payment_confirmation: 'bg-orange-100 text-orange-700',
  stage_a_confirmed: 'bg-green-100 text-green-700',
  stage_c_confirmed: 'bg-green-100 text-green-700',
  under_naming_committee_review: 'bg-purple-100 text-purple-700',
  awaiting_document_resubmission: 'bg-red-100 text-red-700',
  approved_by_committee: 'bg-emerald-100 text-emerald-700',
  rejected_by_committee: 'bg-red-100 text-red-700',
  awaiting_chairman_approval: 'bg-blue-100 text-blue-700',
  approved_by_chairman: 'bg-emerald-100 text-emerald-700',
  rejected_by_chairman: 'bg-red-100 text-red-700',
  certificate_issued: 'bg-teal-100 text-teal-700',
  expired: 'bg-orange-100 text-orange-700',
  renewal_submitted: 'bg-indigo-100 text-indigo-700',
  renewed: 'bg-green-100 text-green-700',
  renewal_payment_confirmed: 'bg-indigo-100 text-indigo-700',
  withdrawn: 'bg-gray-100 text-gray-500',
}

const badgeClasses = computed(() => STATUS_COLORS[props.status] ?? 'bg-gray-100 text-gray-600')

const label = computed(() => props.status.replace(/_/g, ' '))
</script>
