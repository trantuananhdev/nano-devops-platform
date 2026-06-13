<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, X, Check } from '@lucide/vue'
import { useNotificationsStore } from '../stores/notifications'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const notificationsStore = useNotificationsStore()
const authStore = useAuthStore()

const isDropdownOpen = ref(false)

const unreadCount = computed(() => notificationsStore.unreadCount)
const recentNotifications = computed(() => notificationsStore.notifications.slice(0, 5))

onMounted(() => {
  if (authStore.currentUser) {
    notificationsStore.loadNotifications(0, 10)
  }
})

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
  if (isDropdownOpen.value) {
    // Load notifications when dropdown opens
    if (authStore.currentUser) {
      notificationsStore.loadNotifications(0, 10)
    }
  }
}

const goToNotifications = () => {
  isDropdownOpen.value = false
  router.push('/notifications')
}

const markSingleAsRead = (notification, event) => {
  event.stopPropagation()
  notificationsStore.markAsRead(notification.id)
}
</script>

<template>
  <div class="notification-bell-container">
    <button class="notification-btn glass-panel" @click="toggleDropdown">
      <Bell size="22" />
      <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
    </button>

    <div class="notification-dropdown glass-panel" v-if="isDropdownOpen">
      <div class="dropdown-header">
        <span class="dropdown-title">Thông báo</span>
        <button class="close-btn" @click="isDropdownOpen = false"><X size="16"/></button>
      </div>

      <div class="dropdown-body">
        <div v-if="notificationsStore.isLoading" class="loading-state">
          <div class="spinner"></div>
          <span>Đang tải...</span>
        </div>

        <div v-else-if="recentNotifications.length === 0" class="empty-state">
          <span>Không có thông báo mới</span>
        </div>

        <div v-else class="notification-list">
          <div
            v-for="notification in recentNotifications"
            :key="notification.id"
            class="notification-item"
            :class="{ unread: !notification.is_read }"
            @click="markSingleAsRead(notification, $event)"
          >
            <div class="notification-icon" :class="notification.type">
              <span class="icon-dot"></span>
            </div>
            <div class="notification-content">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-message">{{ notification.message }}</div>
              <div class="notification-time">{{ new Date(notification.created_at).toLocaleString('vi-VN') }}</div>
            </div>
            <button v-if="!notification.is_read" class="mark-read-btn" @click="markSingleAsRead(notification, $event)">
              <Check size="14" />
            </button>
          </div>
        </div>
      </div>

      <div class="dropdown-footer">
        <button class="view-all-btn" @click="goToNotifications">
          Xem tất cả thông báo
        </button>
        <button v-if="unreadCount > 0" class="mark-all-btn" @click="notificationsStore.markAllAsRead">
          Đánh dấu tất cả đã đọc
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notification-bell-container {
  position: relative;
  display: inline-block;
}

.notification-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: transform 0.2s;
}

.notification-btn:hover {
  transform: scale(1.05);
}

.notification-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  background: #ef4444;
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 0 2px var(--color-bg-panel);
}

.notification-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 360px;
  max-height: 480px;
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
  z-index: 1000;
}

.dropdown-header {
  padding: 1rem;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dropdown-title {
  font-weight: 600;
  color: var(--color-text-primary);
}

.close-btn {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
}
.close-btn:hover {
  background: rgba(0,0,0,0.05);
}

.dropdown-body {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem 0;
}

.loading-state, .empty-state {
  padding: 2rem 1rem;
  text-align: center;
  color: var(--color-text-secondary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(0, 86, 179, 0.2);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.notification-list {
  display: flex;
  flex-direction: column;
}

.notification-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background 0.15s;
}
.notification-item:hover {
  background: rgba(0, 86, 179, 0.05);
}
.notification-item.unread {
  background: rgba(0, 86, 179, 0.1);
}

.notification-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.icon-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
}
.notification-icon.status_change {
  background: rgba(245, 158, 11, 0.2);
}
.notification-icon.appraisal_complete {
  background: rgba(16, 185, 129, 0.2);
}
.notification-icon.feedback_submitted {
  background: rgba(59, 130, 246, 0.2);
}
.notification-icon.clarification_requested {
  background: rgba(239, 68, 68, 0.2);
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  color: var(--color-text-primary);
  font-size: 0.95rem;
  margin-bottom: 2px;
}

.notification-message {
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  margin-bottom: 4px;
}

.notification-time {
  color: var(--color-text-tertiary);
  font-size: 0.75rem;
}

.mark-read-btn {
  background: none;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.mark-read-btn:hover {
  background: rgba(0, 86, 179, 0.1);
}

.dropdown-footer {
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  gap: 0.5rem;
}

.view-all-btn, .mark-all-btn {
  flex: 1;
  padding: 0.6rem;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9rem;
  transition: background 0.15s;
}

.view-all-btn {
  background: var(--color-primary);
  color: white;
}
.view-all-btn:hover {
  background: #004aad;
}

.mark-all-btn {
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}
.mark-all-btn:hover {
  background: rgba(0, 86, 179, 0.05);
}
</style>
