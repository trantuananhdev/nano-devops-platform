import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { getTokenUsageSummary, getTokenUsageDaily, getTokenUsageByRole, getTokenUsageByDossier } from '../services/api'

export const useTokenUsageStore = defineStore('tokenUsage', () => {
  const summary = ref(null)
  const daily = ref([])
  const byRole = ref([])
  const byDossier = ref([])
  const loading = ref(false)
  const error = ref(null)
  const selectedDays = ref(30)

  const totalTokensFormatted = computed(() => {
    if (!summary.value) return '—'
    const t = summary.value.total_tokens
    if (t >= 1_000_000) return `${(t / 1_000_000).toFixed(2)}M`
    if (t >= 1_000) return `${(t / 1_000).toFixed(1)}K`
    return String(t)
  })

  const costFormatted = computed(() => {
    if (!summary.value) return '$0.000'
    return `$${summary.value.cost_usd.toFixed(4)}`
  })

  // Daily chart data: aggregate across backends per date
  const dailyChartData = computed(() => {
    const map = {}
    for (const row of daily.value) {
      if (!map[row.date]) map[row.date] = { date: row.date, gemini: 0, local: 0, total: 0 }
      map[row.date][row.backend] = (map[row.date][row.backend] || 0) + row.total_tokens
      map[row.date].total += row.total_tokens
    }
    return Object.values(map).sort((a, b) => a.date.localeCompare(b.date))
  })

  async function fetchAll(days = selectedDays.value) {
    selectedDays.value = days
    loading.value = true
    error.value = null
    try {
      const [s, d, r, dos] = await Promise.all([
        getTokenUsageSummary(days),
        getTokenUsageDaily(days),
        getTokenUsageByRole(days),
        getTokenUsageByDossier(days),
      ])
      summary.value = s.data
      daily.value = d.data
      byRole.value = r.data
      byDossier.value = dos.data
    } catch (err) {
      error.value = err?.response?.data?.detail || err.message
    } finally {
      loading.value = false
    }
  }

  return {
    summary, daily, byRole, byDossier,
    loading, error, selectedDays,
    totalTokensFormatted, costFormatted, dailyChartData,
    fetchAll,
  }
})
