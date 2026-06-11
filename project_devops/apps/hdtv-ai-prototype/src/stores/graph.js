import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'

export const useGraphStore = defineStore('graph', () => {
  const graph = ref(null)
  const loading = ref(false)

  async function fetchGraph(dossierId) {
    loading.value = true
    try {
      const { data } = await api.getKnowledgeGraph(dossierId)
      graph.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  return { graph, loading, fetchGraph }
})
