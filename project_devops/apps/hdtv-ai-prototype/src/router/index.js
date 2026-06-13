import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// T-39: Lazy load all views — each chunk only loads when the route is visited.
// This reduces initial bundle size significantly (bpmn-js alone is ~2MB).
const LoginView          = () => import('../views/LoginView.vue')
const DashboardView      = () => import('../views/DashboardView.vue')
const DossierListView    = () => import('../views/DossierListView.vue')
const WorkflowManager    = () => import('../views/WorkflowManager.vue')
const SplitViewWorkspace = () => import('../views/SplitViewWorkspace.vue')
const SkillBuilderView   = () => import('../views/SkillBuilderView.vue')
const ToolRegistryView   = () => import('../views/ToolRegistryView.vue')
const KnowledgeGraphView = () => import('../views/KnowledgeGraphView.vue')
const ScheduleManagerView = () => import('../views/ScheduleManagerView.vue')
const AlertsView         = () => import('../views/AlertsView.vue')
const AdvancedChatView   = () => import('../views/AdvancedChatView.vue')
const DossierSettingsView = () => import('../views/DossierSettingsView.vue')
const SystemAdminView    = () => import('../views/SystemAdminView.vue')
const NotificationsView  = () => import('../views/NotificationsView.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', name: 'login', component: LoginView },
    { path: '/dashboard',  name: 'dashboard',  component: DashboardView, meta: { requiresAuth: true } },
    { path: '/dossiers',   name: 'dossiers',   component: DossierListView },
    { path: '/workflow',   name: 'workflow',   component: WorkflowManager },
    { path: '/workspace/:id?', name: 'workspace', component: SplitViewWorkspace },
    { path: '/skills',     name: 'skills',     component: SkillBuilderView },
    { path: '/tools',      name: 'tools',      component: ToolRegistryView },
    { path: '/graph',      name: 'graph',      component: KnowledgeGraphView },
    { path: '/schedule',   name: 'schedule',   component: ScheduleManagerView },
    { path: '/alerts',     name: 'alerts',     component: AlertsView },
    { path: '/chat',       name: 'chat',       component: AdvancedChatView },
    { path: '/settings',   name: 'settings',   component: DossierSettingsView },
    { path: '/admin',      name: 'admin',      component: SystemAdminView, meta: { requiresAuth: true, requiresRole: ['admin'] } },
    { path: '/notifications', name: 'notifications', component: NotificationsView, meta: { requiresAuth: true } },
  ],
})

// Route guards — auth + RBAC
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // Routes không cần auth
  if (to.name === 'login') {
    if (authStore.isAuthenticated) {
      next('/dashboard')
    } else {
      next()
    }
    return
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  if (to.meta.requiresRole && !authStore.hasRole(to.meta.requiresRole)) {
    next('/dashboard')
    return
  }

  next()
})

export default router
