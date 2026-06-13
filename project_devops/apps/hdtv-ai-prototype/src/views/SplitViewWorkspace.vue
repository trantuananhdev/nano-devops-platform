<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, CheckCircle2, AlertTriangle, FileCheck, MessageSquare, FileOutput, Share2, FileBadge, Bot, FileText, Files, Info, X, BookOpen, Trash2, UploadCloud, RefreshCw, ThumbsUp, ThumbsDown, History } from '@lucide/vue'
import { useDossierStore } from '../stores/dossier'
import { useAuthStore } from '../stores/auth'
import { createAppraisalSocket } from '../services/ws'
import { getDossierPdfUrl, submitFeedback, getPendingClarifications, answerClarification, transitionDossierStatus, getDossierStatusHistory, getReferenceDocuments, uploadReferenceDocument, deleteReferenceDocument, getDocumentVersions, createDocumentVersion, getAuditLogs } from '../services/api'

const route = useRoute()
const router = useRouter()
const store = useDossierStore()
const authStore = useAuthStore()
const activeTab = ref('ai')
const leftTab = ref('main')

const goBack = () => router.push('/dossiers')

const dossierId = computed(() => route.params.id || '1')
const dossierDetail = ref(null)
const pdfViewUrl = ref(null)
const isLoadingPdf = ref(false)
const isHighRisk = computed(() => dossierDetail.value?.risk_level === 'high' || dossierId.value === '1' || dossierId.value === '3')
const statusHistory = ref([])
const isTransitioning = ref(false)
const referenceDocs = ref([])
const isUploadingRefDoc = ref(false)
const documentVersions = ref([])
const selectedDocVersion = ref(null)
const newDocVersionContent = ref("")
const newDocVersionDescription = ref("")
const isCreatingDocVersion = ref(false)
const auditLogs = ref([])
const selectedAuditLog = ref(null)

// ─── Status Labels and Transitions ───────────────────────────────────────
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

const getAvailableActions = (status, userRole) => {
  const actions = []
  switch (status) {
    case 'draft':
      if (userRole === 'specialist' || userRole === 'admin') {
        actions.push({ action: 'pending', label: 'Gửi chờ duyệt', variant: 'primary' })
        actions.push({ action: 'submitted_to_dept', label: 'Trình lên Ban', variant: 'primary' })
      }
      break
    case 'pending':
      if (userRole === 'specialist' || userRole === 'admin') {
        actions.push({ action: 'appraising', label: 'Bắt đầu thẩm định', variant: 'primary' })
        actions.push({ action: 'submitted_to_dept', label: 'Trình lên Ban', variant: 'primary' })
        actions.push({ action: 'draft', label: 'Hủy chờ duyệt', variant: 'outline' })
      }
      break
    case 'appraising':
      if (userRole === 'specialist' || userRole === 'admin') {
        actions.push({ action: 'pending', label: 'Đưa về chờ', variant: 'outline' })
        actions.push({ action: 'submitted_to_dept', label: 'Trình lên Ban', variant: 'primary' })
        actions.push({ action: 'needs_revision', label: 'Yêu cầu chỉnh sửa', variant: 'outline' })
        actions.push({ action: 'approved', label: 'Phê duyệt', variant: 'success' })
      }
      break
    case 'submitted_to_dept':
      if (userRole === 'dept_head' || userRole === 'admin') {
        actions.push({ action: 'dept_approved', label: 'Ban duyệt', variant: 'primary' })
        actions.push({ action: 'dept_rejected', label: 'Ban từ chối', variant: 'danger' })
        actions.push({ action: 'draft', label: 'Đưa về nháp', variant: 'outline' })
      }
      break
    case 'dept_approved':
      if (userRole === 'dept_head' || userRole === 'admin') {
        actions.push({ action: 'submitted_to_board', label: 'Trình lên HĐTV', variant: 'primary' })
        actions.push({ action: 'draft', label: 'Đưa về nháp', variant: 'outline' })
      }
      break
    case 'dept_rejected':
      if (userRole === 'specialist' || userRole === 'admin') {
        actions.push({ action: 'draft', label: 'Sửa lại', variant: 'primary' })
      }
      break
    case 'submitted_to_board':
      if (userRole === 'hdtv_leader' || userRole === 'admin') {
        actions.push({ action: 'board_reviewed', label: 'HĐTV xem xét', variant: 'primary' })
        actions.push({ action: 'dept_approved', label: 'Đưa về Ban', variant: 'outline' })
      }
      break
    case 'board_reviewed':
      if (userRole === 'hdtv_leader' || userRole === 'admin') {
        actions.push({ action: 'approved', label: 'Phê duyệt cuối', variant: 'success' })
        actions.push({ action: 'rejected', label: 'Từ chối cuối', variant: 'danger' })
        actions.push({ action: 'needs_revision', label: 'Yêu cầu chỉnh sửa', variant: 'outline' })
      }
      break
    case 'needs_revision':
      if (userRole === 'specialist' || userRole === 'admin') {
        actions.push({ action: 'draft', label: 'Sửa lại', variant: 'primary' })
      }
      break
    case 'rejected':
      if (userRole === 'specialist' || userRole === 'admin') {
        actions.push({ action: 'draft', label: 'Sửa lại', variant: 'primary' })
      }
      break
  }
  return actions
}

const handleStatusTransition = async (action) => {
  isTransitioning.value = true
  try {
    await transitionDossierStatus(dossierId.value, {
      new_status: action,
      changed_by: authStore.currentUser?.id,
      comment: null // Can add a comment modal later if needed
    }, authStore.currentUser?.role)
    await loadDossier()
    await loadStatusHistory()
  } catch (err) {
    console.error('Status transition failed:', err)
  } finally {
    isTransitioning.value = false
  }
}

const loadStatusHistory = async () => {
  try {
    const { data } = await getDossierStatusHistory(dossierId.value)
    statusHistory.value = data
  } catch (err) {
    console.error('Failed to load status history:', err)
  }
}

const loadReferenceDocs = async () => {
  try {
    const { data } = await getReferenceDocuments(dossierId.value)
    referenceDocs.value = data
  } catch (err) {
    console.error('Failed to load reference documents:', err)
  }
}

