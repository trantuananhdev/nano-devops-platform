import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useWorkflowStore = defineStore('workflow', () => {
  const diagram = ref(null)   // { id, dossier_id, bpmn_xml, updated_at }
  const loading = ref(false)
  const saving = ref(false)
  const error = ref(null)

  async function fetchWorkflow(dossierId) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get(`/workflows/${dossierId}`)
      diagram.value = data
      return data
    } catch (e) {
      if (e.response?.status === 404) {
        diagram.value = null // no saved diagram yet — use default
      } else {
        error.value = e.message
      }
      return null
    } finally {
      loading.value = false
    }
  }

  async function saveWorkflow(dossierId, bpmnXml) {
    saving.value = true
    error.value = null
    try {
      const { data } = await api.put(`/workflows/${dossierId}`, { bpmn_xml: bpmnXml })
      diagram.value = data
      return data
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      saving.value = false
    }
  }

  function clear() {
    diagram.value = null
    error.value = null
  }

  return { diagram, loading, saving, error, fetchWorkflow, saveWorkflow, clear }
})
