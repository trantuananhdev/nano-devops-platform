<script setup>
import { ref, onMounted, computed } from 'vue'
import { Bell, Check, CheckCheck, Inbox, AlertTriangle } from '@lucide/vue'
import { useNotificationsStore } from '../stores/notifications'
import { useAuthStore } from '../stores/auth'

const notificationsStore = useNotificationsStore()
const authStore = useAuthStore()

onMounted(() => {
  if (authStore.currentUser) {
    notificationsStore.loadNotifications(0, 30)
  }
})

const loadMore = () => {
  notificationsStore.loadNotifications(notificationsStore.currentOffset, 20)
}
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <div>
        <h1 class="page-title">Thông báo</h1>
        <p class="page-subtitle">
          {{ notificationsStore.totalCount }} thông báo ({{ notificationsStore.unreadCount }} chưa đọc)
        </p>
      </div>
      <div class="header-actions">
        <button
          v-if="notificationsStore.unreadCount > 0"
          class="btn-secondary"
          @click="notificationsStore.markAllAsRead"
        >
          <CheckCheck size="18" />
          Đánh dấu tất cả đã đọc
        </button>
      </div>
    </header>

    <div v-if="notificationsStore.error" class="error-banner glass-panel flex items-center justify-between mb-4">
      <div class="flex items-center gap-2 text-danger">
        <AlertTriangle size="20" />
        <span>Lỗi: {{ notificationsStore.error }}</span>
      </div>
      <button class="btn-secondary btn-sm" @click="notificationsStore.loadNotifications(0, 30)">Thử lại</button>
    </div>

    <div class="notifications-container">
      <div v-if="notificationsStore.isLoading && notificationsStore.notifications.length === 0" class="loading-state">
        <div class="spinner"></div>
        <span>Đang tải thông báo...</span>
      </div>

      <div v-else-if="notificationsStore.notifications.length === 0" class="empty-state">
        <Inbox size="64" />
        <h3>Không có thông báo</h3>
        <p>Bạn chưa có thông báo nào</p>
      </div>

      <div v-else class="notifications-list">
        <div
          v-for="notification in notificationsStore.notifications"
          :key="notification.id"
          class="notification-card glass-panel"
          :class="{ unread: !notification.is_read }"
        >
          <div class="notification-icon" :class="notification.type">
            <Bell size="20" />
          </div>
          <div class="notification-content">
            <div class="notification-header">
              <h4 class="notification-title">{{ notification.title }}</h4>
              <span class="notification-time">{{ new Date(notification.created_at).toLocaleString('vi-VN') }}</span>
            </div>
            <p class="notification-message">{{ notification.message }}</p>
            <div v-if="notification.dossier_id" class="notification-meta">
              <span class="dossier-link">Tờ trình #{{ notification.dossier_id }}</span>
            </div>
          </div>
          <button
            v-if="!notification.is_read"
            class="mark-read-btn"
            @click="notificationsStore.markAsRead(notification.id)"
            title="Đánh dấu đã đọc"
          >
            <Check size="18" />
          </button>
        </div>

        <div v-if="notificationsStore.hasMore" class="load-more-container">
          <button
            v-if="!notificationsStore.isLoading"
            class="load-more-btn"
            @click="loadMore"
          >
            Tải thêm
          </button>
          <div v-else class="loading-more">
            <div class="spinner-small"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  gap: 1rem;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-secondary {
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-panel);
  color: var(--color-text-primary);
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.15s;
}
.btn-secondary:hover {
  background: rgba(0, 86, 179, 0.05);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.notifications-container {
  width: 100%;
}

.loading-state, .empty-state {
  padding: 4rem 2rem;
  text-align: center;
  color: var(--color-text-secondary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}
.empty-state h3 {
  font-size: 1.25rem;
  color: var(--color-text-primary);
  margin: 0;
}
.empty-state p {
  margin: 0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 86, 179, 0.2);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.notification-card {
  padding: 1.25rem;
  border-radius: 12px;
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}
.notification-card.unread {
  border-left: 4px solid var(--color-primary);
  background: rgba(0, 86, 179, 0.05);
}

.notification-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(0, 86, 179, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  flex-shrink: 0;
}
.notification-icon.status_change {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}
.notification-icon.appraisal_complete {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}
.notification-icon.feedback_submitted {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}
.notification-icon.clarification_requested {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.notification-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.notification-time {
  font-size: 0.85rem;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.notification-message {
  margin: 0 0 0.5rem 0;
  color: var(--color-text-secondary);
  font-size: 0.95rem;
  line-height: 1.5;
}

.notification-meta {
  display: flex;
  gap: 0.75rem;
}

.dossier-link {
  font-size: 0.85rem;
  color: var(--color-primary);
  font-weight: 500;
}

.mark-read-btn {
  background: none;
  border: 1px solid var(--color-border);
  color: var(--color-primary);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
}
.mark-read-btn:hover {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.load-more-container {
  display: flex;
  justify-content: center;
  padding: 1.5rem 0;
}

.load-more-btn {
  padding: 0.75rem 2rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-panel);
  color: var(--color-text-primary);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.load-more-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.loading-more {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--color-text-secondary);
}
.spinner-small {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(0, 86, 179, 0.2);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.error-banner {
  padding: 1rem 1.5rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  border-left: 4px solid var(--color-danger, #ef4444);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.flex { display: flex; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.gap-2 { gap: 0.5rem; }
.text-danger { color: var(--color-danger, #ef4444); }
.mb-4 { margin-bottom: 1rem; }
.btn-sm {
  padding: 0.4rem 0.5rem;
  font-size: 0.85rem;
}
</style>
