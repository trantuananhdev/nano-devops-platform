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

const openDossier = (d) => {
  if (d.dossier_id) router.push(`/workspace/${d.dossier_id}`)
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
        <div class="chart-placeholder">
           <!-- Placeholder for pie chart -->
           <div class="pie-mock"></div>
        </div>
      </div>
      <div class="chart-card glass-panel">
        <h3 class="card-title">Cảnh báo lỗi phổ biến từ AI</h3>
        <div class="chart-placeholder">
          <ul class="error-list">
            <li v-for="(src, i) in alertSources" :key="src.source">
              <span class="dot" :class="i === 0 ? 'danger' : i === 1 ? 'warning' : i === 2 ? 'primary' : 'text'"></span>
              {{ src.source }} ({{ src.pct }}%)
            </li>
          </ul>
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
                <td class="font-medium text-primary">{{ d.id }}</td>
                <td>{{ d.title }}</td>
                <td>{{ d.dept }}</td>
                <td>{{ d.date }}</td>
                <td>
                  <span class="risk-badge" :class="{'high': d.risk === 'Cao', 'medium': d.risk === 'Trung bình', 'low': d.risk === 'Thấp'}">
                    {{ d.risk }}
                  </span>
                </td>
                <td>
                  <span class="status-dot" :class="{'pending': d.status === 'Chờ duyệt', 'processing': d.status === 'Đang thẩm định', 'approved': d.status === 'Đã thông qua'}"></span>
                  {{ d.status }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
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
}
.dot.danger { background: var(--color-danger); }
.dot.warning { background: var(--color-warning); }
.dot.primary { background: var(--color-primary); }
.dot.text { background: var(--color-text-secondary); }

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

@media (max-width: 768px) {
  .charts-area { grid-template-columns: 1fr; }
  .page-container { padding: 1rem; }
}
</style>
