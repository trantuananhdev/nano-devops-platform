<script setup>
import { onMounted, ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDossierStore } from '../stores/dossier'
import { getDossierUnits } from '../services/api'
import { Plus, X, Upload, FileText, CheckCircle, AlertCircle } from '@lucide/vue'
import VirtualList from '../components/VirtualList.vue'

const router = useRouter()
const store  = useDossierStore()

// T-40: Row height must match .virtual-row height in CSS below
const ROW_HEIGHT   = 52
// T-40: Visible scroll area — shows ~9 rows before scroll
const TABLE_HEIGHT = 480

// ─── Status Labels ───────────────────────────────────────────────────────
const STATUS_LABELS = {
  'draft': 'Nháp',
  'pending': 'Chờ duyệt',
  'appraising': 'Đang thẩm định',
  'submitted_to_dept': 'Đã trình lên Ban',
  'dept_approved': 'Ban đã duyệt',
  'dept_rejected': 'Ban từ chối',
  'submitted_to_board': 'Đã trình lên HĐTV',
  'board_reviewed': 'HĐTV đã xem xét',
  'approved': 'Đã phê duyệt',
  'rejected': 'Đã từ chối',
  'needs_revision': 'Cần chỉnh sửa',
}

const getStatusBadgeClass = (status) => {
  switch (status) {
    case 'draft':
    case 'needs_revision':
      return 'badge-secondary'
    case 'pending':
    case 'submitted_to_dept':
    case 'submitted_to_board':
      return 'badge-info'
    case 'appraising':
    case 'dept_approved':
    case 'board_reviewed':
      return 'badge-warning'
    case 'dept_rejected':
    case 'rejected':
      return 'badge-danger'
    case 'approved':
      return 'badge-success'
    default:
      return 'badge-secondary'
  }
}

// ─── Filter state ─────────────────────────────────────────────────────────
const unitOptions   = ref([])   // populated from API on mount
const filterUnit    = ref('')
const filterRisk    = ref('')

onMounted(async () => {
  store.fetchDossiers()
  try {
    const { data } = await getDossierUnits()
    unitOptions.value = data
  } catch {
    // Non-critical — filter simply shows no options on error
  }
})

const openDossier = (id) => router.push(`/workspace/${id}`)

// ─── Create Modal state ───────────────────────────────────────────────────
const showModal   = ref(false)
const step        = ref(1)         // 1=metadata  2=PDF upload  3=done
const newDossierId = ref(null)
const form        = reactive({ doc_no: '', title: '', unit: '' })
const formError   = ref('')
const dragActive  = ref(false)
const selectedFile = ref(null)
const uploadError  = ref('')

function openModal() {
  showModal.value    = true
  step.value         = 1
  newDossierId.value = null
  formError.value    = ''
  uploadError.value  = ''
  selectedFile.value = null
  Object.assign(form, { doc_no: '', title: '', unit: '' })
}

function closeModal() {
  showModal.value = false
  if (step.value === 3) store.fetchDossiers()
}

async function submitMeta() {
  formError.value = ''
  if (!form.doc_no.trim() || !form.title.trim() || !form.unit.trim()) {
    formError.value = 'Vui lòng điền đầy đủ thông tin'
    return
  }
  try {
    const result = await store.createNewDossier({
      doc_no: form.doc_no.trim(),
      title:  form.title.trim(),
      unit:   form.unit.trim(),
    })
    newDossierId.value = result.id
    step.value = 2
  } catch (e) {
    formError.value = e.message
  }
}

function onDragOver(e)  { e.preventDefault(); dragActive.value = true }
function onDragLeave()  { dragActive.value = false }
function onDrop(e) {
  e.preventDefault()
  dragActive.value = false
  const file = e.dataTransfer.files[0]
  if (file) handleFileSelect(file)
}
function onFileInput(e) {
  const file = e.target.files[0]
  if (file) handleFileSelect(file)
}
function handleFileSelect(file) {
  if (file.size > 20 * 1024 * 1024) { uploadError.value = 'File vượt quá giới hạn 20MB'; return }
  selectedFile.value = file
  uploadError.value  = ''
}

async function submitUpload() {
  if (!selectedFile.value) { step.value = 3; return }
  uploadError.value = ''
  const result = await store.uploadPdf(newDossierId.value, selectedFile.value)
  if (result?.ok) {
    step.value = 3
  } else {
    uploadError.value = result?.error || 'Upload thất bại'
  }
}

