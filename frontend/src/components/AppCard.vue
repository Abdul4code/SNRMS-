<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200">
    <div v-if="title" class="px-6 py-4 border-b border-gray-200">
      <h3 class="text-base font-semibold text-gray-900">{{ title }}</h3>
    </div>
    <div class="p-6">
      <slot />
    </div>
    <div v-if="$slots.footer" class="px-6 py-4 bg-gray-50 border-t border-gray-200 rounded-b-xl">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title?: string
}>()
</script>
