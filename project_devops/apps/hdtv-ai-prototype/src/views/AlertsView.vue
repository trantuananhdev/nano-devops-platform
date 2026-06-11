<script setup>
import { ref, computed, onMounted } from 'vue'
import { AlertTriangle, ShieldAlert, AlertCircle, CheckCircle, Filter, Search, FileText, ArrowUpRight, User, MessageSquare, ChevronDown, ChevronUp, Send } from '@lucide/vue'
import { useAlertsStore } from '../stores/alerts'

const searchQuery = ref('')
const selectedSeverity = ref('all')
const selectedStatus = ref('open')
const expandedAlerts = ref(new Set())
const newComments = ref({})
const assignedUsers = ref({})

// Mock users for assignment
const availableUsers = [
  { id: 'u1', name: 'Nguyễn Văn A', role: 'Trưởng Ban Kế hoạch' },
  { id: 'u2', name: 'Trần Thị B', role: 'Thành viên Hội đồng' },
  { id: 'u3', name: 'Lê Văn C', role: 'Chủ nhiệm Ban Tài chính' },
]

const alertsStore = useAlertsStore()

onMounted(() => alertsStore.fetchAlerts())

const alerts = computed(() => alertsStore.alerts.length ? alertsStore.alerts : [
  {
    id: 'AL-1042',
    title: 'Vượt Tổng mức đầu tư dự án (2 Tỷ VNĐ)',
    severity: 'high',
    source: 'ERP Integration',
    dossier: 'Tờ trình phê duyệt dự toán Cáp ngầm Ba Đình',
    dossierId: 'TT-124',
    date: '10 phút trước',
    status: 'open',
    description: 'AI phát hiện giá trị đề nghị phê duyệt (52 tỷ) vượt quá giới hạn Tổng mức đầu tư được ghi nhận trên hệ thống Oracle ERP (50 tỷ).',
    comments: [
      { id: 'c1', author: 'Nguyễn Văn A', text: 'Đã kiểm tra, đề nghị điều chỉnh lại giá trị dự toán', time: '5 phút trước' }
    ],
    assignedTo: null,
  },
  {
    id: 'AL-1041',
    title: 'Căn cứ pháp lý hết hiệu lực',
    severity: 'medium',
    source: 'Legal GraphRAG',
    dossier: 'Tờ trình mua sắm vật tư PCTT',
    dossierId: 'TT-128',
    date: '2 giờ trước',
    status: 'open',
    description: 'Quyết định 14/QĐ-EVN được trích dẫn làm căn cứ pháp lý đã bị thay thế bởi Quyết định 22/QĐ-EVN có hiệu lực từ ngày 01/01/2026.',
    comments: [],
    assignedTo: 'u2',
  },
  {
    id: 'AL-1040',
    title: 'Phát hiện tồn kho vật tư tương đương',
    severity: 'medium',
    source: 'PMIS & ERP',
    dossier: 'Tờ trình xin mua mới MBA 250kVA',
    dossierId: 'TT-130',
    date: '5 giờ trước',
    status: 'resolved',
    description: 'AI đối soát ERP và phát hiện trong Kho Công ty vẫn còn 2 MBA 250kVA chưa xuất, đề nghị không mua mới để tránh lãng phí.',
    comments: [
      { id: 'c2', author: 'Trần Thị B', text: 'Đã xác nhận, quyết định không mua mới', time: '3 giờ trước' }
    ],
    assignedTo: 'u2',
  },
  {
    id: 'AL-1039',
    title: 'Biên bản thiếu chữ ký Ban Tài chính',
    severity: 'low',
    source: 'OCR Engine',
    dossier: 'Tờ trình phê duyệt Quyết toán',
    dossierId: 'TT-119',
    date: '1 ngày trước',
    status: 'open',
    description: 'Bản scan Biên bản họp Hội đồng chưa có chữ ký tươi hoặc chữ ký số của đại diện Ban Tài chính Kế toán.',
    comments: [],
    assignedTo: null,
  }
])

const filteredAlerts = computed(() => {
  return alerts.value.filter(alert => {
    const matchSearch = alert.title.toLowerCase().includes(searchQuery.value.toLowerCase()) || alert.dossier.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchSeverity = selectedSeverity.value === 'all' || alert.severity === selectedSeverity.value
    const matchStatus = selectedStatus.value === 'all' || alert.status === selectedStatus.value
    return matchSearch && matchSeverity && matchStatus
  })
})

