import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

const HISTORY_KEY = 'hdtv_search_history'
const MAX_HISTORY = 10

export const useSearchStore = defineStore('search', () => {
  const query = ref('')
  const hits = ref([])
  const loading = ref(false)
  const processingTimeMs = ref(0)
  const estimatedTotal = ref(0)
  const degraded = ref(false)
  const open = ref(false) // modal/overlay open state
  const history = ref([])

  // Load history from localStorage on init
  function loadHistory() {
    try {
      const saved = localStorage.getItem(HISTORY_KEY)
      if (saved) {
        history.value = JSON.parse(saved)
      }
    } catch {
      history.value = []
    }
  }

  // Save search to history
  function saveToHistory(q) {
    const trimmed = q.trim()
    if (!trimmed) return
    
    // Remove existing entry if present
    history.value = history.value.filter(h => h !== trimmed)
    // Add to front
    history.value.unshift(trimmed)
    // Keep only max history
    if (history.value.length > MAX_HISTORY) {
      history.value = history.value.slice(0, MAX_HISTORY)
    }
    // Save to localStorage
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history.value))
    } catch {
      // Ignore localStorage errors
    }
  }

  // Clear history
  function clearHistory() {
    history.value = []
    try {
      localStorage.removeItem(HISTORY_KEY)
    } catch {
      // Ignore
    }
  }

  async function search(q, { risk = null, status = null, limit = 20 } = {}) {
    query.value = q
    if (!q.trim()) {
      hits.value = []
      estimatedTotal.value = 0
      return
    }
    loading.value = true
    try {
      const params = { q, limit }
      if (risk) params.risk = risk
      if (status) params.status = status
      const { data } = await api.get('/search', { params })
      hits.value = data.hits || []
      processingTimeMs.value = data.processing_time_ms || 0
      estimatedTotal.value = data.estimated_total_hits || 0
      degraded.value = data.degraded || false
      saveToHistory(q)
    } catch (e) {
      hits.value = []
      degraded.value = true
    } finally {
      loading.value = false
    }
  }

  function clear() {
    query.value = ''
    hits.value = []
    loading.value = false
    processingTimeMs.value = 0
    estimatedTotal.value = 0
    degraded.value = false
  }

  loadHistory()

  return { 
    query, hits, loading, processingTimeMs, estimatedTotal, degraded, open, history,
    search, clear, clearHistory 
  }
})
