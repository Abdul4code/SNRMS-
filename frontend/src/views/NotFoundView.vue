<template>
  <div class="min-h-screen flex flex-col items-center justify-center px-4" style="background: #f1f5f9">

    <div class="text-center max-w-md">
      <!-- 404 graphic -->
      <div class="relative mb-8 flex items-center justify-center">
        <span class="font-black select-none" style="font-size: 9rem; line-height: 1; color: #e2e8f0;">404</span>
        <div class="absolute inset-0 flex items-center justify-center">
          <div class="w-20 h-20 rounded-2xl flex items-center justify-center"
               style="background: linear-gradient(135deg, #059669, #047857); box-shadow: 0 8px 32px rgba(5,150,105,0.25)">
            <MapPinIcon class="w-10 h-10 text-white" />
          </div>
        </div>
      </div>

      <h1 class="text-2xl font-bold text-slate-900 mb-2">Page not found</h1>
      <p class="text-slate-500 text-sm mb-8 leading-relaxed">
        The page you're looking for doesn't exist or you don't have permission to view it.
      </p>

      <div class="flex flex-col sm:flex-row items-center justify-center gap-3">
        <button
          class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90 active:scale-95"
          style="background: linear-gradient(135deg, #059669, #047857)"
          @click="router.back()"
        >
          <ArrowLeftIcon class="w-4 h-4" />
          Go back
        </button>
        <RouterLink
          :to="homePath"
          class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all hover:bg-slate-200 active:scale-95"
          style="background: #e2e8f0; color: #334155"
        >
          <HomeIcon class="w-4 h-4" />
          Go to dashboard
        </RouterLink>
      </div>
    </div>

    <!-- Branding -->
    <p class="absolute bottom-6 text-xs text-slate-400">
      Street Naming &amp; Renaming Management System
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { MapPinIcon, ArrowLeftIcon, HomeIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { getRoleDefault } from '@/router/index'

const router = useRouter()
const auth = useAuthStore()

const homePath = computed(() => getRoleDefault(auth.user?.role))
</script>
