<template>
  <div />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getRoleDefault } from '@/router/index'

const auth = useAuthStore()
const router = useRouter()

onMounted(() => {
  router.replace(getRoleDefault(auth.user?.role))
})
</script>
