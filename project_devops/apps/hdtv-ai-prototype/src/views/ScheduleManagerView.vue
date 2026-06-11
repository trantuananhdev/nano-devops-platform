<script setup>
import { computed, onMounted } from 'vue'
import { CalendarClock, Plus, Play, Pause, Trash2, Edit, Activity, Clock } from '@lucide/vue'
import { useScheduleStore } from '../stores/schedule'

const store = useScheduleStore()

onMounted(() => store.fetchSchedules())

const schedules = computed(() => store.schedules)

const toggleStatus = (item) => {
  item.status = item.status === 'active' ? 'paused' : 'active'
  item.nextRun = item.status === 'paused' ? 'Đã tạm dừng' : 'Sắp tới...'
}
</script>

<template>
  <div class="page-container">
    <header class="page-header flex justify-between items-center">
      <div>
        <h1 class="page-title">Quản lý Lập lịch Tự động (AI Task Scheduler)</h1>
        <p class="page-subtitle">Thiết lập các tác vụ định kỳ để AI tự động thực thi mà không cần sự can thiệp của con người</p>
      </div>
      <button class="btn btn-primary"><Plus size="16"/> Thêm Lịch trình mới</button>
    </header>

    <div class="schedule-grid">
      <div v-for="job in schedules" :key="job.id" class="job-card glass-panel" :class="{ 'is-paused': job.status === 'paused' }">
        <div class="job-header">
          <div class="flex items-center gap-3">
            <div class="icon-box" :class="job.status">
              <CalendarClock size="24"/>
            </div>
            <div>
              <h3 class="job-name">{{ job.name }}</h3>
              <div class="cron-badge">{{ job.cron }}</div>
            </div>
          </div>
          <div class="job-actions">
            <button class="btn-icon" title="Sửa"><Edit size="16"/></button>
            <button class="btn-icon text-danger" title="Xóa"><Trash2 size="16"/></button>
          </div>
        </div>

        <div class="job-body">
          <p class="job-desc">{{ job.description }}</p>
          
          <div class="info-row">
            <span class="label">Tần suất:</span>
            <span class="value font-medium">{{ job.scheduleText }}</span>
          </div>
          
          <div class="info-row">
            <span class="label">Công cụ kích hoạt:</span>
            <div class="flex gap-1 flex-wrap">
              <span v-for="tool in job.tools" :key="tool" class="tool-badge">{{ tool }}</span>
            </div>
          </div>
        </div>

        <div class="job-footer">
          <div class="timing-info">
            <div class="flex items-center gap-1 text-xs text-muted mb-1">
              <Activity size="12"/> Lần chạy cuối: {{ job.lastRun }}
            </div>
            <div class="flex items-center gap-1 text-xs font-semibold" :class="job.status === 'active' ? 'text-primary' : 'text-muted'">
              <Clock size="12"/> Tiếp theo: {{ job.nextRun }}
            </div>
          </div>
          
          <button 
            class="btn btn-sm" 
            :class="job.status === 'active' ? 'btn-outline-danger' : 'btn-outline-success'"
            @click="toggleStatus(job)"
          >
            <component :is="job.status === 'active' ? Pause : Play" size="14"/>
            {{ job.status === 'active' ? 'Tạm dừng' : 'Kích hoạt' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container { padding: 2rem; max-width: 1400px; margin: 0 auto; }
.page-header { margin-bottom: 2rem; }
.page-title { font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; }
.page-subtitle { color: var(--color-text-secondary); }

.schedule-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 1.5rem;
}

.job-card {
  display: flex;
  flex-direction: column;
  transition: all 0.3s;
}
.job-card.is-paused {
  opacity: 0.8;
  filter: grayscale(0.5);
}

.job-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.icon-box {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}
.icon-box.active { background: linear-gradient(135deg, var(--color-primary), #2563eb); }
.icon-box.paused { background: var(--color-border); color: var(--color-text-secondary); }

.job-name { font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem; }
.cron-badge { display: inline-block; font-family: monospace; background: rgba(0,0,0,0.05); padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.75rem; color: var(--color-text-secondary); }
[data-theme='dark'] .cron-badge { background: rgba(255,255,255,0.1); }

.job-actions { display: flex; gap: 0.25rem; }
.text-danger { color: var(--color-danger); }

.job-body {
  padding: 1.5rem;
  flex: 1;
}
.job-desc {
  font-size: 0.9rem;
  line-height: 1.5;
  color: var(--color-text-secondary);
  margin-bottom: 1.5rem;
}

.info-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 1rem;
}
.info-row:last-child { margin-bottom: 0; }
.info-row .label { font-size: 0.85rem; color: var(--color-text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
.font-medium { font-weight: 500; font-size: 0.9rem; }
.tool-badge {
  background: rgba(16, 185, 129, 0.1);
  color: var(--color-success);
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.job-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-border);
  background: rgba(0,0,0,0.01);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
[data-theme='dark'] .job-footer { background: rgba(255,255,255,0.01); }

.timing-info { display: flex; flex-direction: column; }
.text-xs { font-size: 0.75rem; }
.text-muted { color: var(--color-text-secondary); }
.text-primary { color: var(--color-primary); }
.font-semibold { font-weight: 600; }
.mb-1 { margin-bottom: 0.25rem; }

.btn-sm { padding: 0.4rem 0.75rem; font-size: 0.85rem; display: flex; align-items: center; gap: 0.4rem; }
.btn-outline-danger { border: 1px solid var(--color-danger); color: var(--color-danger); background: transparent; cursor: pointer; border-radius: 6px; }
.btn-outline-danger:hover { background: rgba(239, 68, 68, 0.1); }
.btn-outline-success { border: 1px solid var(--color-success); color: var(--color-success); background: transparent; cursor: pointer; border-radius: 6px; }
.btn-outline-success:hover { background: rgba(16, 185, 129, 0.1); }
</style>
