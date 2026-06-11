<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useSearchStore } from '../stores/search'
import { Search, X, Loader, AlertCircle, Clock, Trash2 } from '@lucide/vue'

const router = useRouter()
const searchStore = useSearchStore()

const inputRef = ref(null)
let debounceTimer = null

// Debounced search
function onInput(e) {
  const q = e.target.value
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    searchStore.search(q)
  }, 280)
}

function close() {
  searchStore.open = false
  searchStore.clear()
}

function goToDossier(dossierId) {
  close()
  router.push({ name: 'workspace', query: { dossier: dossierId } })
}

// Search history function
function useHistoryQuery(q) {
  inputRef.value.value = q
  searchStore.search(q)
}

// Keyboard: Ctrl+K to open, Escape to close
function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    searchStore.open = !searchStore.open
    if (searchStore.open) {
      setTimeout(() => inputRef.value?.focus(), 50)
    }
  }
  if (e.key === 'Escape' && searchStore.open) {
    close()
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

const RISK_COLOR = { high: '#ef4444', medium: '#f59e0b', low: '#22c55e' }
const STATUS_LABEL = {
  pending: 'Chờ duyệt',
  appraising: 'Đang thẩm định',
  approved: 'Đã duyệt',
  needs_revision: 'Bổ sung hồ sơ',
}
</script>

<template>
  <!-- Trigger button — rendered in sidebar/header -->
  <button
    v-if="!searchStore.open"
    id="global-search-trigger"
    class="search-trigger"
    @click="searchStore.open = true; $nextTick(() => inputRef?.focus())"
    title="Tìm kiếm (Ctrl+K)"
  >
    <Search :size="16" />
    <span class="search-trigger-label">Tìm kiếm...</span>
    <kbd class="kbd">Ctrl K</kbd>
  </button>

  <!-- Modal overlay -->
  <Teleport to="body">
    <Transition name="search-fade">
      <div v-if="searchStore.open" class="search-overlay" @click.self="close">
        <div class="search-modal glass-panel" role="dialog" aria-label="Tìm kiếm hồ sơ">
          <!-- Input row -->
          <div class="search-input-row">
            <Search :size="18" class="search-icon" />
            <input
              ref="inputRef"
              id="global-search-input"
              class="search-input"
              type="text"
              placeholder="Nhập từ khóa: tên hồ sơ, đơn vị, mã số..."
              autofocus
              @input="onInput"
            />
            <Loader v-if="searchStore.loading" :size="16" class="spin search-loader" />
            <button v-else class="search-close-btn" @click="close"><X :size="16" /></button>
          </div>

          <!-- Degraded warning -->
          <div v-if="searchStore.degraded && !searchStore.loading" class="search-degraded">
            <AlertCircle :size="14" />
            <span>Search engine chưa sẵn sàng — kết quả có thể không đầy đủ</span>
          </div>

          <!-- Results -->
          <div class="search-results" v-if="searchStore.hits.length > 0">
            <div class="results-meta">
              {{ searchStore.estimatedTotal }} kết quả
              <span class="time-badge">{{ searchStore.processingTimeMs }}ms</span>
            </div>
            <ul class="results-list">
              <li
                v-for="hit in searchStore.hits"
                :key="hit.id"
                class="result-item"
                @click="goToDossier(hit.id)"
                tabindex="0"
                @keydown.enter="goToDossier(hit.id)"
              >
                <div class="result-meta-row">
                  <span class="result-doc-no">{{ hit.doc_no }}</span>
                  <span
                    class="result-risk"
                    :style="{ color: RISK_COLOR[hit.risk_level] || 'inherit' }"
                  >● {{ hit.risk_level?.toUpperCase() }}</span>
                </div>
                <!-- Use highlighted title if available, else plain -->
                <div
                  class="result-title"
                  v-html="hit._formatted?.title || hit.title"
                />
                <div class="result-unit">{{ hit.unit }}</div>
                <div class="result-status">{{ STATUS_LABEL[hit.status] || hit.status }}</div>
              </li>
            </ul>
          </div>

          <div v-else-if="searchStore.query && !searchStore.loading" class="search-empty">
            Không tìm thấy kết quả cho "<strong>{{ searchStore.query }}</strong>"
          </div>

          <!-- Search History -->
          <div v-if="!searchStore.query && searchStore.history.length > 0" class="search-history">
            <div class="history-header">
              <span class="history-title">Tìm kiếm gần đây</span>
              <button class="history-clear-btn" @click="searchStore.clearHistory()">
                <Trash2 size="14" />
                Xóa lịch sử
              </button>
            </div>
            <ul class="history-list">
              <li
                v-for="(item, idx) in searchStore.history"
                :key="idx"
                class="history-item"
                @click="useHistoryQuery(item)"
                tabindex="0"
                @keydown.enter="useHistoryQuery(item)"
              >
                <Clock size="16" class="history-icon" />
                <span class="history-text">{{ item }}</span>
              </li>
            </ul>
          </div>

          <div v-else-if="!searchStore.query" class="search-hint">
            Gõ để tìm kiếm hồ sơ theo tên, đơn vị hoặc mã số Tờ trình
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* ─── Trigger button ─── */
.search-trigger {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--color-surface-2, rgba(0,0,0,0.05));
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 0.4rem 0.75rem;
  cursor: pointer;
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  transition: all 0.15s;
  width: 100%;
}
.search-trigger:hover {
  background: var(--color-surface-3, rgba(0,0,0,0.08));
  color: var(--color-text-primary);
}
.search-trigger-label { flex: 1; text-align: left; }
.kbd {
  font-size: 0.7rem;
  background: var(--color-border);
  border-radius: 4px;
  padding: 0.1rem 0.3rem;
  font-family: monospace;
  opacity: 0.7;
}

