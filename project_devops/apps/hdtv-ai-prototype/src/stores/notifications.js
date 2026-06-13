import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getUserNotifications, markNotificationRead, markAllNotificationsRead } from '../services/api'
import { useAuthStore } from './auth'

export const useNotificationsStore = defineStore('notifications', () => {
  const authStore = useAuthStore()

  const notifications = ref([])
  const totalCount = ref(0)
  const unreadCount = ref(0)
  const isLoading = ref(false)
  const error = ref(null)
  const currentOffset = ref(0)
  const hasMore = computed(() => currentOffset.value < totalCount.value)

  async function loadNotifications(offset = 0, limit = 20) {
    if (!authStore.currentUser) return
    
    isLoading.value = true
    error.value = null
    try {
      const params = { offset, limit }
      const response = await getUserNotifications(authStore.currentUser.id, params)
      
      if (offset === 0) {
        notifications.value = response.data.items
      } else {
        notifications.value = [...notifications.value, ...response.data.items]
      }
      
      totalCount.value = response.data.total
      unreadCount.value = response.data.unread_count
      currentOffset.value = offset + response.data.items.length
    } catch (err) {
      console.error('Failed to load notifications:', err)
      error.value = err.response?.data?.detail || err.message || 'Lỗi tải thông báo'
    } finally {
      isLoading.value = false
    }
  }

  async function markAsRead(notificationId) {
    error.value = null
    try {
      await markNotificationRead(notificationId, true)
      
      const notification = notifications.value.find(n => n.id === notificationId)
      if (notification && !notification.is_read) {
        notification.is_read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    } catch (err) {
      console.error('Failed to mark notification as read:', err)
      error.value = err.response?.data?.detail || err.message || 'Lỗi cập nhật trạng thái thông báo'
    }
  }

  async function markAllAsRead() {
    if (!authStore.currentUser) return
    
    error.value = null
    try {
      await markAllNotificationsRead(authStore.currentUser.id)
      
      notifications.value.forEach(n => n.is_read = true)
      unreadCount.value = 0
    } catch (err) {
      console.error('Failed to mark all notifications as read:', err)
      error.value = err.response?.data?.detail || err.message || 'Lỗi đánh dấu tất cả đã đọc'
    }
  }

  function addNotification(notification) {
    notifications.value.unshift(notification)
    totalCount.value += 1
    if (!notification.is_read) {
      unreadCount.value += 1
    }
  }

  return {
    notifications,
    totalCount,
    unreadCount,
    isLoading,
    hasMore,
    error,
    loadNotifications,
    markAsRead,
    markAllAsRead,
    addNotification,
  }
})
