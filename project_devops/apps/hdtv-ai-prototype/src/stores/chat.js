import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'
import { useDossierStore } from './dossier'

// Number of audit log rows loaded per page in chat history
const AUDIT_PAGE = 10

// ─── helpers ──────────────────────────────────────────────────────────────
function _auditToMessage(log, id) {
  return {
    id,
    sender:     'ai',
    text:       '',
    time:       log.created_at
      ? new Date(log.created_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
      : '',
    isTool:     true,
    toolName:   log.tool_name,
    toolStatus: log.outputs?.error ? 'failed' : 'success',
    toolResult: JSON.stringify(log.outputs, null, 2),
  }
}

function _filterRelevant(logs, dossierId) {
  const id = String(dossierId)
  return logs.filter(
    (log) => String(log.inputs?.dossier_id || '') === id || !log.inputs?.dossier_id,
  )
}

export const useChatStore = defineStore('chat', () => {
  const sessions        = ref([])
  const messages        = ref([])
  const activeDossierId = ref(null)
  const loading         = ref(false)
  const loadingHistory  = ref(false)   // T-40: loading older audit pages

  // T-40: How many audit-log rows have been fetched for the active session.
  // Used as the `limit` parameter for the next getAuditLogs call — the BE
  // endpoint returns the N most-recent rows, so incrementing limit gives us
  // an older slice.
  const _auditFetchedCount = ref(0)
  const _auditHasMore      = ref(false)

  // T-40: Per-session message cache (dossierId → messages[]).
  // Avoids a full refetch when the user switches tabs.
  const _sessionCache = new Map()

  // ─── loadSessions ─────────────────────────────────────────────────────
  async function loadSessions() {
    const dossierStore = useDossierStore()
    await dossierStore.fetchDossiers()
    sessions.value = dossierStore.dossiers.map((d, i) => ({
      id:     d.id,
      title:  `Thẩm định ${d.docNo}`,
      date:   d.date || 'Gần đây',
      active: i === 0,
      docNo:  d.docNo,
    }))
    if (sessions.value.length && !activeDossierId.value) {
      await selectSession(sessions.value[0].id)
    }
  }

  // ─── selectSession ────────────────────────────────────────────────────
  async function selectSession(dossierId) {
    activeDossierId.value = dossierId
    sessions.value.forEach((s) => { s.active = s.id === dossierId })

    // Instant restore from cache — no API round-trip
    if (_sessionCache.has(dossierId)) {
      const cached = _sessionCache.get(dossierId)
      messages.value        = cached.msgs
      _auditFetchedCount.value = cached.fetched
      _auditHasMore.value      = cached.hasMore
      return
    }

    loading.value = true
    try {
      const dossierStore = useDossierStore()
      const detail = await dossierStore.fetchDossier(dossierId)

      // Initial page: most-recent AUDIT_PAGE rows
      const { data: allLogs } = await api.getAuditLogs(AUDIT_PAGE)
      const relevant = _filterRelevant(allLogs, dossierId)

      const msgs = [
        {
          id:     1,
          sender: 'ai',
          text:   `Xin chào! Đang hỗ trợ thẩm định: ${detail?.title || 'Tờ trình'}.`,
          time:   '08:00',
        },
        ...relevant.map((log, i) => _auditToMessage(log, 10 + i)),
      ]

      if (detail?.appraisal?.report_md) {
        msgs.push({
          id:         99,
          sender:     'ai',
          text:       detail.appraisal.report_md.slice(0, 400) +
                      (detail.appraisal.report_md.length > 400 ? '…' : ''),
          time:       new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
          hasActions: true,
        })
      }

      // Fetched AUDIT_PAGE rows — if all were relevant, there might be more
      const hasMore = allLogs.length >= AUDIT_PAGE

      messages.value           = msgs
      _auditFetchedCount.value = AUDIT_PAGE
      _auditHasMore.value      = hasMore

      _sessionCache.set(dossierId, { msgs, fetched: AUDIT_PAGE, hasMore })
    } finally {
      loading.value = false
    }
  }

  // ─── loadMoreMessages (T-40) ──────────────────────────────────────────
  /**
   * Load the next page of audit logs and prepend them as older messages.
   * The BE `getAuditLogs(limit)` returns the N most-recent rows DESC, so we
   * increment the limit to include an older window, then take the new rows.
   */
  async function loadMoreMessages() {
    if (!_auditHasMore.value || loadingHistory.value || !activeDossierId.value) return
    loadingHistory.value = true
    try {
      const nextLimit  = _auditFetchedCount.value + AUDIT_PAGE
      const { data: allLogs } = await api.getAuditLogs(nextLimit)

      // The new rows are the ones we haven't seen yet (beyond current fetch)
      const newLogs = allLogs.slice(_auditFetchedCount.value)
      const relevant = _filterRelevant(newLogs, activeDossierId.value)

      if (relevant.length === 0) {
        _auditHasMore.value = false
        return
      }

      const olderMsgs = relevant.map((log, i) =>
        _auditToMessage(log, Date.now() + i),
      )

      // Prepend after the greeting (index 0) — keeps oldest-first visual order
      messages.value = [
        messages.value[0],
        ...olderMsgs,
        ...messages.value.slice(1),
      ]

      _auditFetchedCount.value = nextLimit
      _auditHasMore.value      = allLogs.length >= nextLimit

      _sessionCache.set(activeDossierId.value, {
        msgs:    messages.value,
        fetched: _auditFetchedCount.value,
        hasMore: _auditHasMore.value,
      })
    } finally {
      loadingHistory.value = false
    }
  }

  // ─── invalidateSession ────────────────────────────────────────────────
  /** Drop cached messages so the next selectSession does a fresh fetch. */
  function invalidateSession(dossierId) {
    _sessionCache.delete(dossierId)
  }

  // ─── sendAndAppraise ──────────────────────────────────────────────────
  async function sendAndAppraise(text) {
    if (!activeDossierId.value) return
    messages.value.push({
      id:     Date.now(),
      sender: 'user',
      text,
      time:   new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
    })
    await api.appraiseDossier(activeDossierId.value)
    messages.value.push({
      id:         Date.now() + 1,
      sender:     'ai',
      text:       'Đã gửi yêu cầu thẩm định. Agent đang chạy ReAct — theo dõi kết quả qua WebSocket.',
      time:       new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
      hasActions: true,
    })
    // Drop cache so the next switch/WS callback gets fresh audit rows
    invalidateSession(activeDossierId.value)
  }

  return {
    sessions,
    messages,
    activeDossierId,
    loading,
    loadingHistory,
    loadMoreMessages,
    loadSessions,
    selectSession,
    sendAndAppraise,
    invalidateSession,
  }
})
