import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
const TOKEN_KEY = 'hdtv_access_token'

function decodeJwt(token) {
  try {
    const payload = token.split('.')[1]
    return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
  } catch {
    return null
  }
}

function loadUserFromToken() {
  const token = localStorage.getItem(TOKEN_KEY)
  if (!token) return null
  const payload = decodeJwt(token)
  if (!payload) return null
  // Check expiry
  if (payload.exp && Date.now() / 1000 > payload.exp) {
    localStorage.removeItem(TOKEN_KEY)
    return null
  }
  return {
    id: parseInt(payload.sub),
    name: payload.name,
    email: payload.email,
    role: payload.role,
    is_active: true,
  }
}

export const useAuthStore = defineStore('auth', () => {
  const currentUser = ref(loadUserFromToken())
  const isAuthenticated = computed(() => !!currentUser.value)
  const loading = ref(false)
  const error = ref(null)

  async function login(email, password) {
    loading.value = true
    error.value = null
    try {
      const res = await axios.post(`${API_BASE}/auth/login`, { email, password })
      const { access_token, user_id, name, role } = res.data
      localStorage.setItem(TOKEN_KEY, access_token)
      currentUser.value = { id: user_id, name, email, role, is_active: true }
      // Set default Authorization header for all future requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Đăng nhập thất bại'
      return false
    } finally {
      loading.value = false
    }
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY)
    delete axios.defaults.headers.common['Authorization']
    currentUser.value = null
  }

  function hasRole(roles) {
    if (!currentUser.value) return false
    if (typeof roles === 'string') return currentUser.value.role === roles
    return roles.includes(currentUser.value.role)
  }

  // Restore Authorization header on app load
  function initAuth() {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token && currentUser.value) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
  }

  // Legacy support — loginAs còn dùng khi demo offline (không có backend)
  function loginAs(role) {
    const DEMO_USERS = {
      admin: { id: 1, name: 'Nguyễn Văn An', email: 'admin@evnhanoi.vn', role: 'admin', is_active: true },
      hdtv_leader: { id: 2, name: 'Trần Thị Bích', email: 'tbich@evnhanoi.vn', role: 'hdtv_leader', is_active: true },
      dept_head: { id: 3, name: 'Phạm Văn Cường', email: 'pvcuong@evnhanoi.vn', role: 'dept_head', is_active: true },
      specialist: { id: 5, name: 'Hoàng Thị Em', email: 'htem@evnhanoi.vn', role: 'specialist', is_active: true },
    }
    currentUser.value = DEMO_USERS[role] || null
  }

  return {
    currentUser,
    isAuthenticated,
    loading,
    error,
    login,
    logout,
    hasRole,
    initAuth,
    loginAs,
  }
})
