import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'

export const useGraphStore = defineStore('graph', () => {
  const graph = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchGraph(dossierId) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.getKnowledgeGraph(dossierId)
      graph.value = data
      return data
    } catch (err) {
      console.error('Failed to fetch knowledge graph:', err)
      error.value = err.response?.data?.detail || err.message || 'Lỗi khi tải đồ thị tri thức'
      throw err
    } finally {
      loading.value = false
    }
  }

  return { graph, loading, error, fetchGraph }
})
