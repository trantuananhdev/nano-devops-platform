<script setup>
import { ref, onMounted } from 'vue'
import { Users, Shield, ScrollText, UserPlus, Search, Edit2, Trash2, Key, Filter, CheckCircle2, AlertTriangle, Info, Terminal, Activity, X, Brain, GitBranch, ThumbsDown, Database, Plus, Eye, EyeOff, Copy } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { useAdminStore } from '../stores/admin'

const activeTab = ref('users')
const adminStore = useAdminStore()
const { toolAudits, users, roles, systemLogs, agentMetrics, apiKeys, mcpLogs, mcpLogsFiltered, mcpToolFilter } = storeToRefs(adminStore)

onMounted(() => adminStore.fetchAll())

const pct = (rate) => `${((rate ?? 0) * 100).toFixed(1)}%`

const selectedAudit = ref(null)

// T-33: API Keys state
const showAddKeyModal = ref(false)
const newKeyForm = ref({ name: '', key_type: 'gemini', raw_key: '' })
const newKeyResult = ref(null)   // masked_key shown once after creation
const keyTypeFilter = ref('')
const showRawKey = ref(false)
const copiedKeyId = ref(null)

async function submitNewKey() {
  try {
    const result = await adminStore.addApiKey({ ...newKeyForm.value })
    newKeyResult.value = result
    newKeyForm.value = { name: '', key_type: 'gemini', raw_key: '' }
  } catch (err) {
    alert('Lỗi tạo API key: ' + (err?.response?.data?.detail || err.message))
  }
}

async function confirmDelete(keyId, keyName) {
  if (!confirm(`Xác nhận vô hiệu hoá key "${keyName}"?`)) return
  await adminStore.removeApiKey(keyId)
}

function copyToClipboard(text, id) {
  navigator.clipboard.writeText(text).then(() => {
    copiedKeyId.value = id
    setTimeout(() => { copiedKeyId.value = null }, 2000)
  })
}

function closeAddKeyModal() {
  showAddKeyModal.value = false
  newKeyResult.value = null
  showRawKey.value = false
}

