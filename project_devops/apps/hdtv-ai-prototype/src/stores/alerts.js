import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'

export const useAlertsStore = defineStore('alerts', () => {
  const alerts = ref([])
  const loading = ref(false)

  async function fetchAlerts(status = null) {
    loading.value = true
    try {
      const params = status ? { status } : {}
      const { data } = await api.getAlerts(params)
      alerts.value = data.map((a) => ({
        id: `AL-${a.id}`,
        rawId: a.id,
        title: a.description.slice(0, 80),
        severity: a.severity,
        source: a.source,
        dossierId: a.dossier_id ? String(a.dossier_id) : '',
        dossier: a.description,
        date: a.created_at ? new Date(a.created_at).toLocaleString('vi-VN') : '',
        status: a.status,
        description: a.description,
      }))
    } finally {
      loading.value = false
    }
  }

  async function resolve(id) {
    await api.resolveAlert(id)
    await fetchAlerts()
  }

  return { alerts, loading, fetchAlerts, resolve }
})
