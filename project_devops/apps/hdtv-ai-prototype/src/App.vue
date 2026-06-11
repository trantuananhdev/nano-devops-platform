<script setup>
import { ref, onMounted, computed } from 'vue'
import { RouterView, RouterLink, useRoute } from 'vue-router'
import { LayoutDashboard, FileText, GitPullRequest, Sun, Moon, Menu, X, Bot, Settings2, Wrench, Network, CalendarClock, Bell, CheckCircle, AlertTriangle, MessageSquare, FileCog, ShieldCheck } from '@lucide/vue'
import FloatingChat from './components/FloatingChat.vue'
import GlobalSearch from './components/GlobalSearch.vue'

const route = useRoute()
const isDark = ref(false)
const isMobileMenuOpen = ref(false)

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
}

// Auto-detect system theme on mount
onMounted(() => {
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    isDark.value = true
    document.documentElement.setAttribute('data-theme', 'dark')
  }
})

const navItems = [
  { path: '/dashboard', name: 'Dashboard', icon: LayoutDashboard },
  { path: '/chat', name: 'Chat', icon: MessageSquare },
  { path: '/dossiers', name: 'Quản lý Tờ trình', icon: FileText },
  { path: '/alerts', name: 'Cảnh báo', icon: AlertTriangle },
  { path: '/workflow', name: 'Quy trình', icon: GitPullRequest },
  { path: '/settings', name: 'Cấu hình Tờ trình', icon: FileCog },
  { path: '/skills', name: 'Đào tạo Trợ lý AI', icon: Settings2 },
  { path: '/tools', name: 'Danh mục Công cụ', icon: Wrench },
  { path: '/graph', name: 'Đồ thị Tri thức', icon: Network },
  { path: '/schedule', name: 'Lập lịch Tự động', icon: CalendarClock },
  { path: '/admin', name: 'Quản trị Hệ thống', icon: ShieldCheck },
]

const isNotifOpen = ref(false)
const notifications = ref([
  { id: 1, title: 'Nhiệm vụ hoàn tất', message: 'AI đã tổng hợp xong Báo cáo Tồn kho (Cron Job 08:00).', time: '5 phút trước', unread: true },
  { id: 2, title: 'Cảnh báo đồng bộ ERP', message: 'Mất kết nối với hệ thống HRMS SSO.', time: '1 giờ trước', unread: true },
  { id: 3, title: 'Tờ trình mới', message: 'Có 3 tờ trình vừa được chuyển qua luồng DOffice.', time: '2 giờ trước', unread: false }
])

const unreadCount = computed(() => notifications.value.filter(n => n.unread).length)
</script>

