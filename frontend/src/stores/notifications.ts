import { ref } from 'vue'
import { defineStore } from 'pinia'
import { notificationApi } from '@/services/api'

export interface Notification {
  id: number
  title: string
  message: string
  is_read: boolean
  created_at: string
  notification_type?: string
  application?: number | null
}

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([])
  const unreadCount = ref(0)
  const loading = ref(false)
  const hasMore = ref(false)
  const currentPage = ref(1)

  async function fetchNotifications(unreadOnly = false) {
    loading.value = true
    currentPage.value = 1
    try {
      const params: Record<string, unknown> = unreadOnly ? { unread: true } : {}
      const { data } = await notificationApi.list(params)
      if (Array.isArray(data)) {
        notifications.value = data
        hasMore.value = false
      } else {
        notifications.value = data.results ?? []
        hasMore.value = !!data.next
      }
    } finally {
      loading.value = false
    }
  }

  async function loadMore() {
    if (!hasMore.value || loading.value) return
    loading.value = true
    currentPage.value++
    try {
      const { data } = await notificationApi.list({ page: currentPage.value })
      if (Array.isArray(data)) {
        notifications.value = [...notifications.value, ...data]
        hasMore.value = false
      } else {
        notifications.value = [...notifications.value, ...(data.results ?? [])]
        hasMore.value = !!data.next
      }
    } finally {
      loading.value = false
    }
  }

  async function markRead(id: number) {
    await notificationApi.markRead(id)
    const n = notifications.value.find((n) => n.id === id)
    if (n && !n.is_read) {
      n.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  }

  async function markAllRead() {
    await notificationApi.markAllRead()
    notifications.value.forEach((n) => (n.is_read = true))
    unreadCount.value = 0
  }

  async function fetchUnreadCount() {
    try {
      const { data } = await notificationApi.unreadCount()
      unreadCount.value = data.count ?? 0
    } catch {
      // silently fail
    }
  }

  return {
    notifications,
    unreadCount,
    loading,
    hasMore,
    fetchNotifications,
    loadMore,
    markRead,
    markAllRead,
    fetchUnreadCount,
  }
})
