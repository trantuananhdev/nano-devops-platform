---
name: hdtv-ai-uiux
description: Áp dụng khi tạo/sửa UI cho dự án "EVNHANOI AI" (hdtv-ai-prototype) — Vue 3 + Vite. Dùng skill này cho mọi việc thêm view mới, component mới, chỉnh layout, style, hoặc khi cần đảm bảo tính nhất quán visual với prototype hiện có.
---

# HDTV AI Prototype — UI/UX Design System Skill

## Bối cảnh & Style Identity
Đây là dashboard quản trị nội bộ (admin/enterprise dashboard) cho EVN Hà Nội, theme: **"Glassmorphism Corporate"** — kết hợp:
- Nền sáng `#f5f7fa` với gradient radial mờ (brand blue + accent orange) ở góc, tạo depth nhẹ.
- Panel kính mờ (`backdrop-filter: blur(12px)`, nền bán trong suốt, border mảnh, shadow lan tỏa rộng) — class dùng chung: `.glass-panel`.
- Bo góc lớn (12-16px), shadow mềm, không viền cứng.
- Sidebar cố định bên trái 260px, nội dung chính scroll riêng.
- Hỗ trợ dark mode qua `[data-theme='dark']` — MỌI màu phải đi qua CSS variable, không hardcode hex.

Khi nhận xét/cải thiện 1 view mới, luôn tự hỏi: "Có dùng `.glass-panel`, color tokens, spacing scale, và pattern hiện có chưa? Có support dark mode chưa?"

## Design Tokens (bắt buộc dùng, không hardcode)
File gốc: `src/assets/main.css`

```css
--color-primary: #0056b3       /* EVN Blue - hành động chính, active state */
--color-primary-light: #3378c2 /* hover của primary */
--color-accent: #f26522        /* EVN Orange - nhấn, AI badge, cảnh báo nhẹ */
--color-bg-base: #f5f7fa        /* nền toàn trang */
--color-bg-panel: rgba(255,255,255,0.85)  /* nền glass panel */
--color-bg-panel-solid: #ffffff
--color-text-primary: #1e293b
--color-text-secondary: #64748b
--color-border: #e2e8f0
--color-shadow: rgba(0,0,0,0.05)
--color-danger: #ef4444   /* risk cao, lỗi, quá hạn */
--color-warning: #f59e0b  /* risk trung bình, chờ xử lý */
--color-success: #10b981  /* đã thông qua, hoàn tất */
--sidebar-width: 260px
--header-height: 64px
```
Dark mode override toàn bộ trong `[data-theme='dark']` — khi thêm token mới PHẢI thêm cả 2 block.

Font: Inter (import từ Google Fonts trong main.css). Heading: `font-weight: 600`.

## Component Patterns chuẩn (tái dùng, không tạo mới tùy tiện)

### 1. Page wrapper
```html
<div class="page-container">
  <header class="page-header">
    <div>
      <h1 class="page-title">...</h1>
      <p class="page-subtitle">...</p>
    </div>
    <!-- action buttons bên phải nếu cần -->
  </header>
  <!-- nội dung -->
</div>
```
```css
.page-container { padding: 2rem; max-width: 1400px; margin: 0 auto; }
.page-header { margin-bottom: 2rem; display:flex; justify-content:space-between; align-items:center; }
.page-title { font-size: 1.75rem; font-weight: 700; color: var(--color-text-primary); margin-bottom: 0.25rem; }
.page-subtitle { color: var(--color-text-secondary); font-size: 0.95rem; }
@media (max-width: 768px) { .page-container { padding: 1rem; } }
```

### 2. Glass panel / card
Mọi block nội dung (card, table, chart, form section) bọc trong `.glass-panel` (định nghĩa global ở main.css, KHÔNG redefine):
```css
.glass-panel {
  background: var(--color-bg-panel);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px 0 var(--color-shadow);
}
```
Card nội dung thường thêm padding riêng (1.5rem) qua class scoped, ví dụ `.stat-card`, `.chart-card`.

### 3. Stat card (số liệu tổng quan)
Icon vuông bo góc 16px (56x56px) + nội dung: label nhỏ secondary + value lớn bold + trend badge pill.
Màu icon theo ngữ nghĩa: `.warning` / `.danger` / `.success` dùng nền `rgba(color, 0.1)` + chữ màu đó.

