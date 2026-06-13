<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardStore } from '../stores/dashboard'

const router = useRouter()
const store = useDashboardStore()

onMounted(() => store.fetchSummary())

const notableDossiers = computed(() => store.summary?.notable_dossiers || [])
const pendingCount = computed(() => store.summary?.pending_count ?? '—')
const highRiskCount = computed(() => store.summary?.high_risk_count ?? '—')
const approvedCount = computed(() => store.summary?.approved_count ?? '—')
const alertSources = computed(() => store.summary?.alert_sources || [])
const newestDossiers = computed(() => store.summary?.newest_dossiers || [])
const agentModels = computed(() => store.agentModels || [])

const dossiersByUnit = computed(() => store.summary?.dossiers_by_unit || [])

const pieChartStyle = computed(() => {
  if (dossiersByUnit.value.length === 0) {
    return { background: 'var(--color-border)' }
  }
  let currentPct = 0
  const colors = [
    'var(--color-primary)',
    'var(--color-accent)',
    'var(--color-success)',
    'var(--color-warning)',
    'var(--color-danger)',
  ]
  const stops = []
  dossiersByUnit.value.forEach((item, idx) => {
    const nextPct = currentPct + item.pct
    const color = colors[idx % colors.length]
    stops.push(`${color} ${currentPct}% ${nextPct}%`)
    currentPct = nextPct
  })
  return {
    background: `conic-gradient(${stops.join(', ')})`,
    boxShadow: 'inset 0 0 0 30px var(--color-bg-panel)'
  }
})