/* ─── Overlay ─── */
.search-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(4px);
  z-index: 9999;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 10vh;
}

/* ─── Modal ─── */
.search-modal {
  width: 100%;
  max-width: 640px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0,0,0,0.35);
}

/* ─── Input row ─── */
.search-input-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--color-border);
}
.search-icon { color: var(--color-text-secondary); flex-shrink: 0; }
.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 1rem;
  color: var(--color-text-primary);
}
.search-input::placeholder { color: var(--color-text-secondary); }
.search-close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-secondary);
  padding: 0;
  display: flex;
}
.search-loader { color: var(--color-primary); }
.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ─── Degraded ─── */
.search-degraded {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1.25rem;
  font-size: 0.8rem;
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.08);
}

/* ─── Results ─── */
.search-results { max-height: 420px; overflow-y: auto; }
.results-meta {
  padding: 0.6rem 1.25rem;
  font-size: 0.78rem;
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.time-badge {
  background: var(--color-surface-2, rgba(0,0,0,0.06));
  border-radius: 4px;
  padding: 0.1rem 0.4rem;
  font-size: 0.72rem;
}
.results-list { list-style: none; padding: 0; margin: 0; }
.result-item {
  padding: 0.875rem 1.25rem;
  cursor: pointer;
  border-bottom: 1px solid var(--color-border);
  transition: background 0.12s;
}
.result-item:hover, .result-item:focus {
  background: rgba(0, 86, 179, 0.06);
  outline: none;
}
[data-theme='dark'] .result-item:hover { background: rgba(59, 130, 246, 0.1); }

.result-meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.2rem;
}
.result-doc-no { font-size: 0.75rem; font-weight: 600; color: var(--color-primary); font-family: monospace; }
.result-risk { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.03em; }
.result-title { font-weight: 500; margin-bottom: 0.2rem; line-height: 1.4; }
/* Meilisearch highlight */
:deep(mark) { background: rgba(59, 130, 246, 0.2); color: inherit; border-radius: 2px; padding: 0 1px; }
.result-unit { font-size: 0.78rem; color: var(--color-text-secondary); }
.result-status { font-size: 0.75rem; color: var(--color-text-secondary); margin-top: 0.15rem; }

/* ─── Search History ─── */
.search-history {
  padding: 0.6rem 0;
}
.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1.25rem;
  font-size: 0.78rem;
  color: var(--color-text-secondary);
}
.history-title {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.history-clear-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}
.history-clear-btn:hover {
  color: var(--color-danger);
  background: rgba(239, 68, 68, 0.08);
}
.history-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.history-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.25rem;
  cursor: pointer;
  transition: background 0.12s;
}
.history-item:hover, .history-item:focus {
  background: rgba(0, 86, 179, 0.06);
  outline: none;
}
[data-theme='dark'] .history-item:hover { background: rgba(59, 130, 246, 0.1); }
.history-icon {
  color: var(--color-text-secondary);
  flex-shrink: 0;
}
.history-text {
  color: var(--color-text-primary);
  font-size: 0.9rem;
}

/* ─── Empty / Hint ─── */
.search-empty, .search-hint {
  padding: 1.5rem 1.25rem;
  text-align: center;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

/* ─── Transition ─── */
.search-fade-enter-active, .search-fade-leave-active { transition: opacity 0.18s ease; }
.search-fade-enter-from, .search-fade-leave-to { opacity: 0; }
</style>
