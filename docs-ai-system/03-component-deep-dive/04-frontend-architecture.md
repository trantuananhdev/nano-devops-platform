# Frontend Architecture — Vue.js Performance Design

> **Audience:** CTO, Frontend Lead
> **Mục đích:** Thiết kế frontend — tại sao cần virtual scroll, lazy load, và WebSocket real-time.

---

## Challenge: Large Data + Real-time Updates

Nghiệp vụ thẩm định có:
- **Thousands of dossiers** → render all = browser freeze
- **Real-time AI progress** → polling = lag, bad UX
- **Heavy BPMN diagram** (~2MB JS) → load upfront = slow initial load

---

## Virtual Scrolling (VirtualList.vue)

```
Problem: 10,000 dossiers → render 10,000 DOM nodes → browser OOM

Solution: Render chỉ ~20 rows visible + overscan buffer

┌─────────────────────────────────────┐ ← Viewport
│  Row 1  (visible)                   │
│  Row 2  (visible)                   │
│  Row 3  (visible)                   │
│  ...                                │
│  Row 20 (visible)                   │
└─────────────────────────────────────┘
│  [virtual space — not rendered]     │
│  Row 5000 (not in DOM)              │ → Tiết kiệm memory
│  ...                                │

Khi scroll: tính toán item mới → swap DOM nodes (reuse)
```

```javascript
// VirtualList.vue — zero dependency
const ITEM_HEIGHT = 48  // px, fixed height
const OVERSCAN = 5      // extra rows above/below viewport

const visibleItems = computed(() => {
    const start = Math.max(0, scrollTop.value / ITEM_HEIGHT - OVERSCAN)
    const end = Math.min(
        props.items.length,
        (scrollTop.value + viewportHeight) / ITEM_HEIGHT + OVERSCAN
    )
    return props.items.slice(start, end).map((item, i) => ({
        ...item,
        style: { transform: `translateY(${(start + i) * ITEM_HEIGHT}px)` }
    }))
})
```

**Result:** 10,000 rows → chỉ ~30 DOM nodes → smooth 60fps scroll.

---

## Lazy Loading (router/index.js)

```javascript
// BAD: Load everything upfront
import WorkflowManager from '@/views/WorkflowManager.vue'  // bpmn-js = 2MB!

// GOOD: Load on demand
const routes = [
    {
        path: '/workflow',
        component: () => import('@/views/WorkflowManager.vue')
        // bpmn-js chỉ load khi user vào /workflow
    },
    {
        path: '/dashboard',
        component: () => import('@/views/DashboardView.vue')
    },
    // ... tất cả routes đều lazy
]
```

**Result:** Initial bundle giảm ~60%. Page load nhanh hơn đáng kể.

---

## Infinite Scroll + Pagination

```javascript
// dossier.js store
const loadMoreDossiers = async () => {
    if (isLoading.value || !hasMore.value) return

    isLoading.value = true
    const response = await api.getDossiers({
        offset: dossiers.value.length,
        limit: 20
    })

    dossiers.value.push(...response.items)  // Append
    hasMore.value = response.has_more
    isLoading.value = false
}

// Trigger when scroll reaches bottom
const onScrollEnd = throttle(() => {
    if (isNearBottom()) loadMoreDossiers()
}, 200)  // Throttle 200ms to avoid API spam
```

```python
# Backend: DossierPage schema
class DossierPage(BaseModel):
    items: list[DossierOut]
    total: int
    has_more: bool
    offset: int
    limit: int
```

---

## WebSocket Real-time

```javascript
// stores/appraisal.js — WebSocket management
const connectAppraisal = (dossierId) => {
    ws = new WebSocket(`ws://localhost:8000/ws/appraisal/${dossierId}`)

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data)
        switch(msg.type) {
            case 'plan_created':
                progress.value = 20
                currentStep.value = 'Đã lập kế hoạch'
                break
            case 'tool_executing':
                toolProgress.value[msg.tool_name] = 'running'
                break
            case 'tool_result':
                toolProgress.value[msg.tool_name] = msg.status
                break
            case 'clarification_needed':
                showClarificationModal(msg.question, msg.options)
                break
            case 'critic_review':
                criticVerdict.value = msg.approved
                break
            case 'appraisal_complete':
                progress.value = 100
                loadResult(dossierId)
                break
        }
    }
}
```

**requestAnimationFrame cho scroll:**
```javascript
// AdvancedChatView.vue
let rafId = null

const scrollToBottom = () => {
    if (rafId) cancelAnimationFrame(rafId)
    rafId = requestAnimationFrame(() => {
        chatContainer.value?.scrollTo({ top: Infinity, behavior: 'smooth' })
        rafId = null
    })
}
```

---

## 14 Views Summary

| View | Data source | Special feature |
|------|-------------|-----------------|
| DossierList | `/dossiers` (paginated) | Virtual scroll, infinite load |
| SplitViewWorkspace | dossiers + WS | PDF iframe + live AI progress |
| AdvancedChatView | chat + appraise + WS | rAF scroll, chat pagination |
| WorkflowManager | `/workflows/{id}` | bpmn-js (lazy loaded ~2MB) |
| KnowledgeGraphView | `/knowledge-graph` | D3/Vis graph rendering |
| DashboardView | `/dashboard/summary` | KPI cards, charts |
| SystemAdminView | users + roles + agents + keys | 4 tabs: Users, API Keys, MCP Audit, Agent Intelligence |
| GlobalSearch | `/search?q=` (Meilisearch) | Ctrl+K modal, degraded mode |
| SkillBuilderView | `/skills` | Drag-and-drop skill configuration |
| ToolRegistryView | `/tools` | Tool registry management |
| ScheduleManagerView | `/schedules` | Celery beat schedule viewer |
| AlertsView | `/alerts` | Alert list + resolve |
| DossierSettingsView | `/settings` | Per-dossier config |
| NotificationsView | `/notifications` | User notification feed |
