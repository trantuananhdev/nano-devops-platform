import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'

export const useScheduleStore = defineStore('schedule', () => {
  const schedules = ref([])
  const loading = ref(false)

  async function fetchSchedules() {
    loading.value = true
    try {
      const { data } = await api.getSchedules()
      schedules.value = data.map((s) => ({
        id: s.id,
        name: s.name,
        cron: s.cron,
        scheduleText: s.schedule_text,
        tools: s.tools,
        status: s.status,
        description: s.description,
        lastRun: s.status === 'active' ? 'Gần đây' : '—',
        nextRun: s.status === 'paused' ? 'Đã tạm dừng' : 'Sắp tới...',
      }))
    } finally {
      loading.value = false
    }
  }

  return { schedules, loading, fetchSchedules }
})