const KEY_TYPE_LABELS = {
  gemini: 'Gemini AI',
  mcp: 'MCP Server',
  minio: 'MinIO / S3',
  internal: 'Internal',
}
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <div>
        <h1 class="page-title">Quản trị Hệ thống</h1>
        <p class="page-subtitle">Quản lý định danh, phân quyền và giám sát hoạt động</p>
      </div>
    </header>

    <div class="admin-layout">
      <!-- Sidebar Tabs -->
      <aside class="admin-sidebar glass-panel">
        <nav class="tabs-nav">
          <button class="tab-btn" :class="{ active: activeTab === 'users' }" @click="activeTab = 'users'">
            <Users size="18" /> Quản lý Người dùng
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'roles' }" @click="activeTab = 'roles'">
            <Shield size="18" /> Phân quyền
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'logs' }" @click="activeTab = 'logs'">
            <ScrollText size="18" /> Nhật ký Hệ thống
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'tool_audits' }" @click="activeTab = 'tool_audits'">
            <Terminal size="18" /> Kiểm toán Công cụ (AI)
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'agent_intel' }" @click="activeTab = 'agent_intel'">
            <Brain size="18" /> Agent Intelligence
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'api_keys' }" @click="activeTab = 'api_keys'">
            <Key size="18" /> Quản lý API Keys
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'mcp_audit' }" @click="activeTab = 'mcp_audit'">
            <Activity size="18" /> MCP Audit Logs
          </button>
        </nav>
      </aside>

      <!-- Content Area -->
      <main class="admin-content glass-panel">
        
        <!-- Tab 1: Users -->
        <div v-if="activeTab === 'users'" class="tab-pane">
          <div class="pane-header">
            <h2>Danh sách Người dùng</h2>
            <div class="actions">
              <div class="search-box">
                <Search size="16" class="text-muted"/>
                <input type="text" placeholder="Tìm kiếm tên, email..."/>
              </div>
              <button class="btn btn-primary flex-center gap-2"><UserPlus size="16"/> Thêm mới</button>
            </div>
          </div>
          <table class="data-table mt-4">
            <thead>
              <tr>
                <th>Mã NV</th>
                <th>Họ và tên</th>
                <th>Email / Tài khoản</th>
                <th>Phòng ban</th>
                <th>Vai trò</th>
                <th>Trạng thái</th>
                <th width="100">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in users" :key="u.id">
                <td class="font-medium">{{ u.id }}</td>
                <td>{{ u.name }}</td>
                <td>{{ u.email }}</td>
                <td>{{ u.dept }}</td>
                <td><span class="role-badge">{{ u.role }}</span></td>
                <td>
                  <span class="status-badge" :class="u.status === 'Hoạt động' ? 'pass' : 'fail'">{{ u.status }}</span>
                </td>
                <td>
                  <div class="flex gap-2">
                    <button class="btn-icon" title="Chỉnh sửa"><Edit2 size="16"/></button>
                    <button class="btn-icon text-danger" title="Khóa"><Trash2 size="16"/></button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Tab 2: Roles -->
        <div v-if="activeTab === 'roles'" class="tab-pane">
          <div class="pane-header">
            <h2>Nhóm Quyền (Roles)</h2>
            <div class="actions">
              <button class="btn btn-primary flex-center gap-2"><Key size="16"/> Tạo Nhóm quyền</button>
            </div>
          </div>
          <div class="roles-grid mt-4">
            <div v-for="r in roles" :key="r.id" class="role-card glass-panel">
              <div class="role-header">
                <h3>{{ r.name }}</h3>
                <span class="badge primary">{{ r.usersCount }} Users</span>
              </div>
              <p class="role-desc">{{ r.desc }}</p>
              <div class="role-actions">
                <button class="btn btn-outline btn-sm">Chi tiết Quyền</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 3: System Logs -->
        <div v-if="activeTab === 'logs'" class="tab-pane">
          <div class="pane-header">
            <h2>Nhật ký Hoạt động (Audit Logs)</h2>
            <div class="actions">
              <div class="search-box">
                <Filter size="16" class="text-muted"/>
                <select class="border-none bg-transparent outline-none">
                  <option>Tất cả sự kiện</option>
                  <option>Lỗi hệ thống</option>
                  <option>Thao tác người dùng</option>
                </select>
              </div>
            </div>
          </div>
          <table class="data-table mt-4">
            <thead>
              <tr>
                <th width="180">Thời gian</th>
                <th>Người dùng / Tác nhân</th>
                <th>Hành động</th>
                <th>Chi tiết</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in systemLogs" :key="log.id">
                <td class="text-muted text-sm">{{ log.time }}</td>
                <td class="font-medium">{{ log.user }}</td>
                <td>
                  <div class="flex items-center gap-2">
                    <CheckCircle2 v-if="log.type === 'success'" size="14" class="text-success"/>
                    <AlertTriangle v-if="log.type === 'danger'" size="14" class="text-danger"/>
                    <Info v-if="log.type === 'info'" size="14" class="text-primary"/>
                    <AlertTriangle v-if="log.type === 'warning'" size="14" style="color:var(--color-warning)"/>
                    {{ log.action }}
                  </div>
                </td>
                <td class="text-sm">{{ log.details }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Tab 5: Agent Intelligence (T-24) -->
        <div v-if="activeTab === 'agent_intel'" class="tab-pane">
          <div class="pane-header">
            <h2>Agent Intelligence — Level 4 KPIs</h2>
            <div class="actions">
              <button class="btn btn-outline btn-sm" @click="adminStore.fetchAgentMetrics()">Làm mới</button>
            </div>
          </div>

          <div v-if="agentMetrics" class="metrics-grid mt-4">
            <div class="metric-card glass-panel">
              <div class="metric-icon primary"><GitBranch size="22" /></div>
              <div class="metric-body">
                <div class="metric-label">Tỷ lệ sửa kế hoạch</div>
                <div class="metric-value">{{ pct(agentMetrics.plan_revision_rate) }}</div>
                <div class="metric-sub">{{ agentMetrics.revised_plans }} / {{ agentMetrics.total_plans }} kế hoạch</div>
              </div>
            </div>

            <div class="metric-card glass-panel">
              <div class="metric-icon danger"><ThumbsDown size="22" /></div>
              <div class="metric-body">
                <div class="metric-label">Tỷ lệ Critic từ chối</div>
                <div class="metric-value">{{ pct(agentMetrics.critic_rejection_rate) }}</div>
                <div class="metric-sub">{{ agentMetrics.critic_rejections }} / {{ agentMetrics.total_appraisals }} thẩm định</div>
              </div>
            </div>

            <div class="metric-card glass-panel">
              <div class="metric-icon success"><CheckCircle2 size="22" /></div>
              <div class="metric-body">
                <div class="metric-label">Phản hồi người dùng</div>
                <div class="metric-value">{{ agentMetrics.feedback_total }}</div>
                <div class="metric-sub">
                  👍 {{ agentMetrics.feedback_approve }} · 👎 {{ agentMetrics.feedback_reject }} · ✏️ {{ agentMetrics.feedback_adjust }}
                </div>
              </div>
            </div>

            <div class="metric-card glass-panel">
              <div class="metric-icon warning"><Database size="22" /></div>
              <div class="metric-body">
                <div class="metric-label">Bộ nhớ Agent</div>
                <div class="metric-value">{{ agentMetrics.memory_retrieval_count }}</div>
                <div class="metric-sub">{{ agentMetrics.memories_indexed }} đã index Chroma · {{ agentMetrics.tool_calls_total }} tool calls</div>
              </div>
            </div>
          </div>

          <p v-else class="text-muted mt-4">Đang tải metrics...</p>
        </div>

        <!-- Tab 6: API Keys Management (T-33) -->
        <div v-if="activeTab === 'api_keys'" class="tab-pane">
          <div class="pane-header">
            <h2>Quản lý API Keys</h2>
            <div class="actions">
              <select
                v-model="keyTypeFilter"
                class="filter-select"
                @change="adminStore.fetchApiKeys(keyTypeFilter || null)"
              >
                <option value="">Tất cả loại</option>
                <option value="gemini">Gemini AI</option>
                <option value="mcp">MCP Server</option>
                <option value="minio">MinIO / S3</option>
                <option value="internal">Internal</option>
              </select>
              <button class="btn btn-primary flex-center gap-2" @click="showAddKeyModal = true">
                <Plus size="16" /> Thêm API Key
              </button>
            </div>
          </div>

          <table class="data-table mt-4">
            <thead>
              <tr>
                <th width="60">ID</th>
                <th>Tên</th>
                <th>Loại</th>
                <th>Prefix</th>
                <th>Trạng thái</th>
                <th>Lần cuối dùng</th>
                <th>Tạo lúc</th>
                <th width="100">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="k in apiKeys" :key="k.id">
                <td class="text-muted">{{ k.id }}</td>
                <td class="font-medium">{{ k.name }}</td>
                <td>
                  <span class="key-type-badge" :class="k.key_type">
                    {{ KEY_TYPE_LABELS[k.key_type] || k.key_type }}
                  </span>
                </td>
                <td class="font-mono text-sm">{{ k.key_prefix }}…</td>
                <td>
                  <span class="status-badge" :class="k.is_active ? 'pass' : 'fail'">
                    {{ k.is_active ? 'Hoạt động' : 'Vô hiệu' }}
                  </span>
                </td>
                <td class="text-sm text-muted">
                  {{ k.last_used_at ? new Date(k.last_used_at).toLocaleString('vi-VN') : '—' }}
                </td>
                <td class="text-sm text-muted">
                  {{ new Date(k.created_at).toLocaleString('vi-VN') }}
                </td>
                <td>
                  <button
                    v-if="k.is_active"
                    class="btn-icon text-danger"
                    title="Vô hiệu hoá key"
                    @click="confirmDelete(k.id, k.name)"
                  >
                    <Trash2 size="16" />
                  </button>
                  <span v-else class="text-muted text-sm">—</span>
                </td>
              </tr>
              <tr v-if="apiKeys.length === 0">
                <td colspan="8" class="text-center text-muted py-4">Chưa có API key nào. Thêm key để quản lý tập trung.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Tab 7: MCP Audit Logs (T-36) -->
        <div v-if="activeTab === 'mcp_audit'" class="tab-pane">
          <div class="pane-header">
            <h2>MCP Audit Logs</h2>
            <div class="actions">
              <div class="search-box">
                <Filter size="16" class="text-muted"/>
                <input v-model="mcpToolFilter" type="text" placeholder="Lọc tool_name..."/>
              </div>
              <button class="btn btn-outline btn-sm" @click="loadMcpLogs">Làm mới</button>
            </div>
          </div>
          <table class="data-table mt-4">
            <thead>
              <tr>
                <th width="70">ID</th>
                <th width="160">Thời gian</th>
                <th>Tool</th>
                <th>API Key prefix</th>
                <th width="90">Streaming</th>
                <th>Thời gian XL</th>
                <th>Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in mcpLogsFiltered" :key="log.id">
                <td class="text-muted">{{ log.id }}</td>
                <td class="text-sm">{{ new Date(log.created_at).toLocaleString('vi-VN') }}</td>
                <td class="font-medium text-primary">{{ log.tool_name }}</td>
                <td class="font-mono text-sm">{{ log.api_key_prefix }}…</td>
                <td>
                  <span v-if="log.is_streaming" class="role-badge">SSE</span>
                  <span v-else class="text-muted text-sm">sync</span>
                </td>
                <td class="text-sm">{{ log.execution_ms }}ms</td>
                <td>
                  <span class="status-badge" :class="log.is_error ? 'fail' : (log.output_incomplete ? 'warn' : 'pass')">
                    {{ log.is_error ? 'Lỗi' : (log.output_incomplete ? 'Thiếu field' : 'OK') }}
                  </span>
                </td>
              </tr>
              <tr v-if="mcpLogs.length === 0">
                <td colspan="7" class="text-center text-muted py-4">Chưa có MCP call nào. Gọi /mcp/tools/call để tạo log.</td>
              </tr>
            </tbody>
          </table>
          <div class="text-sm text-muted mt-4" style="padding: 0 1rem;">
            Hiển thị {{ mcpLogsFiltered.length }} / {{ mcpLogs.length }} calls · Dữ liệu từ <code>mcp_call_logs</code> table
          </div>
        </div>

        <!-- Tab 4: Tool Audits -->
        <div v-if="activeTab === 'tool_audits'" class="tab-pane">
          <div class="pane-header">
            <h2>Kiểm toán Lệnh gọi Công cụ (Tool Audits)</h2>
            <div class="actions">
              <div class="search-box">
                <Search size="16" class="text-muted"/>
                <input type="text" placeholder="Tìm kiếm tool_name..."/>
              </div>
            </div>
          </div>
          <table class="data-table mt-4">
            <thead>
              <tr>
                <th width="100">ID</th>
                <th width="160">Thời gian</th>
                <th>Công cụ (Tool)</th>
                <th>Tác nhân gọi</th>
                <th>Thời gian xử lý</th>
                <th>Trạng thái</th>
                <th width="120">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="audit in toolAudits" :key="audit.id">
                <td class="font-medium text-muted">{{ audit.id }}</td>
                <td class="text-sm">{{ audit.timestamp }}</td>
                <td class="font-medium text-primary">{{ audit.tool }}</td>
                <td>{{ audit.caller }}</td>
                <td class="text-sm">{{ audit.duration }}</td>
                <td>
                  <span class="status-badge" :class="audit.status === 'success' ? 'pass' : 'fail'">{{ audit.status === 'success' ? 'Thành công' : 'Thất bại' }}</span>
                </td>
                <td>
                  <button class="btn btn-outline btn-sm flex-center gap-1" @click="selectedAudit = audit">
                    <Activity size="14"/> Chi tiết
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

      </main>
    </div>

    <!-- T-33: Add API Key Modal -->
    <div v-if="showAddKeyModal" class="modal-overlay" @click="closeAddKeyModal">
      <div class="modal-content glass-panel" style="width: 520px;" @click.stop>
        <div class="modal-header">
          <h3 class="flex items-center gap-2"><Key size="20" class="text-primary" /> Thêm API Key mới</h3>
          <button class="btn-icon" @click="closeAddKeyModal"><X size="20" /></button>
        </div>

        <!-- Show masked key after creation -->
        <div v-if="newKeyResult" class="modal-body">
          <div class="key-created-banner">
            <CheckCircle2 size="20" class="text-success" />
            <span>Key đã được lưu thành công. Đây là lần duy nhất bạn thấy key đầy đủ:</span>
          </div>
          <div class="key-preview-box mt-4">
            <div class="flex items-center gap-2">
              <span class="font-mono text-sm flex-1">{{ showRawKey ? '(bị ẩn vì lý do bảo mật)' : newKeyResult.masked_key }}</span>
              <button class="btn-icon" @click="copyToClipboard(newKeyResult.masked_key, 'new')" title="Copy">
                <Copy size="16" :class="copiedKeyId === 'new' ? 'text-success' : ''" />
              </button>
            </div>
          </div>
          <p class="text-sm text-muted mt-3">Prefix để nhận diện: <code>{{ newKeyResult.key_prefix }}…</code></p>
        </div>

        <!-- Create form -->
        <div v-else class="modal-body">
          <div class="form-group">
            <label class="form-label">Tên gợi nhớ *</label>
            <input v-model="newKeyForm.name" class="form-input" placeholder="vd: Gemini prod key 1" />
          </div>
          <div class="form-group mt-3">
            <label class="form-label">Loại key *</label>
            <select v-model="newKeyForm.key_type" class="form-input">
              <option value="gemini">Gemini AI</option>
              <option value="mcp">MCP Server</option>
              <option value="minio">MinIO / S3</option>
              <option value="internal">Internal</option>
            </select>
          </div>
          <div class="form-group mt-3">
            <label class="form-label">Giá trị key *</label>
            <div class="key-input-wrap">
              <input
                v-model="newKeyForm.raw_key"
                :type="showRawKey ? 'text' : 'password'"
                class="form-input"
                placeholder="AIzaSy... hoặc key thực tế"
                autocomplete="off"
              />
              <button class="btn-icon key-toggle" @click="showRawKey = !showRawKey">
                <Eye v-if="!showRawKey" size="16" />
                <EyeOff v-else size="16" />
              </button>
            </div>
            <p class="form-hint">Key sẽ được hash bằng bcrypt ngay sau khi lưu. Với Gemini keys, hệ thống dùng base64 để llm_router có thể lấy lại khi cần.</p>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-outline" @click="closeAddKeyModal">
            {{ newKeyResult ? 'Đóng' : 'Huỷ' }}
          </button>
          <button
            v-if="!newKeyResult"
            class="btn btn-primary"
            :disabled="!newKeyForm.name || !newKeyForm.raw_key"
            @click="submitNewKey"
          >
            Lưu Key
          </button>
        </div>
      </div>
    </div>

    <!-- Audit Details Modal -->
    <div v-if="selectedAudit" class="modal-overlay" @click="selectedAudit = null">
      <div class="modal-content glass-panel" style="width: 700px;" @click.stop>
        <div class="modal-header">
          <h3 class="flex items-center gap-2">
            <Terminal size="20" class="text-primary" />
            Chi tiết gọi: {{ selectedAudit.tool }}
          </h3>
          <button class="btn-icon" @click="selectedAudit = null"><X size="20"/></button>
        </div>
        <div class="modal-body code-modal">
          <div class="info-grid">
            <div class="info-item">
              <span class="lbl">Trạng thái:</span>
              <span class="status-badge inline-block mt-1" :class="selectedAudit.status === 'success' ? 'pass' : 'fail'">{{ selectedAudit.status.toUpperCase() }}</span>
            </div>
            <div class="info-item">
              <span class="lbl">Thời gian xử lý:</span>
              <div class="font-medium mt-1">{{ selectedAudit.duration }}</div>
            </div>
            <div class="info-item">
              <span class="lbl">Tác nhân gọi:</span>
              <div class="font-medium mt-1">{{ selectedAudit.caller }}</div>
            </div>
          </div>

          <h4 class="mt-4 mb-2">Input (Parameters)</h4>
          <pre class="code-block">{{ selectedAudit.inputs }}</pre>

          <h4 class="mt-4 mb-2">Output (Response)</h4>
          <pre class="code-block">{{ selectedAudit.outputs }}</pre>
        </div>
        <div class="modal-footer">
          <button class="btn btn-primary" @click="selectedAudit = null">Đóng</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container { padding: 2rem; max-width: 1400px; margin: 0 auto; height: 100vh; display: flex; flex-direction: column; }
.page-header { margin-bottom: 2rem; }
.page-title { font-size: 1.75rem; font-weight: 700; color: var(--color-text-primary); margin-bottom: 0.25rem; }
.page-subtitle { color: var(--color-text-secondary); font-size: 0.95rem; }

.admin-layout {
  flex: 1;
  display: flex;
  gap: 1.5rem;
  overflow: hidden;
}

/* Sidebar */
.admin-sidebar {
  width: 260px;
  padding: 1.5rem;
  border-radius: 12px;
}
.tabs-nav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.tab-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: var(--color-text-secondary);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}
.tab-btn:hover { background: rgba(0,0,0,0.03); color: var(--color-text-primary); }
[data-theme='dark'] .tab-btn:hover { background: rgba(255,255,255,0.05); }
.tab-btn.active {
  background: var(--color-primary);
  color: white;
  box-shadow: 0 4px 12px rgba(0, 86, 179, 0.2);
}