### 4. Badge / pill (risk, status)
```css
.risk-badge { padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
.risk-badge.high { background: rgba(239,68,68,0.1); color: var(--color-danger); }
.risk-badge.medium { background: rgba(245,158,11,0.1); color: var(--color-warning); }
.risk-badge.low { background: rgba(16,185,129,0.1); color: var(--color-success); }
```
Status dot 8px tròn cùng quy tắc màu. Đây là pattern dùng xuyên suốt — luôn map: Cao/Quá hạn/Lỗi → danger, Trung bình/Đang xử lý → warning, Thấp/Hoàn tất → success.

### 5. Table
`.dossier-table` pattern: border-collapse, padding 1rem, header có nền nhẹ `rgba(0,0,0,0.02)` (dark: `rgba(255,255,255,0.02)`), border-bottom mảnh giữa rows, không border ở row cuối. Wrap trong `.table-responsive { overflow-x: auto; }`.

### 6. Buttons
Dùng class global: `.btn` + `.btn-primary` / `.btn-accent` / `.btn-outline`. Không tự tạo style button mới trừ khi có biến thể thực sự cần (ví dụ icon-only button dùng `.btn-icon`).

### 7. Sidebar nav item
`.nav-item` (icon 20px + label), active state = nền `var(--color-primary)` + chữ trắng + shadow màu primary nhạt.

### 8. Grid responsive
`grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))` cho stat cards; 2 cột (`1fr 1fr`) cho charts, collapse về 1 cột dưới 768px.

## Quy tắc khi viết/sửa code (Vue 3 + Composition API)
1. `<script setup>`, import icon từ `@lucide/vue`, kích thước icon mặc định 20px (sidebar) / 24px (stat icon).
2. Style luôn `<style scoped>`, đặt cuối file. Class naming: kebab-case, theo BEM nhẹ (`.stat-card`, `.stat-icon.warning`).
3. KHÔNG hardcode màu — luôn `var(--color-*)`. Nếu cần màu mới, định nghĩa token ở main.css cho cả light & dark.
4. KHÔNG hardcode breakpoint khác 768px (mobile) / để nhất quán với layout hiện tại (sidebar collapse ở 768px).
5. Mọi text UI là tiếng Việt, giọng hành chính/doanh nghiệp (theo data mẫu: "Tờ trình", "Ban nghiệp vụ", "Thẩm duyệt"...).
6. Khi tạo view mới: route vào `src/router/index.js`, thêm nav item vào `navItems` trong `App.vue` với icon lucide phù hợp.
7. Đây là prototype — chấp nhận mock data dạng `ref([...])` inline trong component, không cần API thật.

## Component Patterns bổ sung

### 9. Empty State
Khi không có data, hiển thị empty state rõ ràng thay vì bảng trống:
```html
<div class="empty-state">
  <component :is="icon" :size="48" class="empty-icon" />
  <p class="empty-title">{{ title }}</p>
  <p class="empty-subtitle">{{ subtitle }}</p>
  <slot name="action" /> <!-- optional CTA button -->
</div>
```
```css
.empty-state { display:flex; flex-direction:column; align-items:center; padding:4rem 2rem;
  color:var(--color-text-secondary); gap:0.75rem; }
.empty-icon { opacity:0.3; color:var(--color-text-secondary); }
.empty-title { font-size:1rem; font-weight:600; color:var(--color-text-primary); margin:0; }
.empty-subtitle { font-size:0.875rem; margin:0; text-align:center; }
```

### 10. Loading Skeleton
Dùng cho stat cards và table rows khi đang fetch API:
```html
<!-- Skeleton stat card -->
<div class="skeleton-card glass-panel">
  <div class="skeleton-block" style="width:48px;height:48px;border-radius:12px"></div>
  <div style="flex:1">
    <div class="skeleton-line" style="width:60%;height:14px"></div>
    <div class="skeleton-line" style="width:40%;height:24px;margin-top:8px"></div>
  </div>
</div>
<!-- Skeleton table row: lặp 5 lần -->
<tr class="skeleton-row"><td colspan="6"><div class="skeleton-line"></div></td></tr>
```
```css
.skeleton-block, .skeleton-line {
  background: linear-gradient(90deg, var(--color-border) 25%, rgba(255,255,255,0.5) 50%, var(--color-border) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
}
.skeleton-line { height: 16px; width: 100%; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
[data-theme='dark'] .skeleton-block,
[data-theme='dark'] .skeleton-line {
  background: linear-gradient(90deg, rgba(255,255,255,0.06) 25%, rgba(255,255,255,0.12) 50%, rgba(255,255,255,0.06) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

### 11. Split Panel Layout (Workspace)
Hai panel cạnh nhau, resize bằng drag handle giữa:
```html
<div class="split-container">
  <div class="split-panel" :style="{ width: leftWidth + '%' }"><!-- PDF viewer --></div>
  <div class="split-divider" @mousedown="startResize"></div>
  <div class="split-panel" style="flex:1"><!-- Chat --></div>
