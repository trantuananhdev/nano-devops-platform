import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'

export const useSkillsStore = defineStore('skills', () => {
  const skills = ref([])
  const loading = ref(false)

  async function fetchSkills() {
    loading.value = true
    try {
      const { data } = await api.getSkills()
      skills.value = data.map((s) => ({
        id: s.id,
        name: s.name,
        description: s.description,
        type: s.type || 'prompt',
        isActive: s.is_active,
        markdownContent: s.markdown_content,
      }))
    } finally {
      loading.value = false
    }
  }

  return { skills, loading, fetchSkills }
})
