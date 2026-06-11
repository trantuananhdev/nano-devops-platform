<script setup>
import { computed, onMounted, nextTick, onBeforeUnmount, ref } from 'vue'
import { Plus, Save, Download, CheckCircle, AlertCircle } from '@lucide/vue'
import BpmnModeler from 'bpmn-js/lib/Modeler'
import 'bpmn-js/dist/assets/diagram-js.css'
import 'bpmn-js/dist/assets/bpmn-font/css/bpmn.css'
import { useDossierStore } from '../stores/dossier'
import { useWorkflowStore } from '../stores/workflow'

const dossierStore = useDossierStore()
const workflowStore = useWorkflowStore()

const docTypes = computed(() => dossierStore.dossiers.map((d) => d.title))
const selectedDossier = ref(null)
const canvasRef = ref(null)
const toast = ref(null) // { type: 'success'|'error', msg: string }
let bpmnModeler = null
let toastTimer = null

const DEFAULT_BPMN = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_1" isExecutable="false">
    <bpmn:startEvent id="StartEvent_1" name="Chuyên viên đệ trình">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:task id="Task_1" name="Trưởng Ban xem xét">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:task>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1" />
    <bpmn:task id="Task_2" name="HĐTV phê duyệt">
      <bpmn:incoming>Flow_2</bpmn:incoming>
      <bpmn:outgoing>Flow_3</bpmn:outgoing>
    </bpmn:task>
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="Task_2" />
    <bpmn:endEvent id="EndEvent_1" name="Kết thúc">
      <bpmn:incoming>Flow_3</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_3" sourceRef="Task_2" targetRef="EndEvent_1" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="_BPMNShape_StartEvent_2" bpmnElement="StartEvent_1">
        <dc:Bounds x="152" y="102" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_1_di" bpmnElement="Task_1">
        <dc:Bounds x="240" y="80" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1">
        <di:waypoint x="188" y="120" />
        <di:waypoint x="240" y="120" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNShape id="Task_2_di" bpmnElement="Task_2">
        <dc:Bounds x="400" y="80" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_2_di" bpmnElement="Flow_2">
        <di:waypoint x="340" y="120" />
        <di:waypoint x="400" y="120" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNShape id="EndEvent_1_di" bpmnElement="EndEvent_1">
        <dc:Bounds x="562" y="102" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_3_di" bpmnElement="Flow_3">
        <di:waypoint x="500" y="120" />
        <di:waypoint x="562" y="120" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>`

async function loadDiagram(xml) {
  if (!bpmnModeler) return
  try {
    await bpmnModeler.importXML(xml)
    bpmnModeler.get('canvas').zoom('fit-viewport')
  } catch (err) {
    console.error('BPMN render error', err)
  }
}

async function selectDossier(dossier) {
  selectedDossier.value = dossier
  workflowStore.clear()
  const saved = await workflowStore.fetchWorkflow(Number(dossier.id))
  await loadDiagram(saved ? saved.bpmn_xml : DEFAULT_BPMN)
}

async function saveDiagram() {
  if (!selectedDossier.value || !bpmnModeler) return
  try {
    const { xml } = await bpmnModeler.saveXML({ format: true })
    await workflowStore.saveWorkflow(Number(selectedDossier.value.id), xml)
    showToast('success', 'Đã lưu sơ đồ BPMN thành công')
  } catch (err) {
    showToast('error', `Lưu thất bại: ${err.message}`)
  }
}

async function exportXML() {
  if (!bpmnModeler) return
  const { xml } = await bpmnModeler.saveXML({ format: true })
  const blob = new Blob([xml], { type: 'application/xml' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `workflow-${selectedDossier.value?.docNo || 'bpmn'}.xml`
  a.click()
  URL.revokeObjectURL(url)
}

function showToast(type, msg) {
  clearTimeout(toastTimer)
  toast.value = { type, msg }
  toastTimer = setTimeout(() => (toast.value = null), 3500)
}

onMounted(async () => {
  await dossierStore.fetchDossiers()
  await nextTick()
  bpmnModeler = new BpmnModeler({
    container: canvasRef.value,
    keyboard: { bindTo: document },
  })
  // Select first dossier and load its diagram
  if (dossierStore.dossiers.length > 0) {
    await selectDossier(dossierStore.dossiers[0])
  } else {
    await loadDiagram(DEFAULT_BPMN)
  }
})

onBeforeUnmount(() => {
  if (bpmnModeler) bpmnModeler.destroy()
  clearTimeout(toastTimer)
})
</script>

<template>
  <div class="page-container">
    <header class="page-header flex justify-between items-center">
      <div>
        <h1 class="page-title">Sơ đồ Luân chuyển (BPMN Workflow)</h1>
        <p class="page-subtitle">Thiết lập quy trình thẩm duyệt chuyên biệt cho từng nhóm Tờ trình nghiệp vụ</p>
      </div>
      <div class="header-actions flex gap-2">
        <button
          id="workflow-save-btn"
          class="btn btn-primary"
          :disabled="workflowStore.saving || !selectedDossier"
          @click="saveDiagram"
        >
          <Save v-if="!workflowStore.saving" :size="16" />
          <span v-if="workflowStore.saving" class="spin-inline">⏳</span>
          {{ workflowStore.saving ? 'Đang lưu...' : 'Lưu Sơ đồ' }}
        </button>
      </div>
    </header>

    <!-- Toast notification -->
    <Transition name="toast-slide">
      <div v-if="toast" :class="['workflow-toast', `workflow-toast--${toast.type}`]">
        <CheckCircle v-if="toast.type === 'success'" :size="16" />
        <AlertCircle v-else :size="16" />
        {{ toast.msg }}
      </div>
    </Transition>

    <div class="workflow-layout">
      <!-- Left Panel: Doc Types -->
      <div class="doc-types-panel glass-panel">
        <div class="panel-header">
          <h3>Phân loại Tờ trình</h3>
          <button class="btn-icon"><Plus size="16"/></button>
        </div>
        <ul class="type-list">
          <li
            v-for="dossier in dossierStore.dossiers"
            :key="dossier.id"
            :class="{ active: selectedDossier?.id === dossier.id }"
            @click="selectDossier(dossier)"
          >
            {{ dossier.title }}
            <span class="status-pill">{{ dossier.status }}</span>
          </li>
        </ul>
      </div>

      <!-- Right Panel: BPMN Editor -->
      <div class="editor-panel glass-panel">
        <div class="editor-header flex justify-between items-center">
          <div>
            <h2 class="font-medium">
              Sơ đồ BPMN:
              <span class="text-primary">{{ selectedDossier?.title || 'Chọn Tờ trình' }}</span>
            </h2>
            <p v-if="workflowStore.diagram" class="saved-info">
              Đã lưu: {{ new Date(workflowStore.diagram.updated_at).toLocaleString('vi-VN') }}
            </p>
          </div>
          <div class="actions flex gap-2">
            <button class="btn btn-outline" @click="exportXML" :disabled="!selectedDossier">
              <Download size="14"/> Xuất file XML
            </button>
          </div>
        </div>
        <div
          v-if="workflowStore.loading"
          class="bpmn-loading"
        >
          <span class="spin-inline">⏳</span> Đang tải sơ đồ...
        </div>
        <div class="bpmn-canvas" ref="canvasRef"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container { padding: 2rem; max-width: 1600px; margin: 0 auto; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
.page-header { margin-bottom: 0.75rem; flex-shrink: 0; }
.page-title { font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; }
.page-subtitle { color: var(--color-text-secondary); }
.header-actions { align-items: center; }

/* Toast */
.workflow-toast {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.75rem;
  flex-shrink: 0;
}
.workflow-toast--success { background: rgba(34, 197, 94, 0.12); color: #16a34a; border: 1px solid rgba(34,197,94,0.25); }
.workflow-toast--error { background: rgba(239, 68, 68, 0.12); color: #dc2626; border: 1px solid rgba(239,68,68,0.25); }
[data-theme='dark'] .workflow-toast--success { color: #4ade80; }
[data-theme='dark'] .workflow-toast--error { color: #f87171; }
.toast-slide-enter-active, .toast-slide-leave-active { transition: all 0.2s ease; }
.toast-slide-enter-from, .toast-slide-leave-to { opacity: 0; transform: translateY(-8px); }

.workflow-layout {
  display: flex;
  gap: 1.5rem;
  flex: 1;
  min-height: 0;
  margin-bottom: 1rem;
}

.doc-types-panel {
  width: 320px;
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
.type-list { list-style: none; overflow-y: auto; flex: 1; }
.type-list li {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}
.type-list li:hover { background: rgba(0,0,0,0.02); }
[data-theme='dark'] .type-list li:hover { background: rgba(255,255,255,0.02); }
.type-list li.active {
  background: rgba(0, 86, 179, 0.05);
  border-left: 4px solid var(--color-primary);
  color: var(--color-primary);
}
.status-pill {
  display: block;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin-top: 0.25rem;
}
[data-theme='dark'] .type-list li.active { background: rgba(59, 130, 246, 0.1); color: var(--color-primary-light); }

.editor-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.editor-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
}
.saved-info { font-size: 0.75rem; color: var(--color-text-secondary); margin-top: 0.2rem; }
.text-primary { color: var(--color-primary); font-weight: 600; }

.bpmn-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--color-text-secondary);
  z-index: 10;
}
.bpmn-canvas {
  flex: 1;
  background: white;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
  position: relative;
}
[data-theme='dark'] .bpmn-canvas {
  filter: invert(0.85) hue-rotate(180deg);
}

.spin-inline { display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Fix for bpmn-js internal styles */
:deep(.bjs-powered-by) {
  display: none !important;
}
</style>