const resolveAlert = async (id) => {
  const alert = alerts.value.find(a => a.id === id)
  if (alert?.rawId) {
    await alertsStore.resolve(alert.rawId)
  } else if (alert) {
    alert.status = 'resolved'
  }
}

const toggleExpand = (alertId) => {
  if (expandedAlerts.value.has(alertId)) {
    expandedAlerts.value.delete(alertId)
  } else {
    expandedAlerts.value.add(alertId)
  }
  expandedAlerts.value = new Set(expandedAlerts.value) // Force reactivity
}

const addComment = (alertId) => {
  const text = newComments.value[alertId]?.trim()
  if (!text) return
  const alert = alerts.value.find(a => a.id === alertId)
  if (alert) {
    if (!alert.comments) alert.comments = []
    alert.comments.push({
      id: `c-${Date.now()}`,
      author: 'Bạn',
      text: text,
      time: 'Vừa xong',
    })
    newComments.value[alertId] = ''
  }
}

const assignUser = (alertId, userId) => {
  assignedUsers.value[alertId] = userId
  const alert = alerts.value.find(a => a.id === alertId)
  if (alert) {
    alert.assignedTo = userId
  }
}

const getAssignedUserName = (userId) => {
  return availableUsers.find(u => u.id === userId)?.name || 'Chưa phân công'
}
</script>