<template>
  <div class="app-layout">
    <!-- Mobile Header -->
    <div class="mobile-header">
      <div class="logo-wrapper">
        <svg class="evn-logo-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <polygon points="50,5 58,42 95,50 58,58 50,95 42,58 5,50 42,42" class="star-outer" />
          <polygon points="50,20 55,45 80,50 55,55 50,80 45,55 20,50 45,45" class="star-inner" />
          <polygon points="50,35 52,48 65,50 52,52 50,65 48,52 35,50 48,48" class="star-core" />
        </svg>
        <div class="logo-text">
          <span class="logo-evn">EVN</span>HANOI <span class="logo-ai">AI</span>
        </div>
      </div>
      <button class="btn-icon" @click="isMobileMenuOpen = !isMobileMenuOpen">
        <Menu v-if="!isMobileMenuOpen" />
        <X v-else />
      </button>
    </div>

    <!-- Sidebar -->
    <aside class="sidebar glass-panel" :class="{ 'is-open': isMobileMenuOpen }">
      <div class="sidebar-header">
        <div class="logo-wrapper">
          <svg class="evn-logo-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <polygon points="50,5 58,42 95,50 58,58 50,95 42,58 5,50 42,42" class="star-outer" />
            <polygon points="50,20 55,45 80,50 55,55 50,80 45,55 20,50 45,45" class="star-inner" />
            <polygon points="50,35 52,48 65,50 52,52 50,65 48,52 35,50 48,48" class="star-core" />
          </svg>
          <div class="logo-text">
            <span class="logo-evn">EVN</span>HANOI <span class="logo-ai">AI</span>
          </div>
        </div>
      </div>

      <!-- T-11: Global Search (Ctrl+K) -->
      <div class="sidebar-search">
        <GlobalSearch />
      </div>

      <nav class="sidebar-nav">
        <RouterLink 
          v-for="item in navItems" 
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.path.startsWith(item.path) }"
          @click="isMobileMenuOpen = false"
        >
          <component :is="item.icon" :size="20" />
          <span>{{ item.name }}</span>
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <div class="theme-toggle" @click="toggleTheme">
          <div class="theme-track">
            <div class="theme-thumb" :class="{ 'is-dark': isDark }">
              <Moon v-if="isDark" :size="14" />
              <Sun v-else :size="14" />
            </div>
          </div>
          <span>{{ isDark ? 'Giao diện Tối' : 'Giao diện Sáng' }}</span>
        </div>
        
        <div class="user-profile">
          <div class="avatar">HĐ</div>
          <div class="user-info">
            <div class="name">Lãnh đạo HĐTV</div>
            <div class="role">Quản trị viên</div>
          </div>
          
          <!-- Notification Bell -->
          <div class="notif-wrapper">
            <button class="notif-btn" @click="isNotifOpen = !isNotifOpen">
              <Bell :size="20"/>
              <span class="notif-badge" v-if="unreadCount > 0">{{ unreadCount }}</span>
            </button>
            
            <!-- Notification Panel -->
            <div class="notif-panel glass-panel" v-if="isNotifOpen">
              <div class="notif-header">
                <h3>Thông báo hệ thống</h3>
                <span class="text-xs text-primary cursor-pointer">Đánh dấu đã đọc</span>
              </div>
              <div class="notif-list">
                <div v-for="notif in notifications" :key="notif.id" class="notif-item" :class="{ unread: notif.unread }">
                  <div class="notif-icon">
                    <CheckCircle v-if="!notif.unread" size="14" class="text-success"/>
                    <div v-else class="unread-dot"></div>
                  </div>
                  <div class="notif-content">
                    <div class="notif-title">{{ notif.title }}</div>
                    <div class="notif-msg">{{ notif.message }}</div>
                    <div class="notif-time">{{ notif.time }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <RouterView />
    </main>

    <!-- Overlay for mobile menu -->
    <div 
      class="mobile-overlay" 
      v-if="isMobileMenuOpen" 
      @click="isMobileMenuOpen = false"
    ></div>

    <!-- Floating AI Chatbot -->
    <FloatingChat />
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-image: radial-gradient(circle at top right, rgba(0, 86, 179, 0.05), transparent 40%),
                    radial-gradient(circle at bottom left, rgba(242, 101, 34, 0.05), transparent 40%);
}

[data-theme='dark'] .app-layout {
  background-image: radial-gradient(circle at top right, rgba(59, 130, 246, 0.1), transparent 40%),
                    radial-gradient(circle at bottom left, rgba(249, 115, 22, 0.1), transparent 40%);
}

/* Sidebar Styles */
.sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  display: flex;
  flex-direction: column;
  border-radius: 0;
  border-left: none;
  border-top: none;
  border-bottom: none;
  z-index: 50;
  transition: transform 0.3s ease;
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.sidebar-search {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--color-border);
}