const openDossier = (d) => {
  if (d.dossier_id) {
    router.push(`/workspace/${d.dossier_id}`)
  }
}
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <div>
        <h1 class="page-title">Tổng quan Thẩm duyệt</h1>
        <p class="page-subtitle">Thống kê dữ liệu tờ trình theo thời gian thực</p>
      </div>
    </header>
    
    <!-- Error Banner -->
    <div v-if="store.error" class="error-banner glass-panel">
      <div class="error-banner-content">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="error-icon"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        <span>{{ store.error }}</span>
      </div>
    </div>
    
    <!-- Loading Skeleton -->
    <template v-if="store.loading">
      <div class="dashboard-grid">
        <div v-for="i in 3" :key="i" class="stat-card glass-panel skeleton-card">
          <div class="skeleton-icon"></div>
          <div class="skeleton-content">
            <div class="skeleton-line short"></div>
            <div class="skeleton-line long"></div>
          </div>
        </div>
      </div>
      <div class="charts-area">
        <div class="chart-card glass-panel skeleton-card" style="min-height:300px;">
          <div class="skeleton-line short" style="margin-bottom:1.5rem;"></div>
          <div class="skeleton-circle"></div>
        </div>
        <div class="chart-card glass-panel skeleton-card" style="min-height:300px;">
          <div class="skeleton-line short" style="margin-bottom:1.5rem;"></div>
          <div v-for="j in 4" :key="j" class="skeleton-line long" style="margin-bottom:0.75rem;"></div>
        </div>
      </div>
    </template>

    <template v-else>
    <div class="dashboard-grid">
      <!-- Stats Cards -->
      <div class="stat-card glass-panel">
        <div class="stat-icon warning">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="12" y1="12" x2="16" y2="16"/><line x1="12" y1="12" x2="8" y2="16"/></svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">Chờ duyệt (Quá hạn)</div>
          <div class="stat-value">{{ pendingCount }} <span class="stat-trend negative">từ API</span></div>
        </div>
      </div>

      <div class="stat-card glass-panel">
        <div class="stat-icon danger">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">Cảnh báo Rủi ro cao</div>
          <div class="stat-value">{{ highRiskCount }} <span class="stat-trend negative">từ AI</span></div>
        </div>
      </div>

      <div class="stat-card glass-panel">
        <div class="stat-icon success">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">Đã thông qua (Tháng)</div>
          <div class="stat-value">{{ approvedCount }} <span class="stat-trend positive">đã thông qua</span></div>
        </div>
      </div>
    </div>

    <!-- Charts area placeholder -->
    <div class="charts-area">
      <div class="chart-card glass-panel">
        <h3 class="card-title">Tỷ lệ Tờ trình theo Ban nghiệp vụ</h3>
        <div class="chart-placeholder" style="flex-direction: row; justify-content: space-around; gap: 1rem;">
           <!-- Placeholder for pie chart -->
           <div class="pie-mock" :style="pieChartStyle"></div>
           <ul v-if="dossiersByUnit.length > 0" class="error-list" style="max-width: 50%;">
             <li v-for="(item, i) in dossiersByUnit" :key="item.unit" style="padding: 0.25rem 0; font-size: 0.85rem;">
               <span class="dot" :class="i === 0 ? 'primary' : i === 1 ? 'accent' : i === 2 ? 'success' : i === 3 ? 'warning' : 'danger'"></span>
               <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ item.unit }}: {{ item.count }} ({{ item.pct }}%)</span>
             </li>
           </ul>
           <div v-else class="no-data-msg">
             Chưa có dữ liệu thống kê
           </div>
        </div>
      </div>
      <div class="chart-card glass-panel">
        <h3 class="card-title">Cảnh báo lỗi phổ biến từ AI</h3>
        <div class="chart-placeholder">
          <ul v-if="alertSources.length > 0" class="error-list">
            <li v-for="(src, i) in alertSources" :key="src.source">
              <span class="dot" :class="i === 0 ? 'danger' : i === 1 ? 'warning' : i === 2 ? 'primary' : 'text'"></span>
              {{ src.source }} ({{ src.pct }}%)
            </li>
          </ul>
          <div v-else class="no-data-msg">
            Chưa có cảnh báo nào được ghi nhận
          </div>
        </div>
      </div>
    </div>

    <!-- Newest Dossiers Widget -->
    <div class="newest-dossiers-area mt-6">
      <div class="glass-panel" style="padding: 1.5rem;">
        <h3 class="card-title">Tờ trình mới nhất</h3>
        <div class="dossier-grid">
          <div 
            v-for="d in newestDossiers" 
            :key="d.id" 
            @click="openDossier(d)" 
            class="dossier-card clickable-row"
          >
            <div class="dossier-card-header">
              <span class="dossier-id">{{ d.doc_no || d.id }}</span>
              <span class="risk-badge" :class="{'high': d.risk_level === 'high' || d.risk === 'Cao', 'medium': d.risk_level === 'medium' || d.risk === 'Trung bình', 'low': d.risk_level === 'low' || d.risk === 'Thấp'}">
                {{ d.risk_level === 'high' || d.risk === 'Cao' ? 'Rủi ro cao' : d.risk_level === 'medium' || d.risk === 'Trung bình' ? 'Trung bình' : 'Thấp' }}
              </span>
            </div>
            <div class="dossier-card-title">{{ d.title }}</div>
            <div class="dossier-card-footer">
              <span class="dossier-dept">{{ d.dept || d.unit }}</span>
              <span class="dossier-date">{{ d.date }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Notable Dossiers List -->
    <div class="dossiers-table-area mt-6">
      <div class="glass-panel" style="padding: 1.5rem;">
        <h3 class="card-title">Danh sách 10 Tờ trình đáng chú ý nhất</h3>
        <div class="table-responsive">
          <table class="dossier-table">
            <thead>
              <tr>
                <th>Số hiệu</th>
                <th>Trích yếu</th>
                <th>Ban trình</th>
                <th>Ngày trình</th>
                <th>Mức Rủi ro (AI)</th>
                <th>Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in notableDossiers" :key="d.id" @click="openDossier(d)" class="clickable-row">
                <td class="font-medium text-primary">{{ d.doc_no || d.id }}</td>
                <td>{{ d.title }}</td>
                <td>{{ d.dept || d.unit }}</td>
                <td>{{ d.date }}</td>
                <td>
                  <span class="risk-badge" :class="{'high': d.risk_level === 'high' || d.risk === 'Cao', 'medium': d.risk_level === 'medium' || d.risk === 'Trung bình', 'low': d.risk_level === 'low' || d.risk === 'Thấp'}">
                    {{ d.risk_level === 'high' || d.risk === 'Cao' ? 'Rủi ro cao' : d.risk_level === 'medium' || d.risk === 'Trung bình' ? 'Trung bình' : 'Thấp' }}
                  </span>
                </td>
                <td>
                  <span class="status-dot" :class="{'pending': d.status === 'Chờ duyệt' || d.status === 'pending', 'processing': d.status === 'Đang thẩm định' || d.status === 'needs_revision', 'approved': d.status === 'Đã thông qua' || d.status === 'approved'}"></span>
                  {{ d.status }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- AI Models Widget -->
    <div v-if="agentModels.length > 0" class="ai-models-area mt-6">
      <div class="glass-panel" style="padding: 1.5rem;">
        <h3 class="card-title">Cấu hình Mô hình AI (Agent Roles)</h3>
        <div class="table-responsive">
          <table class="dossier-table">
            <thead>
              <tr>
                <th>Vai trò (Role)</th>
                <th>Tên mô hình (Model Label)</th>
                <th>Phân hệ (Backend)</th>
                <th>Nhiệm vụ (Description)</th>
                <th>Tham số (Temp)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in agentModels" :key="m.role">
                <td class="font-medium text-primary">{{ m.role }}</td>
                <td>{{ m.label }}</td>
                <td>
                  <span class="risk-badge" :class="m.backend === 'local' ? 'medium' : 'low'">
                    {{ m.backend === 'local' ? 'Ubuntu Local' : 'Gemini Cloud' }}
                  </span>
                </td>
                <td>{{ m.description }}</td>
                <td class="font-mono">{{ m.temperature }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    </template><!-- end v-else -->
  </div>
</template>

<style scoped>
.page-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}
.page-header {
  margin-bottom: 2rem;
}
.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 0.25rem;
}
.page-subtitle {
  color: var(--color-text-secondary);
  font-size: 0.95rem;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1.5rem;
}
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.stat-icon.warning { background: rgba(245, 158, 11, 0.1); color: var(--color-warning); }
.stat-icon.danger { background: rgba(239, 68, 68, 0.1); color: var(--color-danger); }
.stat-icon.success { background: rgba(16, 185, 129, 0.1); color: var(--color-success); }

.stat-label {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  font-weight: 500;
  margin-bottom: 0.25rem;
}
.stat-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--color-text-primary);
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}
.stat-trend {
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.15rem 0.5rem;
  border-radius: 12px;
}
.stat-trend.negative { background: rgba(239, 68, 68, 0.1); color: var(--color-danger); }
.stat-trend.positive { background: rgba(16, 185, 129, 0.1); color: var(--color-success); }