/* Content Area */
.admin-content {
  flex: 1;
  border-radius: 12px;
  padding: 2rem;
  overflow-y: auto;
}

.pane-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 1.5rem;
}
.pane-header h2 { font-size: 1.25rem; font-weight: 600; color: var(--color-text-primary); }
.actions { display: flex; gap: 1rem; }

.search-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--color-bg-base);
  border: 1px solid var(--color-border);
  border-radius: 20px;
}
.search-box input { border: none; background: transparent; outline: none; color: var(--color-text-primary); }

.flex-center { display: flex; align-items: center; justify-content: center; }
.mt-4 { margin-top: 1.5rem; }
.text-muted { color: var(--color-text-secondary); }
.text-sm { font-size: 0.85rem; }
.font-medium { font-weight: 500; }
.text-success { color: var(--color-success); }
.text-danger { color: var(--color-danger); }
.text-primary { color: var(--color-primary); }

/* Tables */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}
.data-table th, .data-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}
.data-table th { font-weight: 600; color: var(--color-text-secondary); }
.data-table tr:last-child td { border-bottom: none; }

.role-badge {
  background: rgba(0, 86, 179, 0.1);
  color: var(--color-primary);
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 600;
}
.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}
.status-badge.pass { background: rgba(16, 185, 129, 0.1); color: var(--color-success); }
.status-badge.fail { background: rgba(239, 68, 68, 0.1); color: var(--color-danger); }

