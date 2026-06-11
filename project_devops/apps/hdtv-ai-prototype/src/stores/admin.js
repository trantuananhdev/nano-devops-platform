import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '../services/api'

export const useAdminStore = defineStore('admin', () => {
  const toolAudits = ref([])
  const users = ref([])
  const roles = ref([])
  const systemLogs = ref([])
  const agentMetrics = ref(null)
  const apiKeys = ref([])        // T-33
  const mcpLogs = ref([])         // T-36
  const mcpToolFilter = ref('')   // T-36
  const loading = ref(false)

  async function fetchAuditLogs() {
    loading.value = true
    try {
      const { data } = await api.getAuditLogs(50)
      toolAudits.value = data.map((log) => ({
        id: `TA-${log.id}`,
        timestamp: log.created_at ? new Date(log.created_at).toLocaleString('vi-VN') : '',
        tool: log.tool_name,
        status: log.outputs?.error ? 'failed' : 'success',
        duration: `${log.execution_time_ms}ms`,
        caller: `AI Agent (${log.task_id})`,
        inputs: JSON.stringify(log.inputs, null, 2),
        outputs: JSON.stringify(log.outputs, null, 2),
      }))
    } finally {
      loading.value = false
    }
  }

  async function fetchUsers() {
    const { data } = await api.getUsers()
    users.value = data
  }

  async function fetchRoles() {
    const { data } = await api.getRoles()
    roles.value = data.map((r) => ({
      id: r.id,
      name: r.name,
      desc: r.desc,
      usersCount: r.users_count,
    }))
  }

  async function fetchSystemLogs() {
    const { data } = await api.getSystemLogs()
    systemLogs.value = data
  }

  async function fetchAgentMetrics() {
    const { data } = await api.getAgentMetrics()
    agentMetrics.value = data
  }

  // T-33: API Keys Management
  async function fetchApiKeys(keyType = null) {
    const params = keyType ? { key_type: keyType } : {}
    const { data } = await api.getApiKeys(params)
    apiKeys.value = data
  }

  async function addApiKey(body) {
    const { data } = await api.createApiKey(body)
    // Prepend to list (newest first)
    apiKeys.value = [{ ...data, masked_key: undefined }, ...apiKeys.value]
    return data // includes masked_key — shown once
  }

  async function removeApiKey(keyId) {
    await api.deleteApiKey(keyId)
    apiKeys.value = apiKeys.value.filter((k) => k.id !== keyId)
  }

  // T-36: MCP Audit Logs
  async function loadMcpLogs() {
    loading.value = true
    try {
      const params = mcpToolFilter.value ? { tool_name: mcpToolFilter.value } : {}
      const { data } = await api.getMcpAuditLogs(params)
      mcpLogs.value = data
    } finally {
      loading.value = false
    }
  }

  // T-36: Filtered MCP logs
  const mcpLogsFiltered = computed(() => {
    if (!mcpToolFilter.value) {
      return mcpLogs.value
    }
    return mcpLogs.value.filter(log => 
      log.tool_name.toLowerCase().includes(mcpToolFilter.value.toLowerCase())
    )
  })

  async function fetchAll() {
    loading.value = true
    try {
      await Promise.all([
        fetchAuditLogs(),
        fetchUsers(),
        fetchRoles(),
        fetchSystemLogs(),
        fetchAgentMetrics(),
        fetchApiKeys(),
        loadMcpLogs(),
      ])
    } finally {
      loading.value = false
    }
  }

  return {
    toolAudits,
    users,
    roles,
    systemLogs,
    agentMetrics,
    apiKeys,
    mcpLogs,
    mcpLogsFiltered,
    mcpToolFilter,
    loading,
    fetchAuditLogs,
    fetchUsers,
    fetchRoles,
    fetchSystemLogs,
    fetchAgentMetrics,
    fetchApiKeys,
    addApiKey,
    removeApiKey,
    loadMcpLogs,
    fetchAll,
  }
})