const loadDocumentVersions = async () => {
  try {
    const { data } = await getDocumentVersions(dossierId.value)
    documentVersions.value = data
    if (data.length > 0) {
      selectedDocVersion.value = data[0] // select latest by default
    }
    
    // Map to reportVersions and resolutionVersions
    reportVersions.value = data.map(v => ({
      id: v.id,
      name: `Phiên bản ${v.version_number}`,
      time: new Date(v.created_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
      desc: v.change_description || 'Cập nhật tài liệu'
    }))
    
    resolutionVersions.value = data.map(v => ({
      id: v.id,
      name: `Phiên bản ${v.version_number}`,
      time: new Date(v.created_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
      desc: v.change_description || 'Dự thảo Nghị quyết'
    }))
  } catch (err) {
    console.error('Failed to load document versions:', err)
  }
}

const loadAuditLogs = async () => {
  try {
    const { data } = await getAuditLogs(dossierId.value)
    auditLogs.value = data.items || data
  } catch (err) {
    console.error('Failed to load audit logs:', err)
  }
}

const defaultChecks = [
  { id: 1, label: 'Kiểm tra căn cứ pháp lý', status: 'pass', desc: 'Chờ thẩm định AI...', details: '', tool: 'LegalGraphRAG' },
  { id: 2, label: 'Đối chiếu Tổng mức đầu tư (ERP)', status: 'pass', desc: 'Chờ thẩm định AI...', details: '', tool: 'ErpBudgetCheck' },
  { id: 3, label: 'Kiểm tra Vật tư tồn kho (ERP INV)', status: 'pass', desc: 'Chờ thẩm định AI...', details: '', tool: 'ErpInventoryCheck' },
  { id: 4, label: 'Đối chiếu DOffice', status: 'pass', desc: 'Chờ thẩm định AI...', details: '', tool: 'DOfficeLookup' },
  { id: 5, label: 'Checklist PMIS', status: 'pass', desc: 'Chờ thẩm định AI...', details: '', tool: 'PmisProjectCheck' },
]

const aiChecks = ref([])

function mapChecksFromAppraisal(appraisal) {
  const steps = appraisal.plan_steps || appraisal.checks?.items || []
  aiChecks.value = steps.map((c, i) => ({
    id: i + 1,
    label: c.label || toolLabels[c.tool] || c.tool,
    status: c.status,
    desc: c.desc || 'Chờ thẩm định AI...',
    details: c.details || '',
    tool: c.tool,
  }))
}

async function loadDossier() {
  const data = await store.fetchDossier(dossierId.value)
  dossierDetail.value = data
  pdfViewUrl.value = null
  if (data?.pdf_url) {
    isLoadingPdf.value = true
    try {
      const { data: pdfData } = await getDossierPdfUrl(dossierId.value)
      pdfViewUrl.value = pdfData.pdf_url
    } catch {
      pdfViewUrl.value = null
    } finally {
      isLoadingPdf.value = false
    }
  }
  if (data?.appraisal) {
    mapChecksFromAppraisal(data.appraisal)
  } else if (data?.latest_appraisal) {
    mapChecksFromAppraisal(data.latest_appraisal)
  } else {
    aiChecks.value = []
    feedbackSubmitted.value = null
    feedbackComment.value = ''
  }
  await loadStatusHistory()
  await loadReferenceDocs()
  await loadDocumentVersions()
  await loadAuditLogs()
}

let wsHandle = null
const toolLabels = {
  'LegalGraphRAG': 'Kiểm tra căn cứ pháp lý',
  'ErpBudgetCheck': 'Đối chiếu Tổng mức đầu tư (ERP)',
  'ErpInventoryCheck': 'Kiểm tra Vật tư tồn kho (ERP INV)',
  'DOfficeLookup': 'Đối chiếu DOffice',
  'PmisProjectCheck': 'Checklist PMIS'
}

function updateCheckFromTool(toolName, result) {
  const checkIndex = aiChecks.value.findIndex(c => c.tool === toolName)
  if (checkIndex !== -1) {
    const check = aiChecks.value[checkIndex]
    const templates = {
      'LegalGraphRAG': { passKey: (o) => true, descPass: 'Đã đính kèm văn bản, còn hiệu lực.', descFail: 'Thiếu căn cứ pháp lý.' },
      'ErpBudgetCheck': { passKey: (o) => !o.exceeded, descPass: 'Nằm trong hạn mức an toàn.', descFail: 'Vượt quá ngân sách đã phê duyệt.' },
      'ErpInventoryCheck': { passKey: (o) => !o.waste_warning, descPass: 'Không có vật tư tồn đọng.', descFail: 'Phát hiện vật tư tồn kho — cảnh báo lãng phí.' },
      'DOfficeLookup': { passKey: (o) => o.signed, descPass: 'Hồ sơ đã đăng ký và ký.', descFail: 'Hồ sơ chưa đủ chữ ký.' },
      'PmisProjectCheck': { passKey: (o) => o.on_schedule, descPass: 'Dự án đúng tiến độ.', descFail: 'Dự án trễ tiến độ.' }
    }
    const tpl = templates[toolName]
    const passed = tpl ? tpl.passKey(result) : true
    check.status = passed ? 'pass' : 'fail'
    check.desc = tpl ? (passed ? tpl.descPass : tpl.descFail) : 'Hoàn thành'
    check.details = JSON.stringify(result, null, 2)
  }
}

const showRevisionBanner = ref(false)
const revisionBannerDetails = ref(null)

const WS_BASE = import.meta.env.VITE_WS_BASE_URL || `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}`
let ws = null
let reconnectCount = 0
const maxReconnectRetries = 3
const reconnectDelays = [2000, 5000, 10000]

function connectWebSocket() {
  if (ws) {
    try {
      ws.close()
    } catch (e) {}
  }

  const url = `${WS_BASE}/ws/appraisal/${dossierId.value}`
  ws = new WebSocket(url)

  ws.onopen = () => {
    console.log('WS connection opened')
    reconnectCount = 0
  }

  ws.onmessage = (event) => {
    try {
      const evt = JSON.parse(event.data)
      if (evt.type === 'snapshot') {
        if (evt.latest_plan_steps) {
          aiChecks.value = evt.latest_plan_steps.map((step, i) => ({
            id: i + 1,
            label: toolLabels[step.tool] || step.tool,
            status: step.status || 'pending',
            desc: step.desc || 'Chờ thẩm định AI...',
            details: step.details || '',
            tool: step.tool
          }))
        }
        if (evt.completed) {
          loadDossier()
        }
      } else if (evt.type === 'task_started' || evt.type === 'started') {
        showRevisionBanner.value = false
        if (aiChecks.value.length > 0) {
          aiChecks.value = aiChecks.value.map(c => ({ ...c, status: 'pending', desc: 'Đang xử lý...' }))
        }
      } else if (evt.type === 'plan_created') {
        if (evt.steps) {
          aiChecks.value = evt.steps.map((step, i) => ({
            id: i + 1,
            label: toolLabels[step.tool] || step.tool,
            status: 'pending',
            desc: 'Chờ thẩm định AI...',
            details: '',
            tool: step.tool
          }))
        }
      } else if (evt.type === 'tool_executing') {
        const checkIndex = aiChecks.value.findIndex(c => c.tool === evt.tool_name)
        if (checkIndex !== -1) {
          aiChecks.value[checkIndex].desc = 'Đang chạy...'
        }
      } else if (evt.type === 'tool_result') {
        updateCheckFromTool(evt.tool_name, evt.outputs)
      } else if (evt.type === 'clarification_needed') {
        clarificationModal.value = {
          id: evt.clarification_id,
          question: evt.question,
          options: evt.options || [],
          trigger_type: evt.trigger_type,
        }
      } else if (evt.type === 'clarification_answered') {
        clarificationModal.value = null
      } else if (evt.type === 'revision_requested') {
        showRevisionBanner.value = true
        revisionBannerDetails.value = evt.details || {}
      } else if (evt.type === 'completed') {
        loadDossier()
      }
    } catch (e) {
      console.error('Error parsing WS message', e)
    }
  }

  ws.onclose = () => {
    console.log('WS connection closed')
    if (reconnectCount < maxReconnectRetries) {
      const delay = reconnectDelays[reconnectCount]
      reconnectCount++
      console.log(`WS reconnecting in ${delay}ms (attempt ${reconnectCount}/${maxReconnectRetries})...`)
      setTimeout(() => {
        loadDossier()
        connectWebSocket()
      }, delay)
    } else {
      console.warn('WS reconnect failed after max retries.')
    }
  }

  ws.onerror = (err) => {
    console.error('WS error', err)
    ws.close()
  }
}

onMounted(async () => {
  await loadDossier()
  await loadPendingClarification()
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})

const selectedCheck = ref(null)

const messages = ref([
  { id: 1, sender: 'Đ/c Nguyễn Văn A (Trưởng ban KH)', time: '10:00', content: 'Tôi đã xem báo cáo rủi ro. Đề nghị Ban QLDA giải trình rõ nguyên nhân tăng chi phí dự phòng 2 tỷ so với ERP.', isMe: false },
  { id: 2, sender: 'Đ/c Trần Thị B (Thành viên HĐTV)', time: '10:15', content: 'Nhất trí với ý kiến của Ban KH. Yêu cầu điều chỉnh lại tổng mức đầu tư về đúng 50 tỷ trước khi ra Nghị quyết.', isMe: false }
])
const newMessage = ref('')

const sendMessage = () => {
  if(!newMessage.value) return
  messages.value.push({ id: Date.now(), sender: 'Tôi (Lãnh đạo HĐTV)', time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }), content: newMessage.value, isMe: true })
  newMessage.value = ''
}

