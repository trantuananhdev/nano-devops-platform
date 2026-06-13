import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'

export const useDashboardStore = defineStore('dashboard', () => {
  const summary = ref(null)
  const agentModels = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchSummary() {
    loading.value = true
    error.value = null
    try {
      const [summaryRes, modelsRes] = await Promise.all([
        api.getDashboardSummary(),
        api.getAgentModels()
      ])
      summary.value = summaryRes.data
      agentModels.value = modelsRes.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || 'Lỗi tải dữ liệu tổng quan'
      console.error('Failed to fetch dashboard data:', err)
    } finally {
      loading.value = false
    }
  }

  return { summary, agentModels, loading, error, fetchSummary }
})