function skipUpload()   { step.value = 3 }
function finishAndOpen() {
  closeModal()
  if (newDossierId.value) router.push(`/workspace/${newDossierId.value}`)
}

const STEPS = ['Thông tin', 'Đính kèm PDF', 'Hoàn tất']
</script>

<template>
  <div class="page-container">
    <header class="page-header flex-between">
      <div>
        <h1 class="page-title">Hòm thư Tờ trình (Inbox)</h1>
        <p class="page-subtitle">Danh sách hồ sơ cần HĐTV thẩm duyệt</p>
      </div>
      <button id="create-dossier-btn" class="btn btn-primary" @click="openModal">
        <Plus :size="16" /> Tạo hồ sơ mới
      </button>
    </header>

    <div class="glass-panel content-panel">
      <div class="toolbar flex-between">
        <div class="search-hint">
          <span class="kbd-hint">Ctrl+K</span> để tìm kiếm nhanh
        </div>
        <div class="flex gap-2">
          <select v-model="filterUnit" class="filter-select">
            <option value="">Tất cả Ban</option>
            <option v-for="u in unitOptions" :key="u" :value="u">{{ u }}</option>
          </select>
          <select v-model="filterRisk" class="filter-select">
            <option value="">Mọi mức rủi ro</option>
            <option value="high">Rủi ro Cao</option>
            <option value="medium">Trung bình</option>
            <option value="low">Thấp</option>
          </select>
        </div>
      </div>

      <div v-if="store.loading && store.dossiers.length === 0" class="p-4 text-muted">Đang tải...</div>

      <!--
        T-38: Virtual scrolling table.
        thead is a real <table> for sticky column headers.
        tbody is replaced by VirtualList to avoid rendering 1000+ DOM nodes.
        CSS custom properties (--col-*) keep thead <th> and virtual-row <span> widths in sync.
      -->
      <div class="table-wrapper">
        <!-- Sticky header -->
        <div class="thead-row" role="row">
          <span class="col-docno th">Số Ký Hiệu</span>
          <span class="col-title th">Trích Yếu Tờ Trình</span>
          <span class="col-unit th">Ban Trình</span>
          <span class="col-date th">Ngày Trình</span>
          <span class="col-risk th">Cảnh báo AI</span>
          <span class="col-status th">Trạng thái</span>
        </div>

        <!-- T-38: Only visible rows are in the DOM -->
        <VirtualList
          :items="filteredDossiers"
          :item-height="ROW_HEIGHT"
          :height="TABLE_HEIGHT"
          key-field="id"
          @scroll-end="store.loadMoreDossiers()"
        >
          <template #default="{ item }">
            <div
              class="virtual-row"
              role="row"
              @click="openDossier(item.id)"
            >
              <span class="col-docno mono">{{ item.docNo }}</span>
              <span class="col-title ellipsis">{{ item.title }}</span>
              <span class="col-unit">{{ item.unit }}</span>
              <span class="col-date muted-sm">{{ item.date }}</span>
              <span class="col-risk">
                    <span v-if="item.risk === 'high'"   class="badge badge-danger">Rủi ro Cao</span>
                    <span v-else-if="item.risk === 'medium'" class="badge badge-warning">Trung bình</span>
                    <span v-else class="badge badge-success">Thấp</span>
                  </span>
                  <span class="col-status">
                    <span :class="['badge', getStatusBadgeClass(item.status)]">
                      {{ STATUS_LABELS[item.status] || item.status }}
                    </span>
                  </span>
            </div>
          </template>
        </VirtualList>

        <!-- Empty state -->
        <div v-if="!store.loading && store.dossiers.length === 0" class="empty-row">
          Chưa có hồ sơ nào. Nhấn "Tạo hồ sơ mới" để bắt đầu.
        </div>
      </div>

      <!-- T-40: Load more button (appears when server has more pages) -->
      <div v-if="store.hasMore" class="load-more-bar">
        <button
          class="btn btn-outline btn-sm"
          :disabled="store.loadingMore"
          @click="store.loadMoreDossiers()"
        >
          <span v-if="store.loadingMore">⏳ Đang tải...</span>
          <span v-else>Tải thêm ({{ store.total - store.dossiers.length }} còn lại)</span>
        </button>
      </div>

      <!-- T-40: Pagination summary -->
      <div v-if="store.total > 0" class="pagination-info">
        Hiển thị {{ store.dossiers.length }} / {{ store.total }} hồ sơ
      </div>
    </div>

    <!-- ─── Create Dossier Modal ──────────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
          <div class="modal-box glass-panel" role="dialog" aria-label="Tạo hồ sơ mới">

            <div class="modal-header">
              <h2 class="modal-title">Tạo Tờ trình mới</h2>
              <button class="modal-close" @click="closeModal"><X :size="18" /></button>
            </div>

            <div class="step-bar">
              <div
                v-for="(s, i) in STEPS"
                :key="i"
                class="step-item"
                :class="{ active: step === i + 1, done: step > i + 1 }"
              >
                <div class="step-circle">{{ step > i + 1 ? '✓' : i + 1 }}</div>
                <span class="step-label">{{ s }}</span>
              </div>
            </div>

            <!-- Step 1: Metadata -->
            <div v-if="step === 1" class="modal-body">
              <div class="form-group">
                <label class="form-label">Ký hiệu Tờ trình <span class="required">*</span></label>
                <input id="input-doc-no" v-model="form.doc_no" class="form-input"
                  placeholder="VD: 001/TTr-B02" @keydown.enter="submitMeta" />
                <p class="form-hint">Ký hiệu duy nhất, không trùng lặp</p>
              </div>
              <div class="form-group">
                <label class="form-label">Trích yếu nội dung <span class="required">*</span></label>
                <textarea id="input-title" v-model="form.title" class="form-input form-textarea"
                  placeholder="Mô tả ngắn nội dung Tờ trình HĐTV..." rows="3" />
              </div>
              <div class="form-group">
                <label class="form-label">Ban / Đơn vị trình <span class="required">*</span></label>
                <input id="input-unit" v-model="form.unit" class="form-input"
                  placeholder="VD: Ban Kế hoạch (B02)" @keydown.enter="submitMeta" />
              </div>
              <div v-if="formError" class="form-error"><AlertCircle :size="14" /> {{ formError }}</div>
              <div class="modal-actions">
                <button class="btn btn-outline" @click="closeModal">Hủy</button>
                <button id="btn-submit-meta" class="btn btn-primary" :disabled="store.creating" @click="submitMeta">
                  <span v-if="store.creating">⏳ Đang tạo...</span>
                  <span v-else>Tiếp theo →</span>
                </button>
              </div>
            </div>

            <!-- Step 2: PDF upload -->
            <div v-if="step === 2" class="modal-body">
              <p class="step-desc">Đính kèm file PDF Tờ trình (tùy chọn, tối đa 20MB)</p>
              <div
                class="drop-zone"
                :class="{ 'drag-active': dragActive, 'has-file': selectedFile }"
                @dragover="onDragOver" @dragleave="onDragLeave" @drop="onDrop"
              >
                <input id="pdf-file-input" type="file" accept=".pdf,application/pdf"
                  class="file-input-hidden" @change="onFileInput" />
                <div v-if="!selectedFile" class="drop-content">
                  <Upload :size="32" class="drop-icon" />
                  <p class="drop-text">Kéo thả file PDF vào đây hoặc</p>
                  <label for="pdf-file-input" class="btn btn-outline btn-sm">Chọn file</label>
                </div>
                <div v-else class="file-selected">
                  <FileText :size="24" class="file-icon" />
                  <div>
                    <p class="file-name">{{ selectedFile.name }}</p>
                    <p class="file-size">{{ (selectedFile.size / 1024).toFixed(1) }} KB</p>
                  </div>
                  <button class="remove-file" @click="selectedFile = null"><X :size="14" /></button>
                </div>
              </div>
              <div v-if="uploadError" class="form-error"><AlertCircle :size="14" /> {{ uploadError }}</div>
              <div class="modal-actions">
                <button class="btn btn-outline" @click="skipUpload">Bỏ qua</button>
                <button id="btn-upload-pdf" class="btn btn-primary" :disabled="store.uploading" @click="submitUpload">
                  <span v-if="store.uploading">⏳ Đang upload...</span>
                  <span v-else>{{ selectedFile ? 'Upload PDF' : 'Tiếp tục' }}</span>
                </button>
              </div>
            </div>

            <!-- Step 3: Done -->
            <div v-if="step === 3" class="modal-body modal-done">
              <CheckCircle :size="48" class="done-icon" />
              <h3 class="done-title">Tờ trình đã được tạo!</h3>
              <p class="done-desc">Hồ sơ <strong>{{ form.doc_no }}</strong> đã sẵn sàng để thẩm định AI.</p>
              <div v-if="store.uploadResult?.ok" class="upload-success">
                <CheckCircle :size="14" /> PDF đã upload thành công lên MinIO
              </div>
              <div class="modal-actions modal-actions--center">
                <button class="btn btn-outline" @click="closeModal">Đóng</button>
                <button id="btn-go-workspace" class="btn btn-primary" @click="finishAndOpen">Mở Workspace →</button>
              </div>
            </div>

          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
