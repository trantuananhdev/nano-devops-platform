# Frontend Architecture — L3 System Design

> **Tầng L3: Vue 3 SPA — cấu trúc, state management, realtime**
> **Audience:** Frontend Dev, Fullstack Dev
> **Cập nhật:** 2026-06-13

---

## Tổng quan

```
Vue 3 SPA (hdtv-fe)
├── Vite 5 (build tool, HMR)
├── Vue Router 4 (SPA routing)
├── Pinia (state management)
├── TailwindCSS (design tokens, dark mode)
├── Axios (REST client)
├── bpmn-js (BPMN workflow viewer)
└── Marked.js (Markdown render cho AI reports)
```

---

## Route Map

```
/                  → redirect /dashboard
/login             → LoginView.vue
/dashboard         → DashboardView.vue        (stats, KPI)
/dossiers          → DossierListView.vue       (filter, pagination)
/dossiers/:id      → DossierDetailView.vue     (tabs: info/appraisal/workflow)
/workspace/:id     → SplitViewWorkspace.vue    (PDF + Chat side-by-side)
/alerts            → AlertsView.vue            (filter resolved/open)
/notifications     → NotificationsView.vue     (mark read)
/reports           → ReportsView.vue           (role-based: leader/specialist)
/audit             → AuditLogView.vue          (AI audit trail)
/admin             → SystemAdminView.vue       (requiresRole: admin)
/clarifications    → ClarificationsView.vue    (pending HITL questions)
/skills            → SkillBuilderView.vue      (AI tool config)
/schedules         → ScheduleManagerView.vue   (Celery tasks)
```

---

## Pinia Stores

```
src/stores/
├── auth.js         ← user, token, role; login/logout
├── dossiers.js     ← list, currentDossier, filters, pagination
├── appraisals.js   ← currentAppraisal, streaming status, checkResults
├── notifications.js← items, unreadCount, markRead
├── alerts.js       ← list, filter (open/resolved)
├── ws.js           ← WebSocket connection, reconnect logic
└── chat.js         ← messages per dossier, streaming buffer
```

### Auth Flow
```javascript
// stores/auth.js
async function login(email, password) {
  const { data } = await axios.post('/api/v1/auth/login', { email, password })
  token.value = data.access_token
  user.value = data.user
  localStorage.setItem('hdtv_token', data.access_token)
  axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
  router.push('/dashboard')
}
```

### WebSocket Store
```javascript
// stores/ws.js — Reconnect với exponential backoff
function connect(userId) {
  ws = new WebSocket(`ws://localhost:8000/ws/${userId}`)
  ws.onmessage = (e) => handleEvent(JSON.parse(e.data))
  ws.onclose = () => scheduleReconnect()
}

function scheduleReconnect() {
  const delay = Math.min(1000 * 2 ** retries, 30000)  // 1s, 2s, 4s... max 30s
  setTimeout(() => { retries++; connect(userId) }, delay)
}

function handleEvent(event) {
  if (event.type === 'appraisal_complete')   appraisalsStore.setComplete(event.data)
  if (event.type === 'notification_new')      notificationsStore.addNew(event.data)
  if (event.type === 'stream_chunk')          chatStore.appendChunk(event.data.text)
  if (event.type === 'clarification_requested') clarificationStore.addPending(event.data)
}
```

---

## Key Views

### SplitViewWorkspace.vue
```
┌──────────────────────┬──────────────────────────┐
│  PDF Viewer          │  AI Chat Panel           │
│  (iframe presigned   │  - Chat history          │
│   MinIO URL)         │  - Stream chunks render  │
│                      │  - Clarification form    │
│  BPMN Diagram        │  - Appraisal result tabs │
│  (bpmn-js viewer,    │    Legal/Financial/Tech  │
│   lazy loaded)       │                          │
└──────────────────────┴──────────────────────────┘
```

**Performance:**
```javascript
// BPMN viewer lazy loaded — không block initial render
const BpmnViewer = defineAsyncComponent(
  () => import('@/components/BpmnDiagramViewer.vue')
)
```

### DossierListView.vue — Filter Bar
```
Filters: unit (select) | status (select) | risk_level (select) | search (text)
→ computed query params → GET /api/v1/dossiers?unit=X&status=Y&risk_level=Z
→ pagination: has_more → "Tải thêm" button
```

---

## Design System — TailwindCSS Variables

```css
/* All colors via CSS variables (dark mode compatible) */
--color-primary: #1a56db;     /* EVN blue */
--color-surface: #ffffff;     /* card background */
--color-text: #111928;        /* main text */
--color-border: #e5e7eb;

/* Dark mode */
.dark {
  --color-surface: #1f2937;
  --color-text: #f9fafb;
  --color-border: #374151;
}

/* Risk level colors */
--color-risk-low: #057a55;
--color-risk-medium: #c27803;
--color-risk-high: #e02424;
--color-risk-critical: #9b1c1c;
```

**Rule:** Không bao giờ hardcode hex màu trong component. Chỉ dùng `var(--color-*)` hoặc Tailwind utility classes đã map.

---

## API Client Pattern

```javascript
// src/services/api.js
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
})

// Interceptor: auto-attach token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('hdtv_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Interceptor: handle 401 → logout
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) authStore.logout()
    return Promise.reject(err)
  }
)
```

---

## Role-based Access

```javascript
// router/index.js
router.beforeEach((to, from) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return '/login'
  }
  if (to.meta.requiresRole && !to.meta.requiresRole.includes(auth.user?.role)) {
    return '/dashboard'  // unauthorized redirect
  }
})

// Route definitions
{ path: '/admin', meta: { requiresAuth: true, requiresRole: ['admin'] } }
{ path: '/reports', meta: { requiresAuth: true, requiresRole: ['admin', 'hdtv_leader', 'dept_head'] } }
```

---

## Build & Deploy

```
Dev:  vite dev      → :3080 (HMR)
Prod: vite build    → dist/
      nginx serve   → :80

Env vars (Vite):
  VITE_API_BASE_URL=http://localhost:8000
  VITE_WS_URL=ws://localhost:8000
```
