import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '../services/api'

const PAGE_SIZE = 20

export const useDossierStore = defineStore('dossier', () => {
  const dossiers   = ref([])   // accumulated list (all pages loaded so far)
  const current    = ref(null)
  const loading    = ref(false)
  const loadingMore = ref(false)
  const creating   = ref(false)
  const uploading  = ref(false)
  const error      = ref(null)
  const uploadResult = ref(null)

  // T-40: Pagination state
  const total    = ref(0)
  const offset   = ref(0)
  const hasMore  = ref(false)

  const statusLabels = {
    draft: 'Nháp',
    pending: 'Chờ duyệt',
    appraising: 'Đang thẩm định',
    submitted_to_dept: 'Đã trình lên Ban',
    dept_approved: 'Ban đã duyệt',
    dept_rejected: 'Ban từ chối',
    submitted_to_board: 'Đã trình lên HĐTV',
    board_reviewed: 'HĐTV đã xem xét',
    approved: 'Đã phê duyệt',
    rejected: 'Đã từ chối',
    needs_revision: 'Bổ sung hồ sơ',
  }
  const riskLabels = { high: 'Cao', medium: 'Trung bình', low: 'Thấp' }

  function _mapDossier(d) {
    return {
      id:     String(d.id),
      docNo:  d.doc_no,
      title:  d.title,
      unit:   d.unit,
      date:   d.created_at ? new Date(d.created_at).toLocaleDateString('vi-VN') : '',
      risk:   d.risk_level,
      status: statusLabels[d.status] || d.status,
    }
  }

  // T-40: Initial load — resets list and loads page 0
  async function fetchDossiers() {
    loading.value = true
    error.value   = null
    try {
      const { data } = await api.getDossiers({ offset: 0, limit: PAGE_SIZE })
      dossiers.value = data.items.map(_mapDossier)
      total.value    = data.total
      offset.value   = data.items.length
      hasMore.value  = data.has_more
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  // T-40: Load next page and append (infinite scroll / load-more)
  async function loadMoreDossiers() {
    if (!hasMore.value || loadingMore.value) return
    loadingMore.value = true
    try {
      const { data } = await api.getDossiers({ offset: offset.value, limit: PAGE_SIZE })
      dossiers.value  = [...dossiers.value, ...data.items.map(_mapDossier)]
      total.value     = data.total
      offset.value   += data.items.length
      hasMore.value   = data.has_more
    } catch (e) {
      error.value = e.message
    } finally {
      loadingMore.value = false
    }
  }

  async function fetchDossier(id) {
    loading.value = true
    error.value   = null
    try {
      const { data } = await api.getDossier(id)
      current.value  = data
      return data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function startAppraisal(id) {
    const { data } = await api.appraiseDossier(id)
    return data
  }

  // T-13: Create new dossier
  async function createNewDossier(body) {
    creating.value = true
    error.value    = null
    try {
      const { data } = await api.createDossier(body)
      // Prepend to list, bump total
      dossiers.value = [_mapDossier(data), ...dossiers.value]
      total.value   += 1
      offset.value  += 1
      return data
    } catch (e) {
      const detail = e.response?.data?.detail || e.message
      error.value   = detail
      throw new Error(detail)
    } finally {
      creating.value = false
    }
  }

  // T-13: Upload PDF to MinIO
  async function uploadPdf(dossierId, file) {
    uploading.value    = true
    uploadResult.value = null
    error.value        = null
    try {
      const formData = new FormData()
      formData.append('file', file)
      const { data } = await api.uploadDossierPdf(dossierId, formData)
      uploadResult.value = data
      return data
    } catch (e) {
      const detail = e.response?.data?.detail || e.message
      error.value        = detail
      uploadResult.value = { ok: false, error: detail }
      return null
    } finally {
      uploading.value = false
    }
  }

  return {
    dossiers,
    current,
    loading,
    loadingMore,
    creating,
    uploading,
    error,
    uploadResult,
    total,
    offset,
    hasMore,
    statusLabels,
    riskLabels,
    fetchDossiers,
    loadMoreDossiers,
    fetchDossier,
    startAppraisal,
    createNewDossier,
    uploadPdf,
  }
})
