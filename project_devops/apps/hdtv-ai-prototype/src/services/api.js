import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const api = axios.create({
  baseURL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

export const getDossiers = (params) => api.get('/dossiers', { params })  // T-40: supports { offset, limit }
export const getDossier = (id) => api.get(`/dossiers/${id}`)
export const getDossierUnits = () => api.get('/dossiers/units')  // distinct unit list for filter dropdown
export const appraiseDossier = (id) => api.post(`/dossiers/${id}/appraise`)
export const getAlerts = (params) => api.get('/alerts', { params })
export const resolveAlert = (id) => api.patch(`/alerts/${id}/resolve`)
export const getAuditLogs = (limit = 50) => api.get('/audit-logs', { params: { limit } })
export const getTools = () => api.get('/tools')
export const getKnowledgeGraph = (dossierId) => api.get('/knowledge-graph', { params: { dossier_id: dossierId } })
export const getDashboardSummary = () => api.get('/dashboard/summary')
export const getSchedules = () => api.get('/schedules')
export const getSkills = () => api.get('/skills')
export const getChecklistTemplate = () => api.get('/checklist-template')

// T-11: Meilisearch full-text search
export const searchDossiers = (params) => api.get('/search', { params })

// T-12: BPMN workflow persistence
export const getWorkflow = (dossierId) => api.get(`/workflows/${dossierId}`)
export const saveWorkflow = (dossierId, bpmnXml) => api.put(`/workflows/${dossierId}`, { bpmn_xml: bpmnXml })
export const listWorkflows = () => api.get('/workflows')

// T-13: Dossier create + PDF upload
export const createDossier = (body) => api.post('/dossiers', body)
export const uploadDossierPdf = (dossierId, formData) =>
  api.post(`/dossiers/${dossierId}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })

// T-14: Presigned PDF URL for workspace viewer
export const getDossierPdfUrl = (dossierId) => api.get(`/dossiers/${dossierId}/pdf-url`)

// T-14: Admin panel — users, roles, system logs
export const getUsers = () => api.get('/users')
export const getRoles = () => api.get('/roles')
export const getSystemLogs = () => api.get('/system-logs')

// T-20: Appraisal feedback + learning loop stats
export const submitFeedback = (dossierId, body) =>
  api.post(`/dossiers/${dossierId}/feedback`, body)
export const getFeedbackStats = () => api.get('/feedback/stats')

// T-22: Human-in-the-loop clarifications
export const getPendingClarifications = (params) => api.get('/clarifications/pending', { params })
export const answerClarification = (clarificationId, body) =>
  api.post(`/clarifications/${clarificationId}/answer`, body)

// T-24: Agent intelligence dashboard metrics
export const getAgentMetrics = () => api.get('/agent/metrics')

// T-25: Multi-model registry — which AI model handles which agent role
export const getAgentModels = () => api.get('/agent/models')

// T-33: API Keys Management
export const getApiKeys = (params) => api.get('/api-keys', { params })
export const createApiKey = (body) => api.post('/api-keys', body)
export const deleteApiKey = (keyId) => api.delete(`/api-keys/${keyId}`)

// T-36: MCP Audit Logs
export const getMcpAuditLogs = (params) => api.get('/mcp/audit-logs', { params })

// T-46: Formal Status Transitions
export const transitionDossierStatus = (dossierId, body) => api.post(`/dossiers/${dossierId}/transition-status`, body)
export const getDossierStatusHistory = (dossierId) => api.get(`/dossiers/${dossierId}/status-history`)

// T-52: Reference Document Management
export const getReferenceDocuments = (dossierId) => api.get(`/dossiers/${dossierId}/reference-documents`)
export const uploadReferenceDocument = (dossierId, formData, uploadedBy) =>
  api.post(`/dossiers/${dossierId}/reference-documents`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    params: { uploaded_by: uploadedBy },
    timeout: 60000,
  })
export const deleteReferenceDocument = (dossierId, documentId) =>
  api.delete(`/dossiers/${dossierId}/reference-documents/${documentId}`)

export default api