/* ─── Layout ─────────────────────────────────────────────────────────────── */
.page-container { padding: 2rem; }
.page-title     { font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; }
.page-subtitle  { color: var(--color-text-secondary); }
.content-panel  { margin-top: 1.5rem; padding: 1.5rem; }
.toolbar        { margin-bottom: 1.5rem; }
.flex-between   { display: flex; justify-content: space-between; align-items: center; }
.flex           { display: flex; }
.gap-2          { gap: 0.5rem; }

.search-hint { font-size: 0.85rem; color: var(--color-text-secondary); }
.kbd-hint {
  display: inline-block;
  background: var(--color-surface-2, rgba(0,0,0,0.07));
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 0.1rem 0.4rem;
  font-family: monospace;
  font-size: 0.78rem;
}
.filter-select {
  padding: 0.5rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-primary);
}

/* ─── Table (T-38: thead + VirtualList body) ────────────────────────────── */
/*
 * Column widths are shared between the sticky header row (.thead-row)
 * and the virtual data rows (.virtual-row) via CSS custom properties.
 * Changing --col-* here updates both automatically.
 */
.table-wrapper {
  --col-docno:  130px;
  --col-unit:   150px;
  --col-date:   110px;
  --col-risk:   130px;
  --col-status: 140px;
  /* col-title: flex 1 (remaining space) */
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

/* Shared column classes — used by both .thead-row and .virtual-row */
.col-docno  { flex: 0 0 var(--col-docno);  min-width: 0; }
.col-title  { flex: 1 1 auto;              min-width: 0; }
.col-unit   { flex: 0 0 var(--col-unit);   min-width: 0; }
.col-date   { flex: 0 0 var(--col-date);   min-width: 0; }
.col-risk   { flex: 0 0 var(--col-risk);   min-width: 0; }
.col-status { flex: 0 0 var(--col-status); min-width: 0; }

/* Sticky header row */
.thead-row {
  display: flex;
  align-items: center;
  padding: 0 1rem;
  height: 40px;
  background: var(--color-surface-2, rgba(0,0,0,0.02));
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 1;
}
[data-theme='dark'] .thead-row { background: rgba(255,255,255,0.02); }
.thead-row .th {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
  padding-right: 0.5rem;
}

/* T-38: Virtual data row — flex layout mirrors thead-row */
.virtual-row {
  display: flex;
  align-items: center;
  height: 52px;
  padding: 0 1rem;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  transition: background 0.15s;
  box-sizing: border-box;
  font-size: 0.92rem;
  color: var(--color-text-primary);
  gap: 0;
}
.virtual-row:last-child   { border-bottom: none; }
.virtual-row:hover        { background: rgba(0, 86, 179, 0.04); }
[data-theme='dark'] .virtual-row:hover { background: rgba(59, 130, 246, 0.08); }

/* Per-column modifiers */
.mono     { font-family: monospace; font-size: 0.9rem; font-weight: 500; color: var(--color-primary); }
.ellipsis { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; padding-right: 1rem; }
.muted-sm { color: var(--color-text-secondary); font-size: 0.85rem; }

/* Empty state */
.empty-row {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 3rem 1rem;
  font-size: 0.9rem;
}

/* T-40: Load more + pagination */
.load-more-bar {
  display: flex;
  justify-content: center;
  padding: 1rem;
  border-top: 1px solid var(--color-border);
}
.pagination-info {
  text-align: right;
  font-size: 0.78rem;
  color: var(--color-text-secondary);
  padding: 0.4rem 1rem 0;
}

/* Badges */
.badge        { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.badge-danger  { background: rgba(239,68,68,0.15);  color: #ef4444; }
.badge-warning { background: rgba(245,158,11,0.15); color: #f59e0b; }
.badge-success { background: rgba(34,197,94,0.15);  color: #22c55e; }
.badge-info { background: rgba(59,130,246,0.15); color: #3b82f6; }
.badge-secondary { background: rgba(107,114,128,0.15); color: #6b7280; }

/* ─── Modal ──────────────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.55);
  backdrop-filter: blur(4px);
  z-index: 8000;
  display: flex; align-items: center; justify-content: center;
  padding: 1rem;
}
.modal-box    { width: 100%; max-width: 520px; border-radius: 16px; overflow: hidden; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--color-border); }
.modal-title  { font-size: 1.1rem; font-weight: 700; margin: 0; }
.modal-close  { background: none; border: none; cursor: pointer; color: var(--color-text-secondary); display: flex; transition: color 0.15s; }
.modal-close:hover { color: var(--color-text-primary); }

.step-bar {
  display: flex;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface-2, rgba(0,0,0,0.02));
}
.step-item { display: flex; align-items: center; gap: 0.4rem; flex: 1; color: var(--color-text-secondary); font-size: 0.8rem; }
.step-item.active { color: var(--color-primary); }
.step-item.done   { color: #22c55e; }
.step-circle {
  width: 22px; height: 22px; border-radius: 50%;
  border: 1.5px solid currentColor;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.72rem; font-weight: 700; flex-shrink: 0;
}
.step-item.active .step-circle { background: var(--color-primary); color: white; border-color: var(--color-primary); }
.step-item.done   .step-circle { background: #22c55e; color: white; border-color: #22c55e; }
.step-label { font-weight: 500; }

.modal-body   { padding: 1.5rem; }
.step-desc    { color: var(--color-text-secondary); margin-bottom: 1.25rem; font-size: 0.9rem; }
.form-group   { margin-bottom: 1rem; }
.form-label   { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem; }
.required     { color: #ef4444; }
.form-input {
  width: 100%; padding: 0.6rem 0.875rem; border-radius: 8px;
  border: 1px solid var(--color-border); background: transparent;
  color: var(--color-text-primary); font-size: 0.9rem;
  transition: border-color 0.15s; box-sizing: border-box;
}
.form-input:focus    { outline: none; border-color: var(--color-primary); }
.form-textarea       { resize: vertical; min-height: 72px; font-family: inherit; }
.form-hint           { font-size: 0.75rem; color: var(--color-text-secondary); margin-top: 0.25rem; }
.form-error          { display: flex; align-items: center; gap: 0.4rem; color: #ef4444; font-size: 0.83rem; margin-top: 0.5rem; }
.p-4.text-muted      { padding: 1rem; color: var(--color-text-secondary); }

.drop-zone {
  border: 2px dashed var(--color-border); border-radius: 12px;
  padding: 2rem; text-align: center; transition: all 0.2s;
  position: relative; min-height: 140px;
  display: flex; align-items: center; justify-content: center;
}
.drop-zone.drag-active { border-color: var(--color-primary); background: rgba(0, 86, 179, 0.04); }
.drop-zone.has-file    { border-style: solid; border-color: #22c55e; }
.file-input-hidden { position: absolute; inset: 0; opacity: 0; cursor: pointer; z-index: 0; }
.drop-content   { display: flex; flex-direction: column; align-items: center; gap: 0.75rem; }
.drop-icon      { color: var(--color-text-secondary); }
.drop-text      { color: var(--color-text-secondary); font-size: 0.9rem; margin: 0; }
.btn-sm         { padding: 0.35rem 0.875rem; font-size: 0.85rem; z-index: 1; position: relative; }
.file-selected  { display: flex; align-items: center; gap: 0.75rem; width: 100%; }
.file-icon      { color: var(--color-primary); flex-shrink: 0; }
.file-name      { font-weight: 600; font-size: 0.9rem; margin: 0; word-break: break-all; }
.file-size      { font-size: 0.78rem; color: var(--color-text-secondary); margin: 0.1rem 0 0; }
.remove-file    { margin-left: auto; background: none; border: none; cursor: pointer; color: var(--color-text-secondary); display: flex; }

.modal-actions          { display: flex; gap: 0.75rem; justify-content: flex-end; margin-top: 1.25rem; }
.modal-actions--center  { justify-content: center; }

.modal-done  { text-align: center; }
.done-icon   { color: #22c55e; margin: 0 auto 1rem; display: block; }
.done-title  { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem; }
.done-desc   { color: var(--color-text-secondary); margin-bottom: 1rem; }
.upload-success {
  display: inline-flex; align-items: center; gap: 0.4rem;
  font-size: 0.82rem; color: #22c55e; margin-bottom: 1rem;
}

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.18s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>
