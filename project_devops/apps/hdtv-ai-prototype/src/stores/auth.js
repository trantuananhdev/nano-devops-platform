import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const currentUser = ref(null)
  const isAuthenticated = computed(() => !!currentUser.value)

  // Mock login for demo (in real system, this would call API)
  function loginAs(role) {
    const mockUsers = {
      admin: {
        id: 1,
        name: 'Admin User',
        email: 'admin@evnhanoi.vn',
        role: 'admin',
        is_active: true,
      },
      specialist: {
        id: 2,
        name: 'Nguyễn Thị Chuyên Viên',
        email: 'specialist@evnhanoi.vn',
        role: 'specialist',
        is_active: true,
      },
      dept_head: {
        id: 3,
        name: 'Trần Văn Trưởng Ban',
        email: 'dept_head@evnhanoi.vn',
        role: 'dept_head',
        is_active: true,
      },
      hdtv_leader: {
        id: 4,
        name: 'Lê Thị Lãnh đạo HĐTV',
        email: 'hdtv_leader@evnhanoi.vn',
        role: 'hdtv_leader',
        is_active: true,
      },
    }
    currentUser.value = mockUsers[role] || null
  }

  function logout() {
    currentUser.value = null
  }

  function hasRole(roles) {
    if (!currentUser.value) return false
    if (typeof roles === 'string') return currentUser.value.role === roles
    return roles.includes(currentUser.value.role)
  }

  return {
    currentUser,
    isAuthenticated,
    loginAs,
    logout,
    hasRole,
  }
})
