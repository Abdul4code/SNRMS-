<template>
  <div class="min-h-screen" style="background: #f1f5f9">
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