const clarifyMessages = ref([
  { id: 1, sender: 'Lãnh đạo HĐTV', time: '10:05', content: 'Chi tiết khoản chênh lệch 2 tỷ là từ hạng mục nào?', isMe: true },
  { id: 2, sender: 'Trợ lý AI', time: '10:05', content: 'Thưa sếp, khoản chênh 2 tỷ phát sinh do Ban Kế hoạch đã áp dụng đơn giá cáp ngầm của Quý 1/2026 (cao hơn 15% so với đơn giá Quý 4/2025 ghi nhận trong ERP).', isAI: true }
])
const newClarifyMsg = ref('')

const sendClarifyMsg = () => {
  if(!newClarifyMsg.value) return
  clarifyMessages.value.push({ id: Date.now(), sender: 'Lãnh đạo HĐTV', time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }), content: newClarifyMsg.value, isMe: true })
  const query = newClarifyMsg.value
  newClarifyMsg.value = ''
  
  setTimeout(() => {
    clarifyMessages.value.push({ id: Date.now(), sender: 'Trợ lý AI', time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }), content: `Tôi đang phân tích câu hỏi: "${query}". Xin chờ một lát...`, isAI: true })
  }, 1000)
}

const reportVersions = ref([])

const resolutionVersions = ref([])

const removeRefDoc = async (id) => {
  try {
    await deleteReferenceDocument(dossierId.value, id)
    await loadReferenceDocs()
  } catch (err) {
    console.error('Failed to remove reference document:', err)
  }
}
const addRefDoc = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  isUploadingRefDoc.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    await uploadReferenceDocument(dossierId.value, formData, authStore.currentUser?.id)
    await loadReferenceDocs()
  } catch (err) {
    console.error('Failed to upload reference document:', err)
  } finally {
    isUploadingRefDoc.value = false
  }
}
const handleFileSelect = (event) => {
  addRefDoc(event)
  event.target.value = '' // Reset input
}

const handleCreateDocVersion = async () => {
  if (!newDocVersionContent.trim()) return
  isCreatingDocVersion.value = true
  try {
    await createDocumentVersion(
      dossierId.value,
      {
        content: newDocVersionContent,
        content_type: 'text/plain',
        change_description: newDocVersionDescription || 'Tạo phiên bản mới',
      },
      authStore.currentUser?.id
    )
    newDocVersionContent.value = ''
    newDocVersionDescription.value = ''
    await loadDocumentVersions()
  } catch (err) {
    console.error('Failed to create document version:', err)
  } finally {
    isCreatingDocVersion.value = false
  }
}

const feedbackComment = ref('')
const feedbackSubmitted = ref(null)
const isSubmittingFeedback = ref(false)

const clarificationModal = ref(null)
const isAnsweringClarification = ref(false)

async function loadPendingClarification() {
  try {
    const { data } = await getPendingClarifications({ dossier_id: Number(dossierId.value) })
    if (data?.length) clarificationModal.value = data[0]
  } catch {
    /* API may be unavailable in static demo */
  }
}

async function submitClarificationAnswer(optionId) {
  if (!clarificationModal.value || isAnsweringClarification.value) return
  isAnsweringClarification.value = true
  try {
    await answerClarification(clarificationModal.value.id, { answer_id: optionId })
    clarificationModal.value = null
  } catch (err) {
    console.error('Clarification answer failed', err)
  } finally {
    isAnsweringClarification.value = false
  }
}

async function sendFeedback(type) {
  if (!dossierDetail.value?.appraisal || isSubmittingFeedback.value) return
  isSubmittingFeedback.value = true
  try {
    await submitFeedback(dossierId.value, {
      feedback_type: type,
      comment: feedbackComment.value.trim() || null,
      user_id: 1,
      appraisal_result_id: dossierDetail.value.appraisal.id,
    })
    feedbackSubmitted.value = type
  } catch (err) {
    console.error('Feedback submit failed', err)
  } finally {
    isSubmittingFeedback.value = false
  }
}

const isRerunning = ref(false)
const rerunAppraisal = async () => {
  if (isRerunning.value) return
  isRerunning.value = true
  try {
    await store.startAppraisal(dossierId.value)
  } finally {
    setTimeout(() => { isRerunning.value = false }, 2000)
  }
}

const refMessages = ref([
  { id: 1, sender: 'Trợ lý AI', time: '10:00', content: 'Tôi sẽ dựa vào các tài liệu nguồn bạn tải lên để đối soát. Bạn có muốn tôi tập trung kiểm tra vào điều khoản nào cụ thể không?', isAI: true }
])
const newRefMsg = ref('')
const sendRefMsg = () => {
  if(!newRefMsg.value) return
  refMessages.value.push({ id: Date.now(), sender: 'Lãnh đạo HĐTV', time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }), content: newRefMsg.value, isMe: true })
  newRefMsg.value = ''
  setTimeout(() => {
    refMessages.value.push({ id: Date.now(), sender: 'Trợ lý AI', time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }), content: 'Đã rõ! Tôi sẽ cập nhật tiêu chí và ưu tiên đối chiếu tập trung vào phần mục tiêu bạn vừa nêu.', isAI: true })
  }, 1000)
}
</script>

