<script setup>
import { computed, onMounted } from 'vue'
import { Search, Wrench, FileSearch, Database, Network, Send, Power, Settings } from '@lucide/vue'
import { useToolsStore } from '../stores/tools'

const store = useToolsStore()

const iconMap = {
  erp: Database,
  integration: Send,
  rag: Network,
  ocr: FileSearch,
  general: Settings,
}

onMounted(() => store.fetchTools())

const tools = computed(() =>
  store.tools.map((t) => ({
    ...t,
    icon: iconMap[t.category] || Settings,
    displayName: t.name,
  }))
)

const toggleStatus = (tool) => {
  tool.status = tool.status === 'active' ? 'inactive' : 'active'
}
</script>

<template>
  <div class="page-container">
    <header class="page-header flex justify-between items-center">
      <div>
        <h1 class="page-title">Danh mục Công cụ Hệ thống (Tools)</h1>
        <p class="page-subtitle">Quản lý các "vũ khí" phần mềm (Plugins) mà AI Agent có thể sử dụng để hoàn thành tác vụ</p>
      </div>
      <button class="btn btn-primary"><Wrench size="16"/> Tích hợp Công cụ mới</button>
    </header>

    <div class="tools-layout glass-panel">
      <div class="toolbar flex justify-between items-center">
        <div class="search-box">
          <Search size="16" class="search-icon" />
          <input type="text" placeholder="Tìm kiếm công cụ..." class="search-input" />
        </div>
        <div class="filters flex gap-2">
          <select class="filter-select"><option>Tất cả trạng thái</option><option>Đang hoạt động</option></select>
        </div>
      </div>

      <div class="tools-grid">
        <div v-for="tool in tools" :key="tool.id" class="tool-card glass-panel">
          <div class="tool-header flex justify-between items-start">
            <div class="tool-icon-wrapper" :class="tool.status">
              <component :is="tool.icon" size="24" />
            </div>
            <div class="tool-status-badge" :class="tool.status">
              {{ tool.status === 'active' ? 'Hoạt động' : tool.status === 'maintenance' ? 'Bảo trì' : 'Đã tắt' }}
            </div>
          </div>
          
          <h3 class="tool-name">{{ tool.displayName }}</h3>
          <p class="tool-desc">{{ tool.description }}</p>
          <p v-if="tool.usageCount" class="text-xs text-muted">Đã gọi {{ tool.usageCount }} lần</p>
          
          <div class="tool-footer flex justify-between items-center">
            <button class="btn btn-outline" @click="toggleStatus(tool)">
              <Power size="14"/> Bật / Tắt
            </button>
            <button class="btn btn-link">Xem tài liệu API</button>
          </div>
          
          <div v-if="tool.lastUsedAt" class="integration-settings mt-4 pt-4 border-t border-gray-200">
            <span class="text-xs text-muted">Lần gọi gần nhất: {{ new Date(tool.lastUsedAt).toLocaleString('vi-VN') }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mt-4 { margin-top: 1rem; }
.pt-4 { padding-top: 1rem; }
.border-t { border-top: 1px solid var(--color-border); }
.text-sm { font-size: 0.875rem; }
.font-semibold { font-weight: 600; }
.mb-2 { margin-bottom: 0.5rem; }
.text-xs { font-size: 0.75rem; }
.text-muted { color: var(--color-text-secondary); }
.code-font { font-family: monospace; }
.bg-gray-100 { background-color: rgba(0,0,0,0.05); }
[data-theme='dark'] .bg-gray-100 { background-color: rgba(255,255,255,0.05); }
.p-1 { padding: 0.25rem; }
.rounded { border-radius: 4px; }
.config-row { display: flex; justify-content: space-between; align-items: center; }
.mt-1 { margin-top: 0.25rem; }
.page-container { padding: 2rem; max-width: 1400px; margin: 0 auto; }
.page-header { margin-bottom: 2rem; }
.page-title { font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; }
.page-subtitle { color: var(--color-text-secondary); }

.tools-layout {
  padding: 1.5rem;
}

.toolbar {
  margin-bottom: 2rem;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}
.search-icon {
  position: absolute;
  left: 1rem;
  color: var(--color-text-secondary);
}
.search-input {
  padding: 0.6rem 1rem 0.6rem 2.5rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-base);
  color: var(--color-text-primary);
  font-family: inherit;
  width: 350px;
  outline: none;
  transition: border-color 0.2s;
}
.search-input:focus { border-color: var(--color-primary); }
.filter-select {
  padding: 0.6rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-base);
  color: var(--color-text-primary);
  font-family: inherit;
  outline: none;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.tool-card {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s, box-shadow 0.2s;
}
.tool-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.1);
}

.tool-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}
.tool-icon-wrapper.active { background: rgba(0, 86, 179, 0.1); color: var(--color-primary); }
[data-theme='dark'] .tool-icon-wrapper.active { background: rgba(59, 130, 246, 0.2); }
.tool-icon-wrapper.maintenance { background: rgba(245, 158, 11, 0.1); color: var(--color-warning); }
.tool-icon-wrapper.inactive { background: rgba(100, 116, 139, 0.1); color: var(--color-text-secondary); }

.tool-status-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
}
.tool-status-badge.active { background: rgba(16, 185, 129, 0.1); color: var(--color-success); }
.tool-status-badge.maintenance { background: rgba(245, 158, 11, 0.1); color: var(--color-warning); }
.tool-status-badge.inactive { background: rgba(100, 116, 139, 0.1); color: var(--color-text-secondary); }

.tool-name {
  font-size: 1.15rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--color-text-primary);
}

.tool-desc {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  line-height: 1.5;
  margin-bottom: 1.5rem;
  flex: 1;
}

.tool-footer {
  border-top: 1px solid var(--color-border);
  padding-top: 1rem;
  margin-top: auto;
}

.btn-link {
  background: none;
  border: none;
  color: var(--color-primary);
  font-weight: 500;
  cursor: pointer;
  font-size: 0.9rem;
}
.btn-link:hover { text-decoration: underline; }
</style>
