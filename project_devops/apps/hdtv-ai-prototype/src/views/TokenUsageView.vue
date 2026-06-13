<script setup>
import { onMounted, computed, ref } from 'vue'
import { Cpu, DollarSign, Zap, TrendingUp, RefreshCw, Calendar, ChevronDown } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { useTokenUsageStore } from '../stores/tokenUsage'

const store = useTokenUsageStore()
const { summary, byRole, byDossier, dailyChartData, loading, selectedDays,
        totalTokensFormatted, costFormatted } = storeToRefs(store)

const PERIOD_OPTIONS = [
  { label: '7 ngày', value: 7 },
  { label: '30 ngày', value: 30 },
  { label: '90 ngày', value: 90 },
]

function setPeriod(days) { store.fetchAll(days) }

onMounted(() => store.fetchAll())

// Chart helpers — pure SVG bar chart, no lib needed
const CHART_H = 180
const CHART_W = 700
const BAR_GAP = 2

const chartBars = computed(() => {
  const data = dailyChartData.value
  if (!data.length) return []
  const maxVal = Math.max(...data.map(d => d.total), 1)
  const barW = Math.max(4, Math.floor((CHART_W - BAR_GAP * data.length) / data.length))
  return data.map((d, i) => ({
    x: i * (barW + BAR_GAP),
    geminiH: Math.round((d.gemini / maxVal) * CHART_H),
    localH: Math.round((d.local / maxVal) * CHART_H),
    total: d.total,
    date: d.date,
    barW,
  }))
})

// Role label map
const ROLE_LABELS = {
  planner:   'Planner',
  executor:  'Executor',
  legal:     'Legal RAG',
  financial: 'Financial',
  ocr:       'OCR',
  reflector: 'Reflector',
  critic:    'Critic',
  summary:   'Summary',
  tool_mock: 'Tool Mock',
}