<template>
  <div class="workspace-layout">
    <!-- Header -->
    <header class="ws-header glass-panel">
      <button class="btn-icon" @click="goBack"><ArrowLeft /></button>
      <div class="header-info">
        <h2 class="doc-title">{{ dossierDetail?.title || `Tờ trình ${dossierDetail?.doc_no || 'N/A'}` }}</h2>
        <div class="tags">
          <span v-if="dossierDetail?.risk_level === 'high'" class="badge warning">Rủi ro cao</span>
          <span v-else-if="dossierDetail?.risk_level === 'medium'" class="badge info">Rủi ro trung bình</span>
          <span v-else class="badge-success">Rủi ro thấp</span>
          <span :class="['badge', getStatusBadgeClass(dossierDetail?.status)]">
            {{ STATUS_LABELS[dossierDetail?.status] || dossierDetail?.status }}
          </span>
        </div>
      </div>
      <div class="header-actions">
        <button 
          v-for="action in getAvailableActions(dossierDetail?.status, authStore.currentUser?.role)" 
          :key="action.action"
          :class="['btn', action.variant === 'outline' ? 'btn-outline' : '', action.variant === 'success' ? 'btn-success' : '', action.variant === 'danger' ? 'btn-danger' : '', !action.variant || action.variant === 'primary' ? 'btn-primary' : '']"
          @click="handleStatusTransition(action.action)"
          :disabled="isTransitioning"
        >
          {{ isTransitioning ? 'Đang xử lý...' : action.label }}
        </button>
      </div>
    </header>

    <div class="ws-content">
      <!-- Left: PDF Viewer Mock -->
      <div class="ws-left glass-panel">
        <div class="doc-tabs">
          <button class="tab-btn" :class="{ active: leftTab === 'main' }" @click="leftTab = 'main'">
            <FileText size="16"/> Tờ trình
          </button>
          <button class="tab-btn" :class="{ active: leftTab === 'appendix' }" @click="leftTab = 'appendix'">
            <Files size="16"/> Phụ lục (2)
          </button>
          <button class="tab-btn" :class="{ active: leftTab === 'reference' }" @click="leftTab = 'reference'">
            <BookOpen size="16"/> Tài liệu Khác
          </button>
          <button class="tab-btn" :class="{ active: leftTab === 'versions' }" @click="leftTab = 'versions'">
            <History size="16"/> Phiên bản
          </button>
          <button class="tab-btn" :class="{ active: leftTab === 'report' }" @click="leftTab = 'report'">
            <FileBadge size="16"/> Báo cáo Thẩm định
          </button>
          <button class="tab-btn" :class="{ active: leftTab === 'resolution' }" @click="leftTab = 'resolution'">
            <FileOutput size="16"/> Nghị quyết
          </button>
        </div>

        <div class="pdf-toolbar">
          <span v-if="leftTab === 'main'">Tờ trình bản gốc (PDF)</span>
          <span v-else-if="leftTab === 'report'">Báo cáo Thẩm định (Dự thảo)</span>
          <span v-else-if="leftTab === 'resolution'">Nghị quyết HĐTV (Dự thảo)</span>
          <span v-else-if="leftTab === 'reference'">Nguồn dữ liệu tham khảo cho AI</span>
          <span v-else-if="leftTab === 'versions'">Quản lý phiên bản tài liệu</span>
          <div v-else-if="leftTab === 'appendix'" class="flex items-center gap-2">
            <span>Chọn Phụ lục:</span>
            <select class="form-select text-sm">
              <option>PL01: Bảng tổng hợp chi phí</option>
              <option>PL02: Báo giá thiết bị</option>
            </select>
          </div>
          <div class="zoom-controls">
            <button class="btn-icon">-</button>
            <span>100%</span>
            <button class="btn-icon">+</button>
          </div>
        </div>
        
        <div class="pdf-viewer">
          <!-- Tờ trình -->
          <div v-if="leftTab === 'main' && isLoadingPdf" class="pdf-loading">
            <div class="loading-spinner"></div>
            <p class="loading-text">Đang tải PDF...</p>
          </div>
          <div v-else-if="leftTab === 'main' && pdfViewUrl" class="pdf-embed-wrap">
            <iframe :src="pdfViewUrl" class="pdf-embed" title="Tờ trình PDF" />
          </div>
          <div v-else-if="leftTab === 'main'" class="pdf-page">
            <div class="pdf-header text-center">
              <h3>TỔNG CÔNG TY ĐIỆN LỰC TP HÀ NỘI</h3>
              <h4>TỜ TRÌNH</h4>
            </div>
            <p><strong>V/v:</strong> {{ dossierDetail?.title || 'Phê duyệt kế hoạch đấu thầu dự án cáp ngầm.' }}</p>
            <p><strong>Kính gửi:</strong> Hội đồng thành viên</p>
            <br>
            <p>Căn cứ Quyết định 143/QĐ-HĐTV ngày 15/05/2026...</p>
            <p>Nay Ban Kế hoạch trình HĐTV phê duyệt tổng chi phí là <mark class="highlight-warn">52.000.000.000 VNĐ</mark>.</p>
            <p v-if="dossierDetail?.pdf_url" class="text-muted text-sm mt-4">PDF đã tải lên — đang chờ presigned URL từ MinIO.</p>
          </div>

          <!-- Phụ lục -->
          <div v-if="leftTab === 'appendix'" class="pdf-page">
            <div class="pdf-header text-center">
              <h3>PHỤ LỤC 01</h3>
              <h4>BẢNG TỔNG HỢP CHI PHÍ</h4>
            </div>
            <table class="mock-table mt-4 w-full">
              <thead>
                <tr><th>STT</th><th>Hạng mục</th><th>Chi phí (VNĐ)</th></tr>
              </thead>
              <tbody>
                <tr><td>1</td><td>Chi phí xây dựng</td><td>30.000.000.000</td></tr>
                <tr><td>2</td><td>Chi phí thiết bị</td><td>15.000.000.000</td></tr>
                <tr><td>3</td><td>Chi phí dự phòng</td><td><mark class="highlight-warn">7.000.000.000</mark></td></tr>
                <tr><td colspan="2" class="text-right"><strong>Tổng cộng</strong></td><td><strong>52.000.000.000</strong></td></tr>
              </tbody>
            </table>
          </div>

          <!-- Tài liệu Khác (Reference Documents for AI) -->
          <div v-if="leftTab === 'reference'" class="ref-page w-full" style="padding: 2rem;">
            
            <div class="glass-panel" style="padding: 1.5rem; margin-bottom: 2rem;">
              <h3 class="mb-4 text-primary flex items-center gap-2"><UploadCloud size="20"/> Quản lý Tài liệu Nguồn</h3>
              <p class="text-muted text-sm mb-4">Các tài liệu tải lên tại đây sẽ được AI sử dụng làm căn cứ pháp lý bổ sung để thẩm định hồ sơ này.</p>
              
              <div class="ref-list">
                <div v-for="doc in referenceDocs" :key="doc.id" class="ref-item flex items-center justify-between p-3 border-b border-border">
                  <div class="flex items-center gap-3">
                    <FileText size="18" class="text-primary"/>
                    <div>
                      <div class="font-medium">{{ doc.file_name }}</div>
                      <div class="text-xs text-muted">{{ doc.file_size ? (doc.file_size / (1024 * 1024)).toFixed(1) + ' MB' : 'N/A' }}</div>
                    </div>
                  </div>
                  <button class="btn-icon text-danger" @click="removeRefDoc(doc.id)" title="Xóa tài liệu"><Trash2 size="16"/></button>
                </div>
              </div>

              <div class="flex items-center justify-between mt-4">
                <label class="btn btn-outline flex-center gap-2 cursor-pointer">
                  <UploadCloud size="16"/>
                  {{ isUploadingRefDoc ? 'Đang tải lên...' : 'Tải thêm tài liệu' }}
                  <input 
                    type="file" 
                    class="hidden" 
                    @change="handleFileSelect" 
                    :disabled="isUploadingRefDoc"
                    multiple
                  />
                </label>
              </div>
            </div>

          </div>

          <!-- Phiên bản tài liệu -->
          <div v-if="leftTab === 'versions'" class="versions-page w-full" style="padding: 2rem;">
            
            <div class="glass-panel" style="padding: 1.5rem; margin-bottom: 2rem;">
              <h3 class="mb-4 text-primary flex items-center gap-2"><History size="20"/> Tạo phiên bản mới</h3>
              <div class="form-group">
                <label class="form-label">Mô tả thay đổi</label>
                <input 
                  type="text" 
                  class="form-input" 
                  placeholder="Mô tả ngắn gọn về thay đổi..." 
                  v-model="newDocVersionDescription"
                />
              </div>
              <div class="form-group mt-3">
                <label class="form-label">Nội dung</label>
                <textarea 
                  class="form-input" 
                  rows="10" 
                  placeholder="Nhập nội dung tài liệu..." 
                  v-model="newDocVersionContent"
                ></textarea>
              </div>
              <button 
                class="btn btn-primary flex-center gap-2 mt-4" 
                @click="handleCreateDocVersion" 
                :disabled="isCreatingDocVersion"
              >
                <UploadCloud size="16"/>
                {{ isCreatingDocVersion ? 'Đang tạo...' : 'Tạo phiên bản' }}
              </button>
            </div>

            <div class="glass-panel" style="padding: 1.5rem;">
              <h3 class="mb-4 text-primary flex items-center gap-2"><History size="20"/> Lịch sử phiên bản</h3>
              <div class="versions-list">
                <div 
                  v-for="version in documentVersions" 
                  :key="version.id" 
                  class="version-item p-4 border-b border-border cursor-pointer"
                  :class="{ 'border-l-4 border-l-primary': selectedDocVersion?.id === version.id }"
                  @click="selectedDocVersion = version"
                >
                  <div class="flex items-center justify-between">
                    <div>
                      <div class="font-medium">Phiên bản {{ version.version_number }}</div>
                      <div class="text-xs text-muted">
                        {{ new Date(version.created_at).toLocaleString('vi-VN') }}
                        {{ version.change_description ? ` — ${version.change_description}` : '' }}
                      </div>
                    </div>
                  </div>
                </div>
                <div v-if="documentVersions.length === 0" class="text-muted text-center py-8">
                  Chưa có phiên bản nào được tạo.
                </div>
              </div>
              <div v-if="selectedDocVersion" class="mt-4 p-4 bg-gray-50 rounded-lg">
                <h4 class="mb-2 text-primary">Nội dung phiên bản {{ selectedDocVersion.version_number }}</h4>
                <p class="text-sm text-muted mb-2">
                  {{ new Date(selectedDocVersion.created_at).toLocaleString('vi-VN') }}
                </p>
                <p class="whitespace-pre-wrap">{{ selectedDocVersion.content || '(Không có nội dung)' }}</p>
              </div>
            </div>
          </div>

          <!-- Báo cáo thẩm định -->
          <div v-if="leftTab === 'report'" class="pdf-page">
            <div class="pdf-header text-center">
              <h3>TỔNG CÔNG TY ĐIỆN LỰC TP HÀ NỘI</h3>
              <h4>BÁO CÁO THẨM ĐỊNH</h4>
            </div>
            <p><strong>V/v:</strong> Thẩm định Kế hoạch đấu thầu dự án cáp ngầm.</p>
            <br>
            <p><strong>1. Đánh giá chung:</strong> Hồ sơ trình duyệt cơ bản đầy đủ thủ tục pháp lý. Tuy nhiên phát hiện sai lệch về Hạn mức Đầu tư so với số liệu ghi nhận trên hệ thống ERP.</p>
            <p><strong>2. Rủi ro phát hiện (AI Report):</strong></p>
            <ul>
              <li>Tổng mức đầu tư vượt 2 tỷ VNĐ so với TMĐT đã phê duyệt.</li>
            </ul>
            <p><strong>3. Đề xuất:</strong> Yêu cầu Ban Kế hoạch giải trình khoản chênh lệch 2 tỷ VNĐ thuộc chi phí dự phòng trước khi HĐTV ra Nghị quyết phê duyệt.</p>
          </div>

          <!-- Nghị quyết -->
          <div v-if="leftTab === 'resolution'" class="pdf-page">
            <div class="pdf-header text-center">
              <h3>NGHỊ QUYẾT</h3>
              <h4>HỘI ĐỒNG THÀNH VIÊN TỔNG CÔNG TY ĐIỆN LỰC TP HÀ NỘI</h4>
            </div>
            <p class="text-center"><strong>V/v:</strong> Phê duyệt Kế hoạch đấu thầu Dự án cáp ngầm Ba Đình.</p>
            <br>
            <p><strong>ĐIỀU 1:</strong> Phê duyệt Kế hoạch đấu thầu Dự án cáp ngầm Ba Đình theo Tờ trình số 124/TTr-B02.</p>
            <p><strong>ĐIỀU 2:</strong> Yêu cầu Ban Kế hoạch điều chỉnh chi phí dự phòng, đảm bảo Tổng mức đầu tư không vượt quá 50.000.000.000 VNĐ (Năm mươi tỷ đồng chẵn) theo đúng kế hoạch ERP.</p>
            <p><strong>ĐIỀU 3:</strong> Giao Giám đốc Ban QLDA chịu trách nhiệm tổ chức đấu thầu tuân thủ đúng quy định pháp luật.</p>
            <br>
            <p class="text-right mt-4"><strong>TM. HỘI ĐỒNG THÀNH VIÊN</strong></p>
            <p class="text-right"><strong>CHỦ TỊCH</strong></p>
          </div>
        </div>
      </div>

      <!-- Right: AI Panel -->
      <div class="ws-right glass-panel">
        <div class="ai-tabs">
          <button class="tab-btn" :class="{ active: activeTab === 'ai' }" @click="activeTab = 'ai'">
            <FileCheck size="16" /> Kết quả Thẩm định
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'chat' }" @click="activeTab = 'chat'">
            <MessageSquare size="16" /> Ý kiến Thành viên (2)
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'report' }" @click="activeTab = 'report'">
            <FileBadge size="16" /> Lập Báo cáo Thẩm định
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'resolution' }" @click="activeTab = 'resolution'">
            <FileOutput size="16" /> Lập Nghị quyết
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'history' }" @click="activeTab = 'history'">
            <History size="16" /> Lịch sử Trạng thái
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'audit' }" @click="activeTab = 'audit'">
            <History size="16" /> Lịch sử Hoạt động
          </button>
        </div>

        <div class="tab-content">
          <!-- AI Analysis Tab -->
          <div v-if="activeTab === 'ai'" class="ai-analysis-panel">
            <div class="ai-content-scroll">
              <div class="summary-box">
                <div class="flex items-center justify-between mb-2">
                  <h4 style="margin-bottom: 0;"><Bot size="16" class="inline-icon"/> Tóm tắt nhanh</h4>
                  <button class="btn-icon text-primary flex items-center gap-1" @click="rerunAppraisal" :disabled="isRerunning" style="font-size: 0.8rem; font-weight: 600;" title="Chạy lại phân tích">
                    <RefreshCw size="14" :class="{ 'animate-spin': isRerunning }"/>
                    {{ isRerunning ? 'Đang chạy...' : 'Chạy lại' }}
                  </button>
                </div>
                <ul>
                  <li>Xin phê duyệt KH đấu thầu 3 gói thầu xây lắp cáp ngầm.</li>
                  <li>Tổng dự toán: 52 tỷ VNĐ. Hình thức: Đấu thầu rộng rãi.</li>
                </ul>
              </div>
              
              <h4 class="section-title">Kết quả Thẩm định chéo</h4>
              
              <!-- T-69 Revision requested banner -->
              <div v-if="showRevisionBanner" class="warning-banner">
                <div class="banner-icon">
                  <AlertTriangle size="20"/>
                </div>
                <div class="banner-body">
                  <div class="banner-title">Ban Kỹ thuật cần giải trình bổ sung</div>
                  <div class="banner-text">
                    {{ revisionBannerDetails?.issues?.join(', ') || 'Đề xuất hạ chỉ tiêu kỹ thuật thiết bị.' }}
                  </div>
                </div>
                <button class="btn-icon" @click="showRevisionBanner = false" style="background:transparent; border:none; color:inherit; cursor:pointer;">
                  <X size="16"/>
                </button>
              </div>

              <div v-if="aiChecks.length === 0" class="text-muted text-center py-4">
                Chưa có tiến trình/kết quả thẩm định.
              </div>

              <div class="check-list">
                <div v-for="check in aiChecks" :key="check.id" class="check-item" :class="check.status">
                  <div class="check-icon">
                    <CheckCircle2 v-if="check.status === 'pass'" size="18"/>
                    <AlertTriangle v-else size="18"/>
                  </div>
                  <div class="check-body">
                    <div class="check-label">{{ check.label }}</div>
                    <div class="check-desc">{{ check.desc }}</div>
                  </div>
                  <button class="btn-icon check-details-btn" @click="selectedCheck = check" title="Xem chi tiết">
                    <Info size="18" />
                  </button>
                </div>
              </div>

              <div v-if="dossierDetail?.appraisal" class="feedback-box" style="margin: 1rem 0;">
                <h4 class="section-title">Đánh giá kết quả AI</h4>
                <p class="text-muted text-sm" style="margin-bottom: 0.75rem;">
                  Phản hồi của bạn giúp agent học từ sai sót trong các lần thẩm định sau.
                </p>
                <div v-if="feedbackSubmitted" class="text-sm" style="color: var(--color-success); margin-bottom: 0.5rem;">
                  Đã gửi phản hồi {{ feedbackSubmitted === 'approve' ? 'tích cực' : 'tiêu cực' }}. Cảm ơn!
                </div>
                <div class="flex items-center gap-2" style="margin-bottom: 0.75rem;">
                  <button
                    class="btn btn-outline flex-center gap-1"
                    :disabled="isSubmittingFeedback || feedbackSubmitted"
                    @click="sendFeedback('approve')"
                    title="Kết quả hữu ích"
                  >
                    <ThumbsUp size="16"/> Hữu ích
                  </button>
                  <button
                    class="btn btn-outline flex-center gap-1"
                    :disabled="isSubmittingFeedback || feedbackSubmitted"
                    @click="sendFeedback('reject')"
                    title="Kết quả chưa chính xác"
                  >
                    <ThumbsDown size="16"/> Chưa chính xác
                  </button>
                </div>
                <textarea
                  v-model="feedbackComment"
                  class="chat-input"
                  rows="2"
                  placeholder="Ghi chú thêm (tùy chọn) — ví dụ: thiếu kiểm tra ngân sách..."
                  :disabled="!!feedbackSubmitted"
                  style="width: 100%; resize: vertical; margin-bottom: 0;"
                />
              </div>

              <div class="graph-rag-box">
                <h4 class="section-title"><Share2 size="16" class="inline-icon"/> Đồ thị Suy luận (GraphRAG)</h4>
                <div class="graph-mock">
                  [Tờ trình 124] ➔ [Sai lệch Hạn mức] ➔ [ERP: TMĐT 50 tỷ] 
                </div>
              </div>
              
              <hr class="my-divider"/>
              <h4 class="section-title">Hỏi đáp làm rõ Kết quả</h4>
              <div class="chat-messages clarify-chat">
                <div v-for="msg in clarifyMessages" :key="msg.id" class="message-wrapper" :class="{ 'my-msg': msg.isMe, 'ai-msg': msg.isAI }">
                  <div class="msg-sender">{{ msg.sender }} <span class="time">{{ msg.time }}</span></div>
                  <div class="msg-bubble">{{ msg.content }}</div>
                </div>
              </div>
            </div>
            
            <div class="chat-input-area" style="padding-top: 1rem; border-top: 1px solid var(--color-border); margin-top: 0.5rem;">
              <input v-model="newClarifyMsg" @keyup.enter="sendClarifyMsg" type="text" placeholder="Hỏi AI chi tiết về kết quả thẩm định..." class="chat-input"/>
              <button @click="sendClarifyMsg" class="btn btn-primary">Hỏi AI</button>
            </div>
          </div>

          <!-- Chat Tab (Ý kiến Thành viên) -->
          <div v-if="activeTab === 'chat'" class="chat-panel">
            <div class="chat-messages">
              <div v-for="msg in messages" :key="msg.id" class="message-wrapper" :class="{ 'my-msg': msg.isMe, 'other-msg': !msg.isMe }">
                <div class="msg-sender">{{ msg.sender }} <span class="time">{{ msg.time }}</span></div>
                <div class="msg-bubble">{{ msg.content }}</div>
              </div>
            </div>
            <div class="chat-input-area">
              <input v-model="newMessage" @keyup.enter="sendMessage" type="text" placeholder="Nhập ý kiến chỉ đạo của bạn..." class="chat-input"/>
              <button @click="sendMessage" class="btn btn-primary">Gửi Ý kiến</button>
            </div>
          </div>

          <!-- Report Generator Tab -->
          <div v-if="activeTab === 'report'" class="chat-panel">
            <div class="chat-messages">
              <div class="message-wrapper ai-msg">
                <div class="msg-sender">Trợ lý AI <span class="time">10:15</span></div>
                <div class="msg-bubble">
                  Tôi đã tổng hợp các phát hiện rủi ro và ý kiến đóng góp từ các thành viên HĐTV. Bạn có muốn tôi bắt đầu dự thảo Báo cáo thẩm định không?
                  <div class="mt-2">
                    <button class="btn btn-primary btn-sm" style="display:flex; align-items:center; gap: 0.25rem;" @click="leftTab = 'report'">
                      <FileBadge size="14"/> Dự thảo Báo cáo tự động
                    </button>
                  </div>
                </div>
              </div>
              
              <!-- Versions -->
              <div class="versions-section">
                <div class="versions-title">Lịch sử Phiên bản</div>
                <div class="version-list">
                  <div v-for="v in reportVersions" :key="v.id" class="version-card" :class="{'active-version': v.id === 2}">
                    <div class="v-header">
                      <span class="v-name"><FileText size="14" class="inline-icon"/> {{ v.name }}</span>
                      <span class="time">{{ v.time }}</span>
                    </div>
                    <div class="v-desc">{{ v.desc }}</div>
                    <div class="v-actions">
                      <button class="btn-text" @click="leftTab = 'report'">Xem bản này</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="chat-input-area">
              <input type="text" placeholder="Gõ yêu cầu tùy chỉnh (VD: Hãy bổ sung rủi ro chậm tiến độ)..." class="chat-input"/>
              <button class="btn btn-primary">Gửi</button>
            </div>
          </div>

          <!-- Resolution Generator Tab -->
          <div v-if="activeTab === 'resolution'" class="chat-panel">
            <div class="chat-messages">
              <div class="message-wrapper ai-msg">
                <div class="msg-sender">Trợ lý AI <span class="time">10:20</span></div>
                <div class="msg-bubble">
                  Báo cáo Thẩm định đã được hoàn tất. Dựa trên Báo cáo, tôi có thể dự thảo văn bản Nghị quyết HĐTV để ban hành.
                  <div class="mt-2">
                    <button class="btn btn-primary btn-sm" style="display:flex; align-items:center; gap: 0.25rem;" @click="leftTab = 'resolution'">
                      <FileOutput size="14"/> Dự thảo Nghị quyết tự động
                    </button>
                  </div>
                </div>
              </div>

              <!-- Versions -->
              <div class="versions-section">
                <div class="versions-title">Lịch sử Phiên bản</div>
                <div class="version-list">
                  <div v-for="v in resolutionVersions" :key="v.id" class="version-card" :class="{'active-version': v.id === 1}">
                    <div class="v-header">
                      <span class="v-name"><FileText size="14" class="inline-icon"/> {{ v.name }}</span>
                      <span class="time">{{ v.time }}</span>
                    </div>
                    <div class="v-desc">{{ v.desc }}</div>
                    <div class="v-actions">
                      <button class="btn-text" @click="leftTab = 'resolution'">Xem bản này</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="chat-input-area">
              <input type="text" placeholder="Gõ yêu cầu (VD: Thêm điều khoản giao Ban Tài chính kiểm tra)..." class="chat-input"/>
              <button class="btn btn-primary">Gửi</button>
            </div>
          </div>

          <!-- Status History Tab -->
          <div v-if="activeTab === 'history'" class="ai-analysis-panel">
            <div class="ai-content-scroll">
              <h4 class="section-title">Lịch sử thay đổi trạng thái</h4>
              <div class="version-list">
                <div 
                  v-for="(entry, index) in statusHistory" 
                  :key="entry.id || index" 
                  class="version-card"
                >
                  <div class="v-header">
                    <span class="v-name">
                      <span :class="['badge', getStatusBadgeClass(entry.to_status)]">
                        {{ STATUS_LABELS[entry.to_status] || entry.to_status }}
                      </span>
                    </span>
                    <span class="time">{{ new Date(entry.created_at).toLocaleString('vi-VN') }}</span>
                  </div>
                  <div class="v-desc">
                    Người thay đổi: {{ entry.changed_by || 'N/A' }}
                  </div>
                  <div v-if="entry.from_status" class="v-desc text-xs">
                    Từ: {{ STATUS_LABELS[entry.from_status] || entry.from_status }}
                  </div>
                  <div v-if="entry.comment" class="v-desc text-xs text-muted">
                    Ghi chú: {{ entry.comment }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Audit Trail Tab -->
          <div v-if="activeTab === 'audit'" class="ai-analysis-panel">
            <div class="ai-content-scroll">
              <h4 class="section-title">Lịch sử hoạt động (Audit Trail)</h4>
              <div class="version-list">
                <div 
                  v-for="(log, index) in auditLogs" 
                  :key="log.id || index" 
                  class="version-card cursor-pointer"
                  :class="{'border-l-4 border-l-primary': selectedAuditLog?.id === log.id}"
                  @click="selectedAuditLog = log"
                >
                  <div class="v-header">
                    <span class="v-name">
                      {{ log.action }}
                    </span>
                    <span class="time">{{ new Date(log.created_at).toLocaleString('vi-VN') }}</span>
                  </div>
                  <div class="v-desc">
                    {{ log.description || 'Không có mô tả' }}
                  </div>
                  <div v-if="log.user" class="v-desc text-xs">
                    Người thực hiện: {{ log.user.name }}
                  </div>
                  <div v-if="log.ip_address" class="v-desc text-xs text-muted">
                    IP: {{ log.ip_address }}
                  </div>
                </div>
                <div v-if="auditLogs.length === 0" class="text-muted text-center py-8">
                  Chưa có hoạt động nào được ghi nhận.
                </div>
              </div>
              <div v-if="selectedAuditLog" class="mt-4 p-4 bg-gray-50 rounded-lg">
                <h5 class="mb-2 text-primary">Chi tiết hoạt động</h5>
                <p class="text-sm text-muted mb-1">Thời gian: {{ new Date(selectedAuditLog.created_at).toLocaleString('vi-VN') }}</p>
                <p class="text-sm text-muted mb-1">Action: {{ selectedAuditLog.action }}</p>
                <p v-if="selectedAuditLog.description" class="text-sm mb-2">{{ selectedAuditLog.description }}</p>
                <p v-if="selectedAuditLog.extra_data" class="text-sm">
                  <strong>Metadata:</strong>
                  <br>
                  <code class="whitespace-pre-wrap">{{ JSON.stringify(selectedAuditLog.extra_data, null, 2) }}</code>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Details Modal -->
    <div v-if="selectedCheck" class="modal-overlay" @click="selectedCheck = null">
      <div class="modal-content glass-panel" @click.stop>
        <div class="modal-header">
          <h3 class="flex items-center gap-2">
            <CheckCircle2 v-if="selectedCheck.status === 'pass'" size="20" class="text-success" />
            <AlertTriangle v-else size="20" class="text-danger" />
            {{ selectedCheck.label }}
          </h3>
          <button class="btn-icon" @click="selectedCheck = null"><X size="20"/></button>
        </div>
        <div class="modal-body">
          <div class="status-badge mb-4" :class="selectedCheck.status">
            {{ selectedCheck.status === 'pass' ? 'Hợp lệ / An toàn' : 'Cảnh báo Rủi ro' }}
          </div>
          <div class="details-text" style="white-space: pre-line;">{{ selectedCheck.details }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-primary" @click="selectedCheck = null">Đóng</button>
        </div>
      </div>
    </div>

    <!-- T-22: Human-in-the-loop clarification modal -->
    <div v-if="clarificationModal" class="modal-overlay">
      <div class="glass-panel modal-content clarification-modal" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">Cần xác nhận từ người dùng</h3>
        </div>
        <div class="modal-body">
          <p class="text-muted" style="margin-bottom: 1rem;">{{ clarificationModal.question }}</p>
          <div class="clarification-options">
            <button
              v-for="opt in clarificationModal.options"
              :key="opt.id"
              class="btn btn-outline clarification-option"
              :disabled="isAnsweringClarification"
              @click="submitClarificationAnswer(opt.id)"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workspace-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 1rem;
  gap: 1rem;
}

.ws-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1rem 1.5rem;
  border-radius: 12px;
}
.header-info {
  flex: 1;
}
.doc-title {
  font-size: 1.1rem;
  margin-bottom: 0.25rem;
  color: var(--color-text-primary);
}
.tags { display: flex; gap: 0.5rem; }
.badge { font-size: 0.75rem; padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: 600; }
.badge.warning { background: var(--color-danger); color: white; }
.badge.info { background: var(--color-primary); color: white; }
.badge-success { background: rgba(34,197,94,0.15); color: var(--color-success); }
.badge-danger { background: rgba(239,68,68,0.15); color: var(--color-danger); }
.badge-secondary { background: rgba(107,114,128,0.15); color: var(--color-text-secondary); }

