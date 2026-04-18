<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <!-- Header band -->
    <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
      <div class="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Inbox</p>
            <h1 class="text-white text-2xl font-bold tracking-tight">Notifications</h1>
            <p class="text-slate-400 text-sm mt-1">
              {{ store.unreadCount > 0 ? `${store.unreadCount} unread` : 'All caught up' }}
            </p>
          </div>
          <button v-if="store.unreadCount > 0" :disabled="store.loading"
                  class="flex-shrink-0 flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-slate-700 border border-slate-200 bg-white hover:bg-slate-50 transition-all"
                  @click="store.markAllRead()">
            <CheckIcon class="w-4 h-4" />
            Mark all read
          </button>
        </div>
      </div>
    </div>

    <div class="max-w-3xl mx-auto px-4 sm:px-6 py-8">

      <!-- Loading -->
      <div v-if="store.loading" class="flex items-center justify-center py-16">
        <div class="w-9 h-9 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
      </div>

      <!-- Empty state -->
      <div v-else-if="!store.notifications.length"
           class="flex flex-col items-center justify-center py-20 rounded-2xl"
           style="background: #fff; border: 1px solid #e2e8f0">
        <div class="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
             style="background: rgba(5,150,105,0.07); border: 1px solid rgba(5,150,105,0.12)">
          <BellIcon class="w-7 h-7" style="color: #059669" />
        </div>
        <p class="text-base font-bold text-slate-900 mb-1">No notifications</p>
        <p class="text-sm text-slate-500">You're all caught up!</p>
      </div>

      <!-- Grouped notifications -->
      <div v-else class="space-y-5">
        <template v-for="(group, date) in groupedNotifications" :key="date">
          <div>
            <p class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 px-1">{{ date }}</p>
            <div class="rounded-2xl overflow-hidden"
                 style="background: #fff; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.05)">
              <button v-for="(n, i) in group" :key="n.id"
                      class="w-full text-left flex items-start gap-4 px-5 py-4 transition-colors"
                      :class="n.is_read ? 'hover:bg-slate-50/70' : 'hover:bg-emerald-50/50'"
                      :style="i < group.length - 1 ? 'border-bottom: 1px solid #f8fafc' : ''"
                      @click="handleNotificationClick(n)">
                <!-- Dot indicator -->
                <div class="flex-shrink-0 mt-1.5">
                  <div class="w-2 h-2 rounded-full"
                       :style="n.is_read ? 'background: #cbd5e1' : 'background: #059669'"></div>
                </div>
                <!-- Content -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-start justify-between gap-2">
                    <p class="text-sm font-semibold text-slate-900 leading-snug" :class="!n.is_read ? 'text-slate-900' : 'text-slate-700'">
                      {{ n.title }}
                    </p>
                    <span v-if="!n.is_read"
                          class="flex-shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-full"
                          style="background: rgba(5,150,105,0.1); color: #059669; border: 1px solid rgba(5,150,105,0.2)">
                      New
                    </span>
                  </div>
                  <p class="text-sm text-slate-500 mt-0.5 leading-relaxed">{{ n.message }}</p>
                  <p class="text-xs text-slate-400 mt-1">{{ formatTime(n.created_at) }}</p>
                </div>
                <!-- Arrow if linked -->
                <ChevronRightIcon v-if="n.application" class="w-4 h-4 text-slate-300 flex-shrink-0 mt-1" />
              </button>
            </div>
          </div>
        </template>

        <!-- Load more -->
        <div v-if="store.hasMore" class="flex justify-center pt-1">
          <button :disabled="store.loading"
                  class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-600 border border-slate-200 bg-white hover:bg-slate-50 transition-all disabled:opacity-50"
                  @click="store.loadMore()">
            <span v-if="store.loading" class="w-4 h-4 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></span>
            {{ store.loading ? 'Loading…' : 'Load more' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { BellIcon, CheckIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'
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
  if (!n.is_read) await store.markRead(n.id)
  if (n.application) router.push(`/applications/${n.application}`)
}

onMounted(() => store.fetchNotifications())
</script>
