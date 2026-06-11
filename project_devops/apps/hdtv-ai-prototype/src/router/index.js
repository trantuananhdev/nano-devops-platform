import { createRouter, createWebHistory } from 'vue-router'

// T-39: Lazy load all views — each chunk only loads when the route is visited.
// This reduces initial bundle size significantly (bpmn-js alone is ~2MB).
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

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard',  name: 'dashboard',  component: DashboardView },
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
    { path: '/admin',      name: 'admin',      component: SystemAdminView },
  ],
})

export default router
