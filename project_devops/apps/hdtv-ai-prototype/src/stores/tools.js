import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'

export const useToolsStore = defineStore('tools', () => {
  const tools = ref([])
  const loading = ref(false)

  async function fetchTools() {
    loading.value = true
    try {
      const { data } = await api.getTools()
      tools.value = data.map((t, i) => ({
        id: i + 1,
        name: t.name,
        description: t.description,
        category: t.category,
        status: t.status === 'ready' ? 'active' : t.status,
        usageCount: t.usage_count,
        lastUsedAt: t.last_used_at,
      }))
    } finally {
      loading.value = false
    }
  }

  return { tools, loading, fetchTools }
})