<template>
  <div class="page-container">
    <header class="page-header flex justify-between items-center">
      <div>
        <h1 class="page-title flex items-center gap-2">
          <AlertTriangle class="text-danger" size="28"/>
          Danh sách Cảnh báo Tự động (AI Alerts)
        </h1>
        <p class="page-subtitle">Quản lý tập trung các rủi ro, vi phạm do AI đối soát từ Tờ trình và Hệ thống vệ tinh</p>
      </div>
      <div class="flex gap-2">
        <div class="search-box">
          <Search size="16" class="search-icon" />
          <input type="text" v-model="searchQuery" placeholder="Tìm kiếm cảnh báo..." class="search-input" />
        </div>
      </div>
    </header>

    <div class="filters-bar glass-panel flex gap-4 items-center">
      <div class="flex items-center gap-2 text-sm font-medium text-muted">
        <Filter size="16"/> Lọc theo:
      </div>
      
      <select v-model="selectedSeverity" class="filter-select">
        <option value="all">Tất cả mức độ</option>
        <option value="high">Rủi ro Cao (Đỏ)</option>
        <option value="medium">Rủi ro Trung bình (Vàng)</option>
        <option value="low">Rủi ro Thấp (Xanh)</option>
      </select>

      <select v-model="selectedStatus" class="filter-select">
        <option value="all">Tất cả trạng thái</option>
        <option value="open">Chưa xử lý (Open)</option>
        <option value="resolved">Đã xử lý (Resolved)</option>
      </select>
      
      <div class="ml-auto text-sm font-medium">
        Tìm thấy: <span class="text-primary">{{ filteredAlerts.length }}</span> cảnh báo
      </div>
    </div>

    <div class="alerts-list">
      <div 
        v-for="alert in filteredAlerts" 
        :key="alert.id" 
        class="alert-card glass-panel"
        :class="['severity-' + alert.severity, alert.status === 'resolved' ? 'is-resolved' : '']"
      >
        <div class="alert-icon-col">
          <ShieldAlert v-if="alert.severity === 'high'" size="28" class="icon-high"/>
          <AlertTriangle v-else-if="alert.severity === 'medium'" size="28" class="icon-medium"/>
          <AlertCircle v-else size="28" class="icon-low"/>
        </div>
        
        <div class="alert-content-col">
          <div class="flex justify-between items-start mb-2">
            <h3 class="alert-title">{{ alert.title }}</h3>
            <span class="alert-id">{{ alert.id }}</span>
          </div>
          <p class="alert-desc">{{ alert.description }}</p>
          
          <div class="alert-meta flex gap-4 mt-3">
            <div class="meta-item">
              <span class="label">Nguồn phát hiện:</span>
              <span class="value font-medium">{{ alert.source }}</span>
            </div>
            <div class="meta-item">
              <span class="label">Tờ trình liên quan:</span>
              <span class="value text-primary flex items-center gap-1 cursor-pointer hover-underline">
                <FileText size="12"/> {{ alert.dossierId }} - {{ alert.dossier }}
              </span>
            </div>
            <div class="meta-item" v-if="alert.assignedTo">
              <span class="label">Phân công cho:</span>
              <span class="value font-medium flex items-center gap-1">
                <User size="12"/> {{ getAssignedUserName(alert.assignedTo) }}
              </span>
            </div>
            <div class="meta-item ml-auto">
              <span class="label text-xs">{{ alert.date }}</span>
            </div>
          </div>

          <!-- Expandable Section -->
          <div v-if="expandedAlerts.has(alert.id)" class="alert-details-section">
            <div class="details-grid">
              <!-- Assignment -->
              <div class="detail-block">
                <h4 class="detail-title flex items-center gap-1">
                  <User size="16"/> Phân công xử lý
                </h4>
                <select 
                  v-if="alert.status !== 'resolved'"
                  class="detail-select"
                  :value="alert.assignedTo"
                  @change="assignUser(alert.id, $event.target.value)"
                >
                  <option value="">Chưa phân công</option>
                  <option v-for="u in availableUsers" :key="u.id" :value="u.id">
                    {{ u.name }} ({{ u.role }})
                  </option>
                </select>
                <span v-else class="detail-value">
                  {{ getAssignedUserName(alert.assignedTo) }}
                </span>
              </div>

              <!-- Comments -->
              <div class="detail-block">
                <h4 class="detail-title flex items-center gap-1">
                  <MessageSquare size="16"/> Bình luận & Ghi chú
                  <span class="count-badge">{{ (alert.comments || []).length }}</span>
                </h4>
                <div class="comments-list">
                  <div v-for="comment in alert.comments" :key="comment.id" class="comment-item">
                    <div class="comment-header">
                      <span class="comment-author">{{ comment.author }}</span>
                      <span class="comment-time">{{ comment.time }}</span>
                    </div>
                    <div class="comment-text">{{ comment.text }}</div>
                  </div>
                  <div v-if="!alert.comments || alert.comments.length === 0" class="empty-comments">
                    Chưa có bình luận nào
                  </div>
                </div>
                <div v-if="alert.status !== 'resolved'" class="comment-input-wrapper">
                  <input 
                    v-model="newComments[alert.id]"
                    type="text"
                    placeholder="Thêm bình luận..."
                    class="comment-input"
                    @keyup.enter="addComment(alert.id)"
                  />
                  <button class="send-btn" @click="addComment(alert.id)">
                    <Send size="16"/>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="alert-actions-col">
          <div v-if="alert.status === 'resolved'" class="status-badge resolved flex items-center gap-1">
            <CheckCircle size="14"/> Đã xử lý
          </div>
          <div v-else class="status-badge open">Chưa xử lý</div>
          
          <button 
            v-if="alert.status === 'open'" 
            class="btn btn-outline-success btn-sm w-full mt-3"
            @click="resolveAlert(alert.id)"
          >
            <CheckCircle size="14"/> Xác nhận
          </button>
          <button 
            class="btn btn-link btn-sm w-full mt-1 flex items-center justify-center gap-1"
            @click="toggleExpand(alert.id)"
          >
            {{ expandedAlerts.has(alert.id) ? 'Thu gọn' : 'Xem chi tiết' }}
            <ChevronDown size="14" v-if="!expandedAlerts.has(alert.id)"/>
            <ChevronUp size="14" v-else/>
          </button>
        </div>
      </div>
      
      <div v-if="filteredAlerts.length === 0" class="empty-state glass-panel">
        <CheckCircle size="48" class="text-success mb-3 opacity-50"/>
        <h3>Hệ thống an toàn</h3>
        <p>Không có cảnh báo nào khớp với bộ lọc hiện tại.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container { padding: 2rem; max-width: 1400px; margin: 0 auto; }
.page-header { margin-bottom: 2rem; }
.page-title { font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; }
.page-subtitle { color: var(--color-text-secondary); }
.text-danger { color: var(--color-danger); }
.text-success { color: var(--color-success); }
.text-primary { color: var(--color-primary); }
.text-muted { color: var(--color-text-secondary); }

.search-box { position: relative; display: flex; align-items: center; }
.search-icon { position: absolute; left: 1rem; color: var(--color-text-secondary); }
.search-input { padding: 0.6rem 1rem 0.6rem 2.5rem; border: 1px solid var(--color-border); border-radius: 8px; background: var(--color-bg-base); color: var(--color-text-primary); font-family: inherit; width: 300px; outline: none; transition: border-color 0.2s; }
.search-input:focus { border-color: var(--color-primary); }

