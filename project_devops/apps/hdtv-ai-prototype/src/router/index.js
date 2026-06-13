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
const TokenUsageView     = () => import('../views/TokenUsageView.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', name: 'login', component: LoginView },
    { path: '/dashboard',  name: 'dashboard',  component: DashboardView, meta: { requiresAuth: true } },
    { path: '/dossiers',   name: 'dossiers',   component: DossierListView,    meta: { requiresAuth: true } },
    { path: '/workflow',   name: 'workflow',   component: WorkflowManager,    meta: { requiresAuth: true } },
    { path: '/workspace/:id?', name: 'workspace', component: SplitViewWorkspace, meta: { requiresAuth: true } },
    { path: '/skills',     name: 'skills',     component: SkillBuilderView,   meta: { requiresAuth: true } },
    { path: '/tools',      name: 'tools',      component: ToolRegistryView,   meta: { requiresAuth: true } },
    { path: '/graph',      name: 'graph',      component: KnowledgeGraphView, meta: { requiresAuth: true } },
    { path: '/schedule',   name: 'schedule',   component: ScheduleManagerView,meta: { requiresAuth: true } },
    { path: '/alerts',     name: 'alerts',     component: AlertsView,         meta: { requiresAuth: true } },
    { path: '/chat',       name: 'chat',       component: AdvancedChatView,   meta: { requiresAuth: true } },
    { path: '/settings',   name: 'settings',   component: DossierSettingsView,meta: { requiresAuth: true } },
    { path: '/admin',      name: 'admin',      component: SystemAdminView, meta: { requiresAuth: true, requiresRole: ['admin'] } },
    { path: '/notifications', name: 'notifications', component: NotificationsView, meta: { requiresAuth: true } },
    { path: '/token-usage',   name: 'token-usage',   component: TokenUsageView,    meta: { requiresAuth: true, requiresRole: ['admin', 'hdtv_leader'] } },
  ],
})

// Route guards — RBAC only (no login redirect — auto-login as admin on mount)
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // /login không còn dùng — redirect về dashboard
  if (to.name === 'login') {
    next('/dashboard')
    return
  }

  if (to.meta.requiresRole && !authStore.hasRole(to.meta.requiresRole)) {
    next('/dashboard')
    return
  }

  next()
})

export default router
