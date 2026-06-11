import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'

export const useDashboardStore = defineStore('dashboard', () => {
  const summary = ref(null)
  const loading = ref(false)

  async function fetchSummary() {
    loading.value = true
    try {
      const { data } = await api.getDashboardSummary()
      summary.value = data
    } finally {
      loading.value = false
    }
  }

  return { summary, loading, fetchSummary }
})
