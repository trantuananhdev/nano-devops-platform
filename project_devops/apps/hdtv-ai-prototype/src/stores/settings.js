import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'

export const useSettingsStore = defineStore('settings', () => {
  const checklists = ref([])
  const loading = ref(false)

  async function fetchChecklistTemplate(dossierTypeId = null) {
    loading.value = true
    try {
      const { data } = await api.getChecklistTemplate(dossierTypeId)
      checklists.value = data.map((c) => ({
        id: c.id,
        text: c.text,
        type: c.type,
        isRequired: c.is_required,
      }))
    } finally {
      loading.value = false
    }
  }

  return { checklists, loading, fetchChecklistTemplate }
})