/* Roles Grid */
.roles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}
.role-card {
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
}
.role-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; }
.role-header h3 { font-size: 1.1rem; font-weight: 600; margin: 0; }
.badge.primary { background: var(--color-primary); color: white; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
.role-desc { font-size: 0.9rem; color: var(--color-text-secondary); flex: 1; line-height: 1.5; margin-bottom: 1.5rem; }

/* Agent Intelligence metrics (T-24) */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1.25rem;
}
.metric-card {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  border-radius: 12px;
  border: 1px solid var(--color-border);
  align-items: flex-start;
}
.metric-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.metric-icon.primary { background: rgba(0, 86, 179, 0.12); color: var(--color-primary); }
.metric-icon.danger { background: rgba(239, 68, 68, 0.12); color: var(--color-danger); }
.metric-icon.success { background: rgba(16, 185, 129, 0.12); color: var(--color-success); }
.metric-icon.warning { background: rgba(245, 158, 11, 0.12); color: var(--color-warning, #f59e0b); }
.metric-label { font-size: 0.85rem; color: var(--color-text-secondary); margin-bottom: 0.25rem; }
.metric-value { font-size: 1.5rem; font-weight: 700; color: var(--color-text-primary); }
.metric-sub { font-size: 0.8rem; color: var(--color-text-secondary); margin-top: 0.35rem; }

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}
.modal-content {
  max-width: 90vw;
  background: var(--color-bg-panel);
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}
.modal-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-header h3 { font-size: 1.1rem; margin: 0; }
.modal-body { padding: 1.5rem; flex: 1; overflow-y: auto; }
.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
}
.info-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1rem; background: rgba(0,0,0,0.02); padding: 1rem; border-radius: 8px; }
[data-theme='dark'] .info-grid { background: rgba(255,255,255,0.02); }
.lbl { font-size: 0.8rem; color: var(--color-text-secondary); text-transform: uppercase; }
.mb-2 { margin-bottom: 0.5rem; }
.inline-block { display: inline-block; }

