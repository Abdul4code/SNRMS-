<template>
  <div class="min-h-screen bg-slate-50">
    <TheNavbar v-if="auth.isAuthenticated" />
    <main>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import TheNavbar from '@/components/TheNavbar.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>
