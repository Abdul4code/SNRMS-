<template>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Notifications</h1>
        <p class="text-sm text-gray-500 mt-0.5">
          {{ store.unreadCount > 0 ? `${store.unreadCount} unread` : 'All caught up' }}
        </p>
      </div>
      <button
        v-if="store.unreadCount > 0"
        :disabled="store.loading"
        class="btn-secondary text-sm"
        @click="store.markAllRead()"
      >
        Mark all read
      </button>
    </div>

    <div v-if="store.loading" class="flex justify-center py-16">
      <div class="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" />
    </div>

    <div v-else-if="!store.notifications.length" class="text-center py-20 bg-white rounded-xl border border-gray-200">
      <BellIcon class="w-12 h-12 text-gray-300 mx-auto mb-3" />
      <h3 class="text-base font-medium text-gray-900 mb-1">No notifications</h3>
      <p class="text-sm text-gray-500">You're all caught up!</p>
    </div>

    <div v-else class="space-y-2">
      <!-- Group by date -->
      <template v-for="(group, date) in groupedNotifications" :key="date">
        <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mt-4 mb-2 px-1">{{ date }}</p>
        <div class="space-y-1">
          <button
            v-for="n in group"
            :key="n.id"
            :class="[
              'w-full text-left p-4 rounded-xl border transition-colors',
              n.is_read
                ? 'bg-white border-gray-200 hover:bg-gray-50'
                : 'bg-blue-50 border-blue-200 hover:bg-blue-100',
            ]"
            @click="handleNotificationClick(n)"
          >
            <div class="flex items-start gap-3">
              <div
                :class="n.is_read ? 'bg-gray-200' : 'bg-blue-500'"
                class="w-2 h-2 rounded-full mt-1.5 flex-shrink-0"
              />
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 leading-snug">{{ n.title }}</p>
                <p class="text-sm text-gray-600 mt-0.5 leading-relaxed">{{ n.message }}</p>
                <p class="text-xs text-gray-400 mt-1">{{ formatTime(n.created_at) }}</p>
              </div>
              <span v-if="!n.is_read" class="text-xs text-blue-600 font-medium flex-shrink-0">New</span>
            </div>
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { BellIcon } from '@heroicons/vue/24/outline'
import { useNotificationStore } from '@/stores/notifications'
import type { Notification } from '@/stores/notifications'

const store = useNotificationStore()
const router = useRouter()

const groupedNotifications = computed(() => {
  const groups: Record<string, Notification[]> = {}
  for (const n of store.notifications) {
    const dateKey = formatGroupDate(n.created_at)
    if (!groups[dateKey]) groups[dateKey] = []
    groups[dateKey].push(n)
  }
  return groups
})

function formatGroupDate(d: string) {
  const date = new Date(d)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  if (date.toDateString() === today.toDateString()) return 'Today'
  if (date.toDateString() === yesterday.toDateString()) return 'Yesterday'
  return date.toLocaleDateString('en-NG', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
}

function formatTime(d: string) {
  return new Date(d).toLocaleTimeString('en-NG', { hour: '2-digit', minute: '2-digit', hour12: true })
}

async function handleNotificationClick(n: Notification) {
  if (!n.is_read) {
    await store.markRead(n.id)
  }
  if (n.application) {
    router.push(`/applications/${n.application}`)
  }
}

onMounted(() => store.fetchNotifications())
</script>