.charts-area {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.chart-card {
  padding: 1.5rem;
  min-height: 300px;
}
.card-title {
  font-size: 1.1rem;
  margin-bottom: 1.5rem;
  color: var(--color-text-primary);
}
.chart-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}
.pie-mock {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  background: conic-gradient(
    var(--color-primary) 0% 40%,
    var(--color-accent) 40% 70%,
    var(--color-success) 70% 90%,
    var(--color-warning) 90% 100%
  );
  box-shadow: inset 0 0 0 30px var(--color-bg-panel);
}
.error-list {
  list-style: none;
  width: 100%;
}
.error-list li {
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
}
.dot {
  width: 10px; height: 10px; border-radius: 50%;
  flex-shrink: 0;
}
.dot.danger { background: var(--color-danger); }
.dot.warning { background: var(--color-warning); }
.dot.primary { background: var(--color-primary); }
.dot.text { background: var(--color-text-secondary); }
.dot.success { background: var(--color-success); }
.dot.accent { background: var(--color-accent); }

.no-data-msg {
  color: var(--color-text-secondary);
  font-size: 0.95rem;
  text-align: center;
}

/* Table Styles */
.mt-6 { margin-top: 2rem; }
.table-responsive { overflow-x: auto; }
.dossier-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
  color: var(--color-text-primary);
}
.dossier-table th, .dossier-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}
.dossier-table th {
  font-weight: 600;
  color: var(--color-text-secondary);
  background: rgba(0,0,0,0.02);
}
[data-theme='dark'] .dossier-table th { background: rgba(255,255,255,0.02); }
.dossier-table tr:last-child td { border-bottom: none; }
.clickable-row { cursor: pointer; }
.clickable-row:hover { background: rgba(0,0,0,0.03); }
.font-medium { font-weight: 500; }
.text-primary { color: var(--color-primary); cursor: pointer; }
.text-primary:hover { text-decoration: underline; }

.risk-badge {
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}
.risk-badge.high { background: rgba(239, 68, 68, 0.1); color: var(--color-danger); }
.risk-badge.medium { background: rgba(245, 158, 11, 0.1); color: var(--color-warning); }
.risk-badge.low { background: rgba(16, 185, 129, 0.1); color: var(--color-success); }

.status-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}
.status-dot.pending { background: var(--color-danger); }
.status-dot.processing { background: var(--color-warning); }
.status-dot.approved { background: var(--color-success); }

.dossier-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}
.dossier-card {
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  transition: all 0.2s ease;
}
.dossier-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 4px 12px rgba(0, 86, 179, 0.1);
  transform: translateY(-2px);
}
.dossier-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}
.dossier-id {
  font-weight: 600;
  color: var(--color-primary);
  font-family: monospace;
  font-size: 0.9rem;
}
.dossier-card-title {
  font-weight: 500;
  font-size: 0.95rem;
  margin-bottom: 0.75rem;
  color: var(--color-text-primary);
  line-height: 1.4;
}
.dossier-card-footer {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}
.dossier-dept { font-weight: 500; }
.dossier-date { font-family: monospace; }

.error-banner {
  padding: 1rem;
  margin-bottom: 1.5rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
  color: var(--color-danger);
}
.error-banner-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.error-icon {
  flex-shrink: 0;
}

/* Skeleton shimmer */
.skeleton-card { pointer-events: none; }
.skeleton-icon {
  width: 56px; height: 56px; border-radius: 16px;
  background: var(--color-border);
  animation: shimmer 1.4s ease-in-out infinite;
  flex-shrink: 0;
}
.skeleton-content { flex: 1; display: flex; flex-direction: column; gap: 0.6rem; }
.skeleton-line {
  height: 14px; border-radius: 6px;
  background: var(--color-border);
  animation: shimmer 1.4s ease-in-out infinite;
}
.skeleton-line.short { width: 55%; }
.skeleton-line.long { width: 80%; height: 28px; }
.skeleton-circle {
  width: 150px; height: 150px; border-radius: 50%;
  background: var(--color-border);
  animation: shimmer 1.4s ease-in-out infinite;
  margin: 0 auto;
}
@keyframes shimmer {
  0% { opacity: 1; }
  50% { opacity: 0.45; }
  100% { opacity: 1; }
}

@media (max-width: 768px) {
  .charts-area { grid-template-columns: 1fr; }
  .page-container { padding: 1rem; }
  .dossier-grid { grid-template-columns: 1fr; }
}
</style>
