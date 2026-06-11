<script setup>
import { computed, onMounted, ref } from 'vue'
import { Plus, Settings2, Database, MessageSquareCode, Save, Trash2 } from '@lucide/vue'
import { useSkillsStore } from '../stores/skills'
import { useDossierStore } from '../stores/dossier'

const skillsStore = useSkillsStore()
const dossierStore = useDossierStore()
const selectedDocType = ref('')

const docTypes = computed(() => dossierStore.dossiers.map((d) => d.title))
const skills = computed(() => skillsStore.skills)

onMounted(async () => {
  await dossierStore.fetchDossiers()
  await skillsStore.fetchSkills()
  selectedDocType.value = docTypes.value[0] || 'Tờ trình mặc định'
})
</script>

<template>
  <div class="page-container">
    <header class="page-header flex justify-between items-center">
      <div>
        <h1 class="page-title">Hệ thống Đào tạo Trợ lý AI</h1>
        <p class="page-subtitle">Thiết lập quy tắc và kỹ năng phân tích cho từng nhóm Tờ trình nghiệp vụ</p>
      </div>
      <button class="btn btn-primary"><Plus size="16"/> Thêm Kỹ năng mới</button>
    </header>

    <div class="skill-builder-layout">
      <!-- Left Sidebar: Document Types -->
      <div class="doc-types-panel glass-panel">
        <div class="panel-header">
          <h3>Danh mục Loại Tờ trình</h3>
          <button class="btn-icon"><Plus size="16"/></button>
        </div>
        <ul class="type-list">
          <li 
            v-for="type in docTypes" 
            :key="type" 
            :class="{ active: selectedDocType === type }"
            @click="selectedDocType = type"
          >
            {{ type }}
          </li>
        </ul>
      </div>

      <!-- Right Panel: Skill Configuration -->
      <div class="skill-config-panel">
        <div class="config-header">
          <h2>Kỹ năng cấu hình cho: <span class="highlight">{{ selectedDocType }}</span></h2>
        </div>
        
        <div class="skills-grid">
          <div v-for="skill in skills" :key="skill.id" class="skill-card glass-panel">
            <div class="skill-card-header flex justify-between items-center">
              <div class="skill-title flex items-center gap-2">
                <Database v-if="skill.type === 'api_crosscheck'" size="18" class="icon-api"/>
                <MessageSquareCode v-else size="18" class="icon-prompt"/>
                <h4>{{ skill.name }}</h4>
              </div>
              <div class="toggle-switch">
                <input type="checkbox" :checked="skill.isActive" />
                <span class="slider"></span>
              </div>
            </div>
            
            <p class="skill-desc">{{ skill.description }}</p>
            
            <div class="skill-details markdown-editor">
              <div class="editor-toolbar flex gap-2">
                <button class="btn-icon"><span class="font-medium">H1</span></button>
                <button class="btn-icon"><span class="font-medium">H2</span></button>
                <button class="btn-icon font-medium" style="font-weight: bold;">B</button>
                <button class="btn-icon font-medium" style="font-style: italic;">I</button>
                <div style="flex:1"></div>
                <span style="font-size: 0.8rem; color: var(--color-text-secondary);">Hỗ trợ cú pháp Markdown chuẩn</span>
              </div>
              <textarea rows="18" :value="skill.markdownContent" class="form-control code-font markdown-textarea" spellcheck="false" readonly></textarea>
            </div>

            <div class="skill-actions">
              <button class="btn btn-outline"><Settings2 size="14"/> Chạy Thử nghiệm</button>
              <div class="right-actions">
                <button class="btn-icon danger"><Trash2 size="16"/></button>
                <button class="btn btn-primary"><Save size="14"/> Lưu Cấu hình</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container { padding: 2rem; max-width: 1400px; margin: 0 auto; height: 100%; display: flex; flex-direction: column; }
.page-header { margin-bottom: 2rem; }
.page-title { font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; }
.page-subtitle { color: var(--color-text-secondary); }

.skill-builder-layout {
  display: flex;
  gap: 1.5rem;
  flex: 1;
  min-height: 0;
}

/* Left Panel */
.doc-types-panel {
  width: 300px;
  display: flex;
  flex-direction: column;
}
.panel-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.panel-header h3 { font-size: 1rem; margin: 0; }
.type-list {
  list-style: none;
  overflow-y: auto;
}
.type-list li {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  transition: background 0.2s;
  font-weight: 500;
}
.type-list li:hover { background: rgba(0,0,0,0.02); }
[data-theme='dark'] .type-list li:hover { background: rgba(255,255,255,0.02); }
.type-list li.active {
  background: rgba(0, 86, 179, 0.05);
  border-left: 4px solid var(--color-primary);
  color: var(--color-primary);
}
[data-theme='dark'] .type-list li.active { background: rgba(59, 130, 246, 0.1); }

/* Right Panel */
.skill-config-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding-right: 0.5rem;
}
.config-header { margin-bottom: 1.5rem; }
.config-header h2 { font-size: 1.25rem; font-weight: 600; }
.highlight { color: var(--color-primary); }

.skills-grid {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.skill-card {
  padding: 1.5rem;
}
.skill-card-header { margin-bottom: 1rem; }
.skill-title h4 { font-size: 1.1rem; margin: 0; }
.icon-api { color: var(--color-success); }
.icon-prompt { color: var(--color-primary); }
.skill-desc {
  color: var(--color-text-secondary);
  font-size: 0.95rem;
  margin-bottom: 1.5rem;
}

.skill-details {
  background: var(--color-bg-base);
  padding: 1.25rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  margin-bottom: 1.5rem;
}
.form-group { margin-bottom: 1rem; }
.form-group:last-child { margin-bottom: 0; }
.form-group label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 0.5rem;
}
.form-control {
  width: 100%;
  padding: 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-panel-solid);
  color: var(--color-text-primary);
}
.code-font {
  font-family: 'Consolas', 'Courier New', Courier, monospace;
  font-size: 0.95rem;
  line-height: 1.6;
}

.markdown-editor {
  padding: 0;
  overflow: hidden;
}

.editor-toolbar {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--color-border);
  background: rgba(0,0,0,0.02);
  align-items: center;
}
[data-theme='dark'] .editor-toolbar { background: rgba(255,255,255,0.02); }

.editor-toolbar .btn-icon {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  background: transparent;
  color: var(--color-text-primary);
}
.editor-toolbar .btn-icon:hover { background: rgba(0,0,0,0.05); }
[data-theme='dark'] .editor-toolbar .btn-icon:hover { background: rgba(255,255,255,0.1); }

.markdown-textarea {
  border: none;
  border-radius: 0;
  background: transparent;
  resize: vertical;
  padding: 1rem;
}
.markdown-textarea:focus {
  outline: none;
}

.skill-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}
.right-actions { display: flex; gap: 0.5rem; }
.btn-icon.danger { color: var(--color-danger); }

/* Toggle Switch */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.slider {
  position: absolute;
  cursor: pointer;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: var(--color-border);
  transition: .4s;
  border-radius: 24px;
}
.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}
input:checked + .slider { background-color: var(--color-success); }
input:checked + .slider:before { transform: translateX(20px); }
</style>