function fmtTokens(n) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K`
  return String(n ?? 0)
}
function fmtCost(usd) { return `$${(usd || 0).toFixed(4)}` }
function fmtMs(ms) {
  if (!ms) return '—'
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`
  return `${ms}ms`
}
function backendBadge(b) {
  return b === 'gemini' ? 'badge-primary' : 'badge-secondary'
}
function riskPct(total, grand) {
  if (!grand) return '0%'
  return `${((total / grand) * 100).toFixed(1)}%`
}
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <div>
        <h1 class="page-title">Sử dụng Token AI</h1>
        <p class="page-subtitle">Theo dõi lượng token tiêu thụ và ước tính chi phí LLM</p>
      </div>
      <div style="display:flex;align-items:center;gap:0.75rem">
        <!-- Period selector -->
        <div style="display:flex;gap:0.375rem">
          <button
            v-for="opt in PERIOD_OPTIONS"
            :key="opt.value"
            class="btn"
            :class="selectedDays === opt.value ? 'btn-primary' : 'btn-secondary'"
            style="padding:0.375rem 0.75rem;font-size:0.8125rem"
            @click="setPeriod(opt.value)"
          >{{ opt.label }}</button>
        </div>
        <button class="btn btn-secondary" :disabled="loading" @click="store.fetchAll()">
          <RefreshCw :size="15" :class="loading ? 'spin' : ''" />
        </button>
      </div>
    </header>

    <!-- Loading skeleton -->
    <div v-if="loading && !summary" class="skeleton-grid">
      <div v-for="i in 4" :key="i" class="skeleton-card"></div>
    </div>

    <template v-else-if="summary">
      <!-- ── KPI Cards ─────────────────────────────────────────────────── -->
      <div class="kpi-grid">
        <div class="glass-panel kpi-card">
          <div class="kpi-icon kpi-icon--blue"><Cpu :size="20" /></div>
          <div>
            <p class="kpi-label">Tổng token ({{ selectedDays }} ngày)</p>
            <p class="kpi-value">{{ totalTokensFormatted }}</p>
            <p class="kpi-sub">{{ summary.total_calls }} lượt gọi LLM</p>
          </div>
        </div>

        <div class="glass-panel kpi-card">
          <div class="kpi-icon kpi-icon--green"><DollarSign :size="20" /></div>
          <div>
            <p class="kpi-label">Chi phí ước tính (Gemini)</p>
            <p class="kpi-value">{{ costFormatted }}</p>
            <p class="kpi-sub">Local (Gemma): $0.00</p>
          </div>
        </div>

        <div class="glass-panel kpi-card">
          <div class="kpi-icon kpi-icon--purple"><Zap :size="20" /></div>
          <div>
            <p class="kpi-label">Prompt tokens</p>
            <p class="kpi-value">{{ fmtTokens(summary.prompt_tokens) }}</p>
            <p class="kpi-sub">{{ fmtTokens(summary.completion_tokens) }} completion</p>
          </div>
        </div>

        <div class="glass-panel kpi-card">
          <div class="kpi-icon kpi-icon--orange"><TrendingUp :size="20" /></div>
          <div>
            <p class="kpi-label">Tỷ lệ Gemini / Local</p>
            <p class="kpi-value">
              <template v-for="b in summary.by_backend" :key="b.backend">
                <span :class="backendBadge(b.backend)" style="font-size:0.875rem;margin-right:4px">
                  {{ b.backend }}: {{ fmtTokens(b.total_tokens) }}
                </span>
              </template>
            </p>
            <p class="kpi-sub">Gemini = billed, Local = free</p>
          </div>
        </div>
      </div>

      <!-- ── Daily Usage Chart ─────────────────────────────────────────── -->
      <div class="glass-panel section-card">
        <h3 class="section-title">
          <Calendar :size="16" style="margin-right:6px;vertical-align:-2px" />
          Xu hướng theo ngày
        </h3>

        <div v-if="!dailyChartData.length" class="empty-chart">Chưa có dữ liệu token trong khoảng thời gian này.</div>

        <div v-else class="chart-wrapper">
          <svg
            :viewBox="`0 0 ${CHART_W} ${CHART_H + 30}`"
            style="width:100%;height:220px"
            preserveAspectRatio="none"
          >
            <!-- Gridlines -->
            <line v-for="i in 4" :key="i"
              x1="0" :y1="(CHART_H / 4) * i" :x2="CHART_W" :y2="(CHART_H / 4) * i"
              stroke="var(--color-border)" stroke-width="0.5"
            />
            <!-- Bars: Gemini (bottom) + Local (stacked on top) -->
            <g v-for="bar in chartBars" :key="bar.date">
              <!-- Gemini bar -->
              <rect
                :x="bar.x"
                :y="CHART_H - bar.geminiH"
                :width="bar.barW"
                :height="bar.geminiH"
                fill="var(--color-primary)"
                opacity="0.85"
                rx="1"
              >
                <title>{{ bar.date }}: Gemini {{ fmtTokens(bar.gemini) }}</title>
              </rect>
              <!-- Local bar (stacked) -->
              <rect
                :x="bar.x"
                :y="CHART_H - bar.geminiH - bar.localH"
                :width="bar.barW"
                :height="bar.localH"
                fill="#10b981"
                opacity="0.85"
                rx="1"
              >
                <title>{{ bar.date }}: Local {{ fmtTokens(bar.local) }}</title>
              </rect>
            </g>
          </svg>
          <!-- Legend -->
          <div style="display:flex;gap:1.5rem;margin-top:0.5rem;font-size:0.8125rem;color:var(--color-text-secondary)">
            <span style="display:flex;align-items:center;gap:6px">
              <span style="width:12px;height:12px;background:var(--color-primary);border-radius:2px;display:inline-block"></span>
              Gemini (billed)
            </span>
            <span style="display:flex;align-items:center;gap:6px">
              <span style="width:12px;height:12px;background:#10b981;border-radius:2px;display:inline-block"></span>
              Local / Gemma (free)
            </span>
          </div>
        </div>
      </div>

      <!-- ── By Role Table ─────────────────────────────────────────────── -->
      <div class="glass-panel section-card">
        <h3 class="section-title">Phân tích theo Agent Role</h3>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Role</th>
                <th>Backend</th>
                <th class="text-right">Calls</th>
                <th class="text-right">Prompt</th>
                <th class="text-right">Completion</th>
                <th class="text-right">Total</th>
                <th class="text-right">Avg/call</th>
                <th class="text-right">Avg latency</th>
                <th class="text-right">Cost (USD)</th>
                <th>% tổng</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!byRole.length">
                <td colspan="10" class="empty-row">Chưa có dữ liệu</td>
              </tr>
              <tr v-for="row in byRole" :key="`${row.role}-${row.backend}`">
                <td><strong>{{ ROLE_LABELS[row.role] || row.role }}</strong></td>
                <td><span :class="`badge ${backendBadge(row.backend)}`">{{ row.backend }}</span></td>
                <td class="text-right mono">{{ row.calls }}</td>
                <td class="text-right mono">{{ fmtTokens(row.prompt_tokens) }}</td>
                <td class="text-right mono">{{ fmtTokens(row.completion_tokens) }}</td>
                <td class="text-right mono"><strong>{{ fmtTokens(row.total_tokens) }}</strong></td>
                <td class="text-right mono">{{ fmtTokens(row.avg_tokens_per_call) }}</td>
                <td class="text-right mono">{{ fmtMs(row.avg_duration_ms) }}</td>
                <td class="text-right mono cost">{{ fmtCost(row.cost_usd) }}</td>
                <td>
                  <div class="progress-bar-wrap">
                    <div class="progress-bar-fill"
                      :style="`width:${riskPct(row.total_tokens, summary.total_tokens)}`"></div>
                    <span class="progress-bar-label">{{ riskPct(row.total_tokens, summary.total_tokens) }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── By Dossier Table ──────────────────────────────────────────── -->
      <div class="glass-panel section-card">
        <h3 class="section-title">Top hồ sơ tiêu thụ nhiều token nhất</h3>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Dossier ID</th>
                <th class="text-right">Calls</th>
                <th class="text-right">Prompt</th>
                <th class="text-right">Completion</th>
                <th class="text-right">Total</th>
                <th>% tổng</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!byDossier.length">
                <td colspan="7" class="empty-row">Chưa có dữ liệu hồ sơ</td>
              </tr>
              <tr v-for="(row, idx) in byDossier" :key="row.dossier_id">
                <td class="mono text-muted">{{ idx + 1 }}</td>
                <td><strong>#{{ row.dossier_id }}</strong></td>
                <td class="text-right mono">{{ row.calls }}</td>
                <td class="text-right mono">{{ fmtTokens(row.prompt_tokens) }}</td>
                <td class="text-right mono">{{ fmtTokens(row.completion_tokens) }}</td>
                <td class="text-right mono"><strong>{{ fmtTokens(row.total_tokens) }}</strong></td>
                <td>
                  <div class="progress-bar-wrap">
                    <div class="progress-bar-fill"
                      :style="`width:${riskPct(row.total_tokens, summary.total_tokens)}`"></div>
                    <span class="progress-bar-label">{{ riskPct(row.total_tokens, summary.total_tokens) }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── Cost note ─────────────────────────────────────────────────── -->
      <p class="cost-note">
        * Chi phí Gemini tính theo giá tham chiếu: $0.15/1M input tokens, $0.60/1M output tokens (Gemini 2.5 Flash, 2026).
        Local Gemma không tính phí API — chỉ tiêu thụ điện server Node 2.
      </p>
    </template>

    <div v-else-if="store.error" class="error-state">
      Lỗi tải dữ liệu: {{ store.error }}
    </div>
  </div>
</template>

<style scoped>
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin-bottom: 1.25rem;
}
.kpi-card {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.25rem;
}
.kpi-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.kpi-icon--blue   { background: rgba(26,86,219,.15); color: var(--color-primary); }
.kpi-icon--green  { background: rgba(16,185,129,.15); color: #10b981; }
.kpi-icon--purple { background: rgba(139,92,246,.15); color: #8b5cf6; }
.kpi-icon--orange { background: rgba(245,158,11,.15); color: #f59e0b; }
.kpi-label  { font-size: .8125rem; color: var(--color-text-secondary); margin-bottom: .25rem; }
.kpi-value  { font-size: 1.5rem; font-weight: 700; color: var(--color-text-primary); line-height: 1.2; }
.kpi-sub    { font-size: .75rem; color: var(--color-text-secondary); margin-top: .25rem; }

.section-card { padding: 1.25rem; margin-bottom: 1.25rem; }
.section-title {
  font-size: .9375rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
}

.chart-wrapper { overflow-x: auto; }
.empty-chart {
  text-align: center;
  padding: 3rem 0;
  color: var(--color-text-secondary);
  font-size: .875rem;
}

.table-wrapper { overflow-x: auto; }
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: .8125rem;
}
.data-table th {
  text-align: left;
  padding: .5rem .75rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}
.data-table td {
  padding: .5rem .75rem;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-primary);
}
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: var(--color-bg-hover, rgba(0,0,0,.03)); }
.text-right { text-align: right; }
.mono { font-family: monospace; }
.text-muted { color: var(--color-text-secondary); }
.cost { color: #f59e0b; font-weight: 600; }
.empty-row { text-align: center; color: var(--color-text-secondary); padding: 2rem; }

.progress-bar-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 100px;
}
.progress-bar-fill {
  height: 6px;
  background: var(--color-primary);
  border-radius: 3px;
  opacity: .7;
  transition: width .3s ease;
  min-width: 2px;
}
.progress-bar-label { font-size: .75rem; color: var(--color-text-secondary); white-space: nowrap; }

.badge { display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: .75rem; font-weight: 500; }
.badge-primary { background: rgba(26,86,219,.12); color: var(--color-primary); }
.badge-secondary { background: rgba(16,185,129,.12); color: #10b981; }

.skeleton-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.25rem; }
.skeleton-card { height: 100px; border-radius: 12px; background: var(--color-border); animation: pulse 1.5s ease infinite; }
@keyframes pulse { 0%,100%{opacity:.6} 50%{opacity:1} }

.cost-note {
  font-size: .75rem;
  color: var(--color-text-secondary);
  margin-top: .5rem;
  padding: .75rem 1rem;
  background: var(--color-bg-panel);
  border-radius: 8px;
  border-left: 3px solid var(--color-border);
}
.error-state { color: var(--color-danger, #e02424); padding: 2rem; text-align: center; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
