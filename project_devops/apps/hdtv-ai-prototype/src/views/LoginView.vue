<template>
  <div class="login-page">
    <div class="login-card glass-panel">
      <div class="login-logo">
        <div class="logo-icon">⚡</div>
        <h1 class="login-title">HDTV AI</h1>
        <p class="login-subtitle">Hệ thống Thẩm định Hồ sơ Vật tư — EVN Hà Nội</p>
      </div>

      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">Email</label>
          <input
            v-model="email"
            type="email"
            class="form-input"
            placeholder="admin@evnhanoi.vn"
            autocomplete="email"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label">Mật khẩu</label>
          <input
            v-model="password"
            type="password"
            class="form-input"
            placeholder="••••••••"
            autocomplete="current-password"
            required
          />
        </div>

        <p v-if="authStore.error" class="login-error">{{ authStore.error }}</p>

        <button type="submit" class="btn btn-primary login-btn" :disabled="authStore.loading">
          <span v-if="authStore.loading">Đang đăng nhập...</span>
          <span v-else>Đăng nhập</span>
        </button>
      </form>

      <div class="demo-accounts">
        <p class="demo-title">Tài khoản demo</p>
        <div class="demo-grid">
          <button
            v-for="demo in demoAccounts"
            :key="demo.role"
            class="demo-btn"
            @click="fillDemo(demo)"
          >
            <span class="demo-role">{{ demo.label }}</span>
            <span class="demo-email">{{ demo.email }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const email = ref('admin@evnhanoi.vn')
const password = ref('EVN@2024!')

const demoAccounts = [
  { role: 'admin', label: 'Admin', email: 'admin@evnhanoi.vn' },
  { role: 'hdtv_leader', label: 'Lãnh đạo HĐTV', email: 'tbich@evnhanoi.vn' },
  { role: 'dept_head', label: 'Trưởng phòng', email: 'pvcuong@evnhanoi.vn' },
  { role: 'specialist', label: 'Chuyên viên', email: 'htem@evnhanoi.vn' },
]

function fillDemo(demo) {
  email.value = demo.email
  password.value = 'EVN@2024!'
}

async function handleLogin() {
  const ok = await authStore.login(email.value, password.value)
  if (ok) {
    const redirect = route.query.redirect || '/dashboard'
    router.push(redirect)
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-base);
  background-image: radial-gradient(ellipse at 20% 20%, rgba(0, 86, 179, 0.08), transparent 50%),
                    radial-gradient(ellipse at 80% 80%, rgba(242, 101, 34, 0.06), transparent 50%);
  padding: 1rem;
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 2.5rem;
}

.login-logo {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.login-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-primary);
  margin: 0 0 0.25rem;
}

.login-subtitle {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.form-input {
  padding: 0.625rem 0.875rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-panel-solid);
  color: var(--color-text-primary);
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.2s;
}

.form-input:focus {
  border-color: var(--color-primary);
}

.login-error {
  color: var(--color-danger);
  font-size: 0.875rem;
  margin: 0;
  padding: 0.5rem 0.75rem;
  background: rgba(239, 68, 68, 0.08);
  border-radius: 6px;
}

.login-btn {
  width: 100%;
  padding: 0.75rem;
  font-size: 1rem;
  font-weight: 600;
}

.demo-accounts {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border);
}

.demo-title {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  margin: 0 0 0.75rem;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.demo-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.demo-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  text-align: left;
}

.demo-btn:hover {
  background: rgba(0, 86, 179, 0.05);
  border-color: var(--color-primary);
}

.demo-role {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.demo-email {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
}
</style>