.header-actions { display: flex; gap: 1rem; }

.ws-content {
  flex: 1;
  display: flex;
  gap: 1rem;
  overflow: hidden;
}

/* Left Panel */
.ws-left {
  flex: 3;
  display: flex;
  flex-direction: column;
}
.pdf-toolbar {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
}
.pdf-viewer {
  flex: 1;
  background: var(--color-bg-base);
  overflow-y: auto;
  padding: 2rem;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}
.pdf-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  gap: 1rem;
}
.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--color-border);
  border-top: 4px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.loading-text {
  color: var(--color-text-secondary);
  font-weight: 500;
}
.pdf-embed-wrap {
  width: 100%;
  height: 100%;
  min-height: 600px;
}
.pdf-embed {
  width: 100%;
  height: 100%;
  min-height: 600px;
  border: none;
  background: white;
  border-radius: 4px;
}
.pdf-page {
  background: white;
  width: 100%;
  max-width: 800px;
  min-height: 1000px;
  padding: 3rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  color: #333; /* strict PDF color */
  font-family: "Times New Roman", Times, serif;
}
.highlight-warn {
  background-color: rgba(239, 68, 68, 0.3);
  cursor: pointer;
}

.doc-tabs {
  display: flex;
  border-bottom: 1px solid var(--color-border);
  background: rgba(0,0,0,0.01);
}
[data-theme='dark'] .doc-tabs { background: rgba(255,255,255,0.01); }