.filters-bar {
  padding: 1rem 1.5rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
}
.filter-select {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-base);
  color: var(--color-text-primary);
  font-family: inherit;
  font-size: 0.9rem;
  outline: none;
}
.ml-auto { margin-left: auto; }

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.alert-card {
  display: flex;
  padding: 1.5rem;
  gap: 1.5rem;
  border-left: 4px solid transparent;
  transition: all 0.2s;
}
.alert-card:hover { transform: translateX(4px); box-shadow: 0 8px 20px rgba(0,0,0,0.05); }

/* Severity Styling */
.severity-high { border-left-color: var(--color-danger); }
.severity-medium { border-left-color: #f59e0b; } /* Amber */
.severity-low { border-left-color: var(--color-primary); }

.icon-high { color: var(--color-danger); }
.icon-medium { color: #f59e0b; }
.icon-low { color: var(--color-primary); }

.alert-card.is-resolved {
  opacity: 0.6;
  border-left-color: var(--color-border);
}
.alert-card.is-resolved .alert-icon-col { filter: grayscale(1); opacity: 0.5; }

.alert-icon-col {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: rgba(0,0,0,0.03);
  border-radius: 12px;
  flex-shrink: 0;
}
[data-theme='dark'] .alert-icon-col { background: rgba(255,255,255,0.05); }

.alert-content-col {
  flex: 1;
}
.alert-title { font-size: 1.15rem; font-weight: 600; margin: 0; }
.alert-id { font-family: monospace; font-size: 0.8rem; color: var(--color-text-secondary); background: var(--color-bg-base); padding: 0.1rem 0.4rem; border-radius: 4px; }
.alert-desc { font-size: 0.95rem; color: var(--color-text-secondary); line-height: 1.5; margin-bottom: 0; }

.alert-meta { font-size: 0.85rem; border-top: 1px dashed var(--color-border); padding-top: 0.75rem; }
.meta-item .label { color: var(--color-text-secondary); margin-right: 0.25rem; }
.font-medium { font-weight: 500; }
.cursor-pointer { cursor: pointer; }
.hover-underline:hover { text-decoration: underline; }

.alert-actions-col {
  width: 150px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  border-left: 1px solid var(--color-border);
  padding-left: 1.5rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.status-badge.open { background: rgba(239, 68, 68, 0.1); color: var(--color-danger); }
.status-badge.resolved { background: rgba(16, 185, 129, 0.1); color: var(--color-success); }

.w-full { width: 100%; }
.mt-3 { margin-top: 0.75rem; }
.mt-1 { margin-top: 0.25rem; }
.btn-sm { padding: 0.4rem 0.5rem; font-size: 0.85rem; display: flex; align-items: center; justify-content: center; gap: 0.4rem; }
.btn-outline-success { border: 1px solid var(--color-success); color: var(--color-success); background: transparent; cursor: pointer; border-radius: 6px; }
.btn-outline-success:hover { background: rgba(16, 185, 129, 0.1); }
.btn-link { background: transparent; border: none; color: var(--color-primary); cursor: pointer; }
.btn-link:hover { text-decoration: underline; }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
}
.empty-state h3 { font-size: 1.25rem; margin-bottom: 0.5rem; }
.empty-state p { color: var(--color-text-secondary); }
.mb-3 { margin-bottom: 0.75rem; }
.opacity-50 { opacity: 0.5; }

/* Alert Details Section */
.alert-details-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px dashed var(--color-border);
}

.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.detail-block {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.detail-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-select {
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-base);
  color: var(--color-text-primary);
  font-family: inherit;
  font-size: 0.9rem;
  outline: none;
}

.detail-value {
  padding: 0.6rem 0;
  font-size: 0.9rem;
}

.count-badge {
  background: var(--color-primary);
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  border-radius: 10px;
}

/* Comments */
.comments-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  max-height: 200px;
  overflow-y: auto;
}

.comment-item {
  padding: 0.75rem;
  background: var(--color-bg-base);
  border-radius: 8px;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.comment-author {
  font-size: 0.85rem;
  font-weight: 600;
}

.comment-time {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.comment-text {
  font-size: 0.9rem;
  color: var(--color-text-primary);
}

.empty-comments {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  font-style: italic;
  padding: 0.5rem 0;
}

.comment-input-wrapper {
  display: flex;
  gap: 0.5rem;
}

.comment-input {
  flex: 1;
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-base);
  color: var(--color-text-primary);
  font-family: inherit;
  font-size: 0.9rem;
  outline: none;
}

.comment-input:focus {
  border-color: var(--color-primary);
}

.send-btn {
  padding: 0 0.75rem;
  border: none;
  background: var(--color-primary);
  color: white;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.send-btn:hover {
  background: #1d4ed8;
}
</style>