.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 1rem;
  border-radius: 8px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9rem;
  overflow-x: auto;
}

@media (max-width: 768px) {
  .admin-layout { flex-direction: column; overflow: auto; }
  .admin-sidebar { width: 100%; }
  .tabs-nav { flex-direction: row; overflow-x: auto; }
  .tab-btn { white-space: nowrap; }
}

/* T-33: API Keys tab */
.filter-select {
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 20px;
  background: var(--color-bg-base);
  color: var(--color-text-primary);
  outline: none;
  font-size: 0.9rem;
}

.key-type-badge {
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
}
.key-type-badge.gemini { background: rgba(66, 133, 244, 0.12); color: #4285f4; }
.key-type-badge.mcp    { background: rgba(0, 86, 179, 0.12); color: var(--color-primary); }
.key-type-badge.minio  { background: rgba(255, 143, 0, 0.12); color: #ff8f00; }
.key-type-badge.internal { background: rgba(16, 185, 129, 0.12); color: var(--color-success); }

.font-mono { font-family: 'Courier New', Courier, monospace; }
.py-4 { padding-top: 1rem; padding-bottom: 1rem; }
.text-center { text-align: center; }
.gap-2 { gap: 0.5rem; }
.flex-1 { flex: 1; }

/* Add key modal form */
.form-group { display: flex; flex-direction: column; }
.form-label { font-size: 0.85rem; font-weight: 600; color: var(--color-text-secondary); margin-bottom: 0.4rem; }
.form-input {
  padding: 0.6rem 0.9rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-base);
  color: var(--color-text-primary);
  outline: none;
  font-size: 0.95rem;
  width: 100%;
  box-sizing: border-box;
}
.form-input:focus { border-color: var(--color-primary); }
.form-hint { font-size: 0.8rem; color: var(--color-text-secondary); margin-top: 0.4rem; line-height: 1.5; }

.key-input-wrap { position: relative; display: flex; align-items: center; }
.key-input-wrap .form-input { padding-right: 2.5rem; }
.key-toggle { position: absolute; right: 0.5rem; color: var(--color-text-secondary); }

.key-created-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 8px;
  font-size: 0.9rem;
  line-height: 1.5;
}
.key-preview-box {
  background: #1e1e1e;
  color: #d4d4d4;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  display: flex;
  align-items: center;
}
</style>