.form-select {
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  border-radius: 4px;
  padding: 0.2rem 0.5rem;
  outline: none;
}
.mock-table { width: 100%; border-collapse: collapse; font-size: 0.95rem; }
.mock-table th, .mock-table td { border: 1px solid #ddd; padding: 0.75rem; text-align: left; }
.mock-table th { background: #f5f5f5; font-weight: 600; }
[data-theme='dark'] .mock-table th, [data-theme='dark'] .mock-table td { border-color: #444; }
[data-theme='dark'] .mock-table th { background: #333; }
.w-full { width: 100%; }
.text-right { text-align: right; }
.mt-4 { margin-top: 1rem; }

/* Right Panel */
.ws-right {
  flex: 2;
  display: flex;
  flex-direction: column;
  min-width: 350px;
}
.ai-tabs {
  display: flex;
  border-bottom: 1px solid var(--color-border);
}
.tab-btn {
  flex: 1;
  padding: 1rem;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--color-text-secondary);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}
.tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  background: rgba(0,0,0,0.02);
}
[data-theme='dark'] .tab-btn.active { background: rgba(255,255,255,0.02); }

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

/* AI Analysis styles */
.ai-analysis-panel { display: flex; flex-direction: column; height: 100%; }
.ai-content-scroll { flex: 1; overflow-y: auto; padding-right: 0.5rem; }

.summary-box {
  background: rgba(0, 86, 179, 0.05);
  border: 1px solid rgba(0, 86, 179, 0.1);
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}
[data-theme='dark'] .summary-box { background: rgba(59, 130, 246, 0.1); }
.summary-box h4 { color: var(--color-primary); margin-bottom: 0.5rem; }
.summary-box ul { margin-left: 1.5rem; font-size: 0.95rem; }

.section-title { margin: 1.5rem 0 1rem 0; font-size: 1rem; }

.check-item {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin-bottom: 0.75rem;
  align-items: flex-start;
}
.check-item.pass .check-icon { color: var(--color-success); }
.check-item.fail { border-color: var(--color-danger); background: rgba(239, 68, 68, 0.05); }
.check-item.fail .check-icon { color: var(--color-danger); }

.check-body { flex: 1; }
.check-label { font-weight: 600; margin-bottom: 0.25rem; font-size: 0.95rem; }
.check-desc { font-size: 0.85rem; color: var(--color-text-secondary); }

.check-details-btn { opacity: 0.5; transition: opacity 0.2s; }
.check-item:hover .check-details-btn { opacity: 1; }
.check-details-btn:hover { color: var(--color-primary); }

.graph-mock {
  padding: 1rem;
  background: var(--color-bg-base);
  border-radius: 8px;
  font-family: monospace;
  font-size: 0.85rem;
  border: 1px dashed var(--color-primary);
}

.my-divider { border: none; border-top: 1px dashed var(--color-border); margin: 2rem 0 1rem 0; }
.clarify-chat { margin-bottom: 1rem; }

/* Chat styles */
.chat-panel { display: flex; flex-direction: column; height: 100%; }
.chat-messages { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 1rem; margin-bottom: 1rem; }
.message-wrapper { max-width: 85%; }
.message-wrapper.my-msg { align-self: flex-end; }
.msg-sender { font-size: 0.8rem; color: var(--color-text-secondary); margin-bottom: 0.25rem; }
.my-msg .msg-sender { text-align: right; }
.msg-bubble {
  padding: 0.75rem 1rem;
  border-radius: 12px;
  background: var(--color-bg-base);
  border: 1px solid var(--color-border);
  font-size: 0.95rem;
}
.my-msg .msg-bubble { background: var(--color-primary); color: white; border-color: var(--color-primary); }
.other-msg .msg-bubble { background: rgba(0, 0, 0, 0.03); }
[data-theme='dark'] .other-msg .msg-bubble { background: rgba(255, 255, 255, 0.05); }

.chat-input-area { display: flex; gap: 0.5rem; }
.chat-input { flex: 1; padding: 0.75rem; border-radius: 8px; border: 1px solid var(--color-border); background: var(--color-bg-base); color: var(--color-text-primary); }
.chat-input:focus { outline: none; border-color: var(--color-primary); }

.report-panel { display: flex; align-items: center; justify-content: center; height: 100%; }
.empty-state { color: var(--color-text-secondary); }

/* Versions styles */
.versions-section { margin-top: 1.5rem; padding-top: 1rem; border-top: 1px dashed var(--color-border); }
.versions-title { font-size: 0.85rem; font-weight: 600; color: var(--color-text-secondary); margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; }
.version-list { display: flex; flex-direction: column; gap: 0.75rem; }
.version-card { background: var(--color-bg-panel); border: 1px solid var(--color-border); border-radius: 8px; padding: 0.75rem; }
.version-card.active-version { border-color: var(--color-primary); box-shadow: 0 0 0 1px var(--color-primary); }
.v-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem; }
.v-name { font-weight: 600; font-size: 0.9rem; color: var(--color-primary); display: flex; align-items: center; gap: 0.25rem; }
.v-desc { font-size: 0.8rem; color: var(--color-text-secondary); margin-bottom: 0.5rem; }
.btn-text { background: none; border: none; color: var(--color-primary); font-size: 0.8rem; font-weight: 600; cursor: pointer; padding: 0; }
.btn-text:hover { text-decoration: underline; }

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}
.modal-content {
  width: 500px;
  max-width: 90vw;
  background: var(--color-bg-panel);
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
  display: flex;
  flex-direction: column;
}
.modal-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-header h3 { font-size: 1.1rem; margin: 0; }
.text-success { color: var(--color-success); }
.text-danger { color: var(--color-danger); }
.modal-body { padding: 1.5rem; flex: 1; overflow-y: auto; }
.mb-4 { margin-bottom: 1rem; }
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}
.status-badge.pass { background: rgba(16, 185, 129, 0.1); color: var(--color-success); }
.status-badge.fail { background: rgba(239, 68, 68, 0.1); color: var(--color-danger); }
.details-text { font-size: 0.95rem; line-height: 1.5; color: var(--color-text-primary); }
.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
}