</div>
```
```css
.split-container { display:flex; height:100%; overflow:hidden; }
.split-panel { overflow:auto; min-width:200px; }
.split-divider { width:4px; cursor:col-resize; background:var(--color-border);
  transition:background 0.2s; flex-shrink:0; }
.split-divider:hover, .split-divider.dragging { background:var(--color-primary); }
```
Resize logic (script setup):
```js
const leftWidth = ref(50)
function startResize(e) {
  const startX = e.clientX, startW = leftWidth.value
  const onMove = (e) => { leftWidth.value = Math.min(80, Math.max(20, startW + (e.clientX - startX) / window.innerWidth * 100)) }
  const onUp = () => { document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp) }
  document.addEventListener('mousemove', onMove); document.addEventListener('mouseup', onUp)
}
```

### 12. WebSocket Status Indicator (Sidebar)
Dot nhỏ ở góc sidebar cho biết trạng thái kết nối WS:
```html
<span class="ws-status" :class="wsStatus">{{ wsStatus === 'connected' ? 'Live' : wsStatus === 'connecting' ? '...' : 'Offline' }}</span>
```
```css
.ws-status { font-size:0.7rem; padding:2px 6px; border-radius:8px; font-weight:600; }
.ws-status.connected { background:rgba(16,185,129,0.1); color:var(--color-success); }
.ws-status.connecting { background:rgba(245,158,11,0.1); color:var(--color-warning); }
.ws-status.disconnected { background:rgba(239,68,68,0.1); color:var(--color-danger); }
```

### 13. Toast / Inline Feedback
Sau action (save, resolve, submit), hiển thị feedback ngắn ở góc phải dưới:
```html
<Teleport to="body">
  <div v-if="toast.show" class="toast" :class="toast.type">{{ toast.message }}</div>
</Teleport>
```
```css
.toast { position:fixed; bottom:1.5rem; right:1.5rem; padding:0.75rem 1.25rem;
  border-radius:10px; font-size:0.875rem; font-weight:500; z-index:9999;
  box-shadow:0 4px 16px rgba(0,0,0,0.12); animation: slideUp 0.3s ease; }
.toast.success { background:var(--color-success); color:#fff; }
.toast.error { background:var(--color-danger); color:#fff; }
.toast.warning { background:var(--color-warning); color:#fff; }
@keyframes slideUp { from { transform:translateY(20px); opacity:0; } to { transform:translateY(0); opacity:1; } }
```
Composable dùng chung:
```js
// src/composables/useToast.js
import { ref } from 'vue'
const toast = ref({ show: false, message: '', type: 'success' })
export function useToast() {
  function showToast(message, type = 'success', duration = 3000) {
    toast.value = { show: true, message, type }
    setTimeout(() => { toast.value.show = false }, duration)
  }
  return { toast, showToast }
}
```

---

## Quy trình cải thiện 1 màn hình
1. Đọc file view hiện tại, xác định: có dùng đúng tokens/patterns trên không?
2. Phân loại lệch chuẩn: (a) hardcode màu/spacing, (b) thiếu dark-mode support, (c) không dùng `.glass-panel`/`.page-container`, (d) responsive thiếu breakpoint 768px, (e) badge/status không theo quy ước màu ngữ nghĩa.
3. Sửa theo đúng pattern tương ứng ở trên, giữ nguyên cấu trúc dữ liệu/logic, chỉ chuẩn hóa markup + style.
4. Nếu thêm UI hoàn toàn mới (chưa có pattern tương tự) — thiết kế theo phong cách glass-panel + spacing/radius/shadow nhất quán, rồi đề xuất bổ sung pattern này vào skill nếu sẽ tái dùng.
