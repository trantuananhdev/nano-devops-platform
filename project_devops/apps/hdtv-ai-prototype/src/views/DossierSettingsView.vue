<script setup>
import { computed, onMounted, ref } from 'vue'
import { FileCog, CheckSquare, FileText, FileBadge, FileSignature, Plus, Search, Trash2, Upload, Edit } from '@lucide/vue'
import { useSettingsStore } from '../stores/settings'
import { useDossierStore } from '../stores/dossier'

const settingsStore = useSettingsStore()
const dossierStore = useDossierStore()
const activeTab = ref('checklist')
const activeTypeId = ref(null)

const dossierTypes = computed(() =>
  dossierStore.dossiers.map((d, i) => ({
    id: d.id,
    name: d.title,
    active: activeTypeId.value ? activeTypeId.value === d.id : i === 0,
  }))
)

const checklists = computed(() => settingsStore.checklists)

onMounted(async () => {
  await dossierStore.fetchDossiers()
  await settingsStore.fetchChecklistTemplate()
  activeTypeId.value = dossierStore.dossiers[0]?.id || null
})

const selectType = (id) => {
  activeTypeId.value = id
}
</script>

<template>
  <div class="page-container">
    <header class="page-header flex justify-between items-center">
      <div>
        <h1 class="page-title flex items-center gap-2">
          <FileCog class="text-primary" size="28"/>
          Cấu hình Loại Tờ trình (Dossier Settings)
        </h1>
        <p class="page-subtitle">Thiết lập bộ tiêu chuẩn thẩm định và biểu mẫu chuẩn cho từng nhóm Tờ trình</p>
      </div>
      <button class="btn btn-primary"><Plus size="16"/> Thêm Loại Tờ trình mới</button>
    </header>

    <div class="split-layout">
      <!-- Left Sidebar: Dossier Types -->
      <aside class="type-sidebar glass-panel">
        <div class="sidebar-search">
          <div class="search-box w-full">
            <Search size="14" class="search-icon" />
            <input type="text" placeholder="Tìm loại tờ trình..." class="search-input w-full" />
          </div>
        </div>
        
        <ul class="type-list">
          <li 
            v-for="type in dossierTypes" 
            :key="type.id" 
            class="type-item"
            :class="{ active: type.active }"
            @click="selectType(type.id)"
          >
            <FileText size="16" class="item-icon"/>
            <span class="item-name">{{ type.name }}</span>
          </li>
        </ul>
      </aside>

      <!-- Right Main Panel -->
      <main class="settings-main glass-panel">
        <!-- Tabs -->
        <div class="tabs-header">
          <button class="tab-btn" :class="{ active: activeTab === 'checklist' }" @click="activeTab = 'checklist'">
            <CheckSquare size="16"/> Checklist Thẩm định
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'input_form' }" @click="activeTab = 'input_form'">
            <FileText size="16"/> Biểu mẫu Tờ trình
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'output_report' }" @click="activeTab = 'output_report'">
            <FileBadge size="16"/> Mẫu Báo cáo Thẩm định
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'output_resolution' }" @click="activeTab = 'output_resolution'">
            <FileSignature size="16"/> Mẫu Nghị quyết
          </button>
        </div>

        <!-- Tab Content -->
        <div class="tab-content">
          <!-- 1. CHECKLIST -->
          <div v-if="activeTab === 'checklist'" class="tab-pane">
            <div class="flex justify-between items-center mb-4">
              <div>
                <h3 class="pane-title">Danh mục Thẩm định bắt buộc</h3>
                <p class="text-sm text-muted">AI sẽ dựa vào checklist này để tự động tick kiểm tra các tiêu chí của hồ sơ.</p>
              </div>
              <button class="btn btn-outline-primary btn-sm"><Plus size="14"/> Thêm Tiêu chí</button>
            </div>
            
            <div class="checklist-items">
              <div v-for="item in checklists" :key="item.id" class="check-item flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <input type="checkbox" checked disabled class="check-input"/>
                  <span class="font-medium">{{ item.text }}</span>
                  <span v-if="item.type === 'auto'" class="badge badge-auto">AI Tự động</span>
                  <span v-else class="badge badge-manual">Thủ công</span>
                  <span v-if="item.isRequired" class="text-danger text-xs font-bold">* Bắt buộc</span>
                </div>
                <div class="flex gap-2">
                  <button class="btn-icon" title="Sửa"><Edit size="14"/></button>
                  <button class="btn-icon text-danger" title="Xóa"><Trash2 size="14"/></button>
                </div>
              </div>
            </div>
          </div>

          <!-- 2. BIỂU MẪU TỜ TRÌNH (INPUT) -->
          <div v-if="activeTab === 'input_form'" class="tab-pane">
            <div class="mb-4">
              <h3 class="pane-title">Biểu mẫu Tờ trình chuẩn (Input Template)</h3>
              <p class="text-sm text-muted">Hệ thống sẽ đối chiếu Tờ trình được tải lên với biểu mẫu gốc này để phát hiện sai lệch về thể thức văn bản.</p>
            </div>
            
            <div class="upload-area">
              <Upload size="32" class="text-primary mb-2 opacity-70"/>
              <div class="font-medium mb-1">Kéo thả file biểu mẫu (.docx, .pdf) vào đây</div>
              <div class="text-xs text-muted mb-3">Hoặc</div>
              <button class="btn btn-outline-primary btn-sm">Tải file lên</button>
            </div>
            
            <div class="current-file glass-panel mt-4 flex items-center justify-between">
              <div class="flex items-center gap-3">
                <FileText size="24" class="text-primary"/>
                <div>
                  <div class="font-medium">Mau_To_Trinh_Dau_Tu_2026.docx</div>
                  <div class="text-xs text-muted">Cập nhật lần cuối: 15/05/2026 bởi Quản trị viên</div>
                </div>
              </div>
              <div class="flex gap-2">
                <button class="btn btn-outline btn-sm">Xem trước</button>
                <button class="btn-icon text-danger"><Trash2 size="16"/></button>
              </div>
            </div>
          </div>

          <!-- 3. MẪU BÁO CÁO THẨM ĐỊNH (OUTPUT 1) -->
          <div v-if="activeTab === 'output_report'" class="tab-pane">
            <div class="mb-4">
              <h3 class="pane-title">Mẫu Báo cáo Thẩm định (Output Template)</h3>
              <p class="text-sm text-muted">Định dạng file Word để AI tự động điền các kết quả phân tích, thông số tài chính và sinh ra Báo cáo cuối cùng.</p>
            </div>
            
            <div class="editor-header flex justify-between items-center mb-2">
              <div class="flex gap-2">
                <select class="form-select text-sm"><option>Tiêu đề 1</option><option>Đoạn văn</option></select>
                <button class="btn-icon"><strong>B</strong></button>
                <button class="btn-icon"><em>I</em></button>
                <button class="btn-icon"><u>U</u></button>
              </div>
              <button class="btn btn-outline-primary btn-sm">Chèn Data Field { }</button>
            </div>
            
            <div class="template-editor code-font">
              <p class="text-center font-bold">BÁO CÁO THẨM ĐỊNH</p>
              <p class="text-center">V/v: {Tieu_De_To_Trinh}</p>
              <br>
              <p><strong>1. Thông tin chung:</strong></p>
              <p>- Đơn vị trình: {Don_Vi_Trinh}</p>
              <p>- Tổng mức đầu tư đề nghị: {Tong_Muc_Dau_Tu} VNĐ</p>
              <br>
              <p><strong>2. Kết quả kiểm tra của AI:</strong></p>
              <p>- Đối soát với Kế hoạch ERP: {Ket_Qua_ERP}</p>
              <p>- Đối soát Pháp lý: {Ket_Qua_Phap_Ly}</p>
              <p>- Các rủi ro phát hiện: {Danh_Sach_Canh_Bao}</p>
              <br>
              <p><strong>3. Đề xuất của Ban Thẩm định:</strong></p>
              <p>{De_Xuat_Hoi_Dong}</p>
            </div>
            <div class="mt-4 flex justify-end">
              <button class="btn btn-primary">Lưu Biểu mẫu</button>
            </div>
          </div>

          <!-- 4. MẪU NGHỊ QUYẾT (OUTPUT 2) -->
          <div v-if="activeTab === 'output_resolution'" class="tab-pane">
            <div class="mb-4">
              <h3 class="pane-title">Mẫu Nghị quyết HĐTV (Resolution Template)</h3>
              <p class="text-sm text-muted">Sau khi Tờ trình được thông qua, AI sẽ tự động sinh văn bản Nghị quyết dựa trên mẫu này để Lãnh đạo ký ban hành ngay lập tức.</p>
            </div>
            
             <div class="editor-header flex justify-between items-center mb-2">
              <div class="flex gap-2">
                <select class="form-select text-sm"><option>Tiêu đề 1</option><option>Đoạn văn</option></select>
                <button class="btn-icon"><strong>B</strong></button>
                <button class="btn-icon"><em>I</em></button>
                <button class="btn-icon"><u>U</u></button>
              </div>
              <button class="btn btn-outline-primary btn-sm">Chèn Data Field { }</button>
            </div>
            
            <div class="template-editor code-font">
              <p class="text-center font-bold">NGHỊ QUYẾT</p>
              <p class="text-center font-bold">HỘI ĐỒNG THÀNH VIÊN TỔNG CÔNG TY ĐIỆN LỰC TP HÀ NỘI</p>
              <p class="text-center">V/v: Phê duyệt {Tieu_De_Du_An}</p>
              <br>
              <p><strong>ĐIỀU 1:</strong> Phê duyệt {Tieu_De_Du_An} theo đề nghị của {Don_Vi_Trinh} tại Tờ trình số {So_To_Trinh}.</p>
              <p><strong>ĐIỀU 2:</strong> Tổng mức đầu tư dự án không vượt quá: {Tong_Muc_Dau_Tu_Duyet} VNĐ.</p>
              <p><strong>ĐIỀU 3:</strong> Giao Giám đốc {Don_Vi_Thuc_Hien} chịu trách nhiệm triển khai dự án tuân thủ đúng quy định hiện hành của Nhà nước và EVN.</p>
              <br>
              <p class="text-right"><strong>TM. HỘI ĐỒNG THÀNH VIÊN</strong></p>
              <p class="text-right"><strong>CHỦ TỊCH</strong></p>
            </div>
            <div class="mt-4 flex justify-end">
              <button class="btn btn-primary">Lưu Biểu mẫu</button>
            </div>
          </div>

        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.page-container { padding: 2rem; max-width: 1400px; margin: 0 auto; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
.page-header { margin-bottom: 1.5rem; flex-shrink: 0; }
.page-title { font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; }
.page-subtitle { color: var(--color-text-secondary); }
.text-primary { color: var(--color-primary); }
.text-danger { color: var(--color-danger); }
.text-muted { color: var(--color-text-secondary); }

.split-layout { display: flex; gap: 1.5rem; flex: 1; min-height: 0; margin-bottom: 1rem; }

/* Left Sidebar */
.type-sidebar { width: 300px; display: flex; flex-direction: column; border-radius: 12px; overflow: hidden; }
.sidebar-search { padding: 1rem; border-bottom: 1px solid var(--color-border); }
.search-box { position: relative; display: flex; align-items: center; }
.search-icon { position: absolute; left: 0.75rem; color: var(--color-text-secondary); }
.search-input { padding: 0.5rem 1rem 0.5rem 2rem; border: 1px solid var(--color-border); border-radius: 8px; background: var(--color-bg-base); color: var(--color-text-primary); font-family: inherit; outline: none; transition: border-color 0.2s; font-size: 0.85rem; }
.search-input:focus { border-color: var(--color-primary); }
.w-full { width: 100%; }

.type-list { flex: 1; overflow-y: auto; list-style: none; padding: 0; margin: 0; }
.type-item { display: flex; align-items: center; gap: 0.75rem; padding: 1rem; border-bottom: 1px solid var(--color-border); cursor: pointer; transition: background 0.2s; }
.type-item:hover { background: rgba(0,0,0,0.02); }
[data-theme='dark'] .type-item:hover { background: rgba(255,255,255,0.02); }
.type-item.active { background: rgba(0, 86, 179, 0.05); border-left: 4px solid var(--color-primary); }
[data-theme='dark'] .type-item.active { background: rgba(59, 130, 246, 0.1); }
.item-icon { color: var(--color-text-secondary); flex-shrink: 0; }
.type-item.active .item-icon { color: var(--color-primary); }
.item-name { font-size: 0.9rem; font-weight: 500; line-height: 1.4; }
.type-item.active .item-name { color: var(--color-primary); font-weight: 600; }
[data-theme='dark'] .type-item.active .item-name { color: var(--color-primary-light); }

/* Right Panel */
.settings-main { flex: 1; display: flex; flex-direction: column; border-radius: 12px; overflow: hidden; }

.tabs-header { display: flex; border-bottom: 1px solid var(--color-border); background: rgba(0,0,0,0.01); }
[data-theme='dark'] .tabs-header { background: rgba(255,255,255,0.01); }
.tab-btn { flex: 1; display: flex; align-items: center; justify-content: center; gap: 0.5rem; padding: 1rem; border: none; background: transparent; cursor: pointer; color: var(--color-text-secondary); font-weight: 600; font-size: 0.9rem; border-bottom: 2px solid transparent; transition: all 0.2s; }
.tab-btn:hover { color: var(--color-primary); background: rgba(0,0,0,0.02); }
[data-theme='dark'] .tab-btn:hover { background: rgba(255,255,255,0.02); }
.tab-btn.active { color: var(--color-primary); border-bottom-color: var(--color-primary); background: var(--color-bg-base); }

.tab-content { flex: 1; overflow-y: auto; padding: 2rem; }
.pane-title { font-size: 1.2rem; font-weight: 600; margin-bottom: 0.25rem; }

/* Checklist Styling */
.checklist-items { display: flex; flex-direction: column; gap: 0.75rem; }
.check-item { padding: 1rem 1.25rem; border: 1px solid var(--color-border); border-radius: 8px; background: var(--color-bg-base); transition: box-shadow 0.2s; }
.check-item:hover { box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
.check-input { width: 16px; height: 16px; accent-color: var(--color-primary); cursor: pointer; }
.font-medium { font-weight: 500; font-size: 0.95rem; }
.badge { padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; }
.badge-auto { background: rgba(16, 185, 129, 0.1); color: var(--color-success); }
.badge-manual { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
.text-xs { font-size: 0.75rem; }
.font-bold { font-weight: 700; }

/* Upload Area */
.upload-area { border: 2px dashed var(--color-border); border-radius: 12px; padding: 3rem 2rem; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(0,0,0,0.01); transition: all 0.2s; }
.upload-area:hover { border-color: var(--color-primary); background: rgba(0, 86, 179, 0.02); }
[data-theme='dark'] .upload-area:hover { background: rgba(59, 130, 246, 0.05); }
.opacity-70 { opacity: 0.7; }
.current-file { padding: 1rem 1.5rem; border-radius: 8px; border: 1px solid var(--color-primary); }

/* Editor */
.editor-header { padding: 0.5rem; background: var(--color-bg-base); border: 1px solid var(--color-border); border-radius: 8px 8px 0 0; border-bottom: none; }
.form-select { border: 1px solid var(--color-border); border-radius: 4px; padding: 0.2rem 0.5rem; background: transparent; color: var(--color-text-primary); }
.template-editor { padding: 2rem; min-height: 300px; border: 1px solid var(--color-border); border-radius: 0 0 8px 8px; background: var(--color-bg-base); color: var(--color-text-primary); line-height: 1.6; }
.code-font { font-family: 'Consolas', 'Courier New', Courier, monospace; font-size: 0.9rem; }
.text-center { text-align: center; }
.text-right { text-align: right; }

.btn-sm { padding: 0.4rem 0.75rem; font-size: 0.85rem; }
.btn-outline-primary { border: 1px solid var(--color-primary); color: var(--color-primary); background: transparent; cursor: pointer; border-radius: 6px; display: flex; align-items: center; gap: 0.4rem;}
.btn-outline-primary:hover { background: rgba(0, 86, 179, 0.1); }
[data-theme='dark'] .btn-outline-primary:hover { background: rgba(59, 130, 246, 0.15); }
.btn-outline { border: 1px solid var(--color-border); background: transparent; color: var(--color-text-primary); cursor: pointer; border-radius: 6px;}
.btn-outline:hover { background: rgba(0,0,0,0.05); }
[data-theme='dark'] .btn-outline:hover { background: rgba(255,255,255,0.1); }
</style>