/* Reference Docs Tab */
.ref-page { display: flex; flex-direction: column; gap: 1rem; }
.ref-list { background: rgba(0,0,0,0.02); border-radius: 8px; border: 1px solid var(--color-border); }
[data-theme='dark'] .ref-list { background: rgba(255,255,255,0.02); }
.ref-item { border-bottom: 1px solid var(--color-border); padding: 0.75rem 1rem; }
.ref-item:last-child { border-bottom: none; }
.animate-spin { animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }
.p-3 { padding: 0.75rem; }
.border-b { border-bottom: 1px solid var(--color-border); }

.clarification-options { display: flex; flex-direction: column; gap: 0.5rem; }
.clarification-option { text-align: left; justify-content: flex-start; }
.clarification-modal { max-width: 480px; }
.border-border { border-color: var(--color-border); }
.mb-4 { margin-bottom: 1rem; }
.text-xs { font-size: 0.75rem; }

/* T-69 Revision Banner Styles */
.warning-banner {
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.2);
  color: var(--color-warning);
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
[data-theme='dark'] .warning-banner {
  background: rgba(245, 158, 11, 0.15);
  border-color: rgba(245, 158, 11, 0.3);
  color: var(--color-warning);
}
.banner-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}
.banner-body {
  flex: 1;
}
.banner-title {
  font-weight: 600;
  margin-bottom: 0.25rem;
}
.banner-text {
  font-size: 0.875rem;
}
</style>