.logo-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.evn-logo-svg {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}
.star-outer { fill: #003399; transition: fill 0.3s; }
.star-inner { fill: #ED1C24; }
.star-core { fill: #FFDE00; }

[data-theme='dark'] .star-outer { fill: #60A5FA; }

.logo-text {
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: -0.5px;
}
.logo-evn { color: #003399; transition: color 0.3s; }
[data-theme='dark'] .logo-evn { color: #60A5FA; }
.logo-ai { color: var(--color-accent); font-style: italic; }

.sidebar-nav {
  padding: 1.5rem 1rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  text-decoration: none;
  color: var(--color-text-secondary);
  font-weight: 500;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background: rgba(0, 0, 0, 0.03);
  color: var(--color-text-primary);
}

[data-theme='dark'] .nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.nav-item.active {
  background: var(--color-primary);
  color: white;
  box-shadow: 0 4px 12px rgba(0, 86, 179, 0.2);
}

.sidebar-footer {
  padding: 1.5rem 1rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Theme Toggle */
.theme-toggle {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
}
.theme-toggle:hover { color: var(--color-text-primary); }

.theme-track {
  width: 44px;
  height: 24px;
  background: var(--color-border);
  border-radius: 12px;
  position: relative;
  transition: background 0.3s;
}
.theme-thumb {
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  transition: transform 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.theme-thumb.is-dark {
  transform: translateX(20px);
  background: var(--color-bg-panel-solid);
  color: var(--color-accent);
}

/* User Profile */
.user-profile {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
}
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
.user-info .name {
  font-weight: 600;
  font-size: 0.95rem;
}
.user-info .role {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

/* Notifications */
.notif-wrapper {
  position: relative;
  margin-left: auto;
}
.notif-btn {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  position: relative;
  padding: 0.25rem;
  display: flex;
  transition: color 0.2s;
}
.notif-btn:hover { color: var(--color-text-primary); }
.notif-badge {
  position: absolute;
  top: -2px; right: -2px;
  background: var(--color-danger);
  color: white;
  font-size: 0.6rem;
  font-weight: 700;
  width: 16px; height: 16px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}

.notif-panel {
  position: absolute;
  bottom: 120%; left: 0;
  width: 320px;
  background: var(--color-bg-panel);
  border: 1px solid var(--color-border);
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
  border-radius: 12px;
  z-index: 100;
  display: flex; flex-direction: column;
}
.notif-header {
  padding: 1rem; border-bottom: 1px solid var(--color-border);
  display: flex; justify-content: space-between; align-items: center;
}
.notif-header h3 { font-size: 0.95rem; font-weight: 600; margin: 0; }
.text-xs { font-size: 0.75rem; }
.text-primary { color: var(--color-primary); }
.cursor-pointer { cursor: pointer; }
.notif-list { max-height: 300px; overflow-y: auto; }
.notif-item { padding: 1rem; border-bottom: 1px solid var(--color-border); display: flex; gap: 0.75rem; }
.notif-item.unread { background: rgba(0, 86, 179, 0.03); }
[data-theme='dark'] .notif-item.unread { background: rgba(59, 130, 246, 0.05); }
.notif-icon { padding-top: 0.2rem; }
.unread-dot { width: 8px; height: 8px; background: var(--color-primary); border-radius: 50%; }
.text-success { color: var(--color-success); }
.notif-title { font-weight: 600; font-size: 0.85rem; margin-bottom: 0.25rem; }
.notif-msg { font-size: 0.8rem; color: var(--color-text-secondary); margin-bottom: 0.4rem; line-height: 1.4; }
.notif-time { font-size: 0.7rem; color: var(--color-text-secondary); opacity: 0.7; }

/* Main Content */
.main-content {
  flex: 1;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
}

/* Mobile Header */
.mobile-header {
  display: none;
  height: var(--header-height);
  background: var(--color-bg-panel);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border);
  align-items: center;
  justify-content: space-between;
  padding: 0 1rem;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 40;
}

.btn-icon {
  background: none;
  border: none;
  color: var(--color-text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mobile-overlay {
  display: none;
}

/* Responsive */
@media (max-width: 768px) {
  .app-layout { flex-direction: column; }
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    transform: translateX(-100%);
  }
  .sidebar.is-open { transform: translateX(0); }
  .mobile-header { display: flex; }
  .main-content {
    margin-top: var(--header-height);
    height: calc(100vh - var(--header-height));
  }
  .mobile-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.5);
    z-index: 40;
  }
}
</style>
