<script setup>
import { computed, onMounted, ref } from 'vue'
import { Network, Search, Maximize2, FileText, Database, Book, AlertTriangle } from '@lucide/vue'
import { useGraphStore } from '../stores/graph'
import { useDossierStore } from '../stores/dossier'

const searchQuery = ref('')
const graphStore = useGraphStore()
const dossierStore = useDossierStore()
const selectedDossierId = ref(null)
const selectedNode = ref(null)

const typeStyle = {
  dossier: { icon: FileText, color: 'var(--color-primary)' },
  legal: { icon: Book, color: 'var(--color-success)' },
  law: { icon: Book, color: 'var(--color-success)' },
  data: { icon: Database, color: '#f59e0b' },
  risk: { icon: AlertTriangle, color: 'var(--color-danger)' },
}

const graphCategories = computed(() =>
  dossierStore.dossiers.map((d) => ({ id: d.id, label: d.docNo }))
)

const nodes = computed(() =>
  (graphStore.graph?.nodes || []).map((n) => ({
    ...n,
    icon: typeStyle[n.type]?.icon || FileText,
    color: typeStyle[n.type]?.color || 'var(--color-primary)',
  }))
)

const edges = computed(() => graphStore.graph?.edges || [])

onMounted(async () => {
  await dossierStore.fetchDossiers()
  if (dossierStore.dossiers.length) {
    selectedDossierId.value = dossierStore.dossiers[0].id
    await loadGraph(selectedDossierId.value)
  }
})

async function loadGraph(dossierId) {
  await graphStore.fetchGraph(dossierId)
  selectedNode.value = nodes.value[0] || null
}

const selectNode = (node) => {
  selectedNode.value = node
}

const selectCategory = async (cat) => {
  selectedDossierId.value = cat.id
  await loadGraph(cat.id)
}
</script>

<template>
  <div class="page-container">
    <header class="page-header flex justify-between items-center">
      <div>
        <h1 class="page-title">Khám phá Đồ thị Tri thức (GraphRAG Explorer)</h1>
        <p class="page-subtitle">Truy vết dòng chảy Pháp lý và Dữ liệu của hệ thống</p>
      </div>
      <div class="flex gap-2">
        <div class="search-box">
          <Search size="16" class="search-icon" />
          <input type="text" v-model="searchQuery" placeholder="Tìm kiếm văn bản, điều khoản..." class="search-input" />
        </div>
        <button class="btn btn-outline"><Maximize2 size="16"/> Toàn màn hình</button>
      </div>
    </header>

    <div class="main-split-layout">
      <!-- Left Panel: Categories -->
      <div class="sidebar-panel glass-panel">
        <div class="panel-header">
          <h3>Phân luồng Tri thức</h3>
        </div>
        <ul class="category-list">
          <li 
            v-for="cat in graphCategories" 
            :key="cat.id" 
            :class="{ active: selectedDossierId === cat.id }"
            @click="selectCategory(cat)"
          >
            {{ cat.label }}
          </li>
        </ul>
      </div>

      <!-- Right Panel: Graph -->
      <div class="graph-layout">
        <!-- Main Canvas -->
        <div class="graph-canvas glass-panel">
          <svg class="edges-layer">
            <line 
              v-for="(edge, index) in edges" 
              :key="index"
              :x1="nodes.find(n => n.id === edge.source).x"
              :y1="nodes.find(n => n.id === edge.source).y"
              :x2="nodes.find(n => n.id === edge.target).x"
              :y2="nodes.find(n => n.id === edge.target).y"
              class="edge-line"
            />
            <text 
              v-for="(edge, index) in edges" 
              :key="'text-'+index"
              :x="(nodes.find(n => n.id === edge.source).x + nodes.find(n => n.id === edge.target).x) / 2"
              :y="(nodes.find(n => n.id === edge.source).y + nodes.find(n => n.id === edge.target).y) / 2 - 5"
              class="edge-label"
            >
              {{ edge.label }}
            </text>
          </svg>

          <div class="nodes-layer">
            <div 
              v-for="node in nodes" 
              :key="node.id"
              class="graph-node"
              :class="{ active: selectedNode && selectedNode.id === node.id }"
              :style="{ left: node.x + 'px', top: node.y + 'px', borderColor: node.color }"
              @click="selectNode(node)"
            >
              <div class="node-icon" :style="{ backgroundColor: node.color }">
                <component :is="node.icon" size="18" color="white" />
              </div>
              <div class="node-label">{{ node.label }}</div>
            </div>
          </div>
        </div>

        <!-- Node Details -->
        <div class="node-details glass-panel">
          <h3 class="panel-title">Chi tiết Thực thể</h3>
          
          <div v-if="selectedNode" class="detail-content">
          <div class="detail-header flex items-center gap-3">
            <div class="node-icon-large" :style="{ backgroundColor: selectedNode.color }">
              <component :is="selectedNode.icon" size="24" color="white" />
            </div>
            <div>
              <h2 class="detail-title">{{ selectedNode.label }}</h2>
              <span class="detail-type badge" :style="{ backgroundColor: selectedNode.color }">{{ selectedNode.type.toUpperCase() }}</span>
            </div>
          </div>

          <div class="detail-section">
            <h4>Mô tả</h4>
            <p>{{ selectedNode.desc }}</p>
          </div>

          <div class="detail-section">
            <h4>Siêu dữ liệu (Metadata)</h4>
            <ul class="meta-list">
              <li><strong>ID:</strong> {{ selectedNode.id }}</li>
              <li><strong>Mức độ tin cậy:</strong> 98.5%</li>
              <li><strong>Nguồn:</strong> {{ selectedNode.type === 'law' ? 'Thư viện Pháp luật' : selectedNode.type === 'data' ? 'ERP Integration' : 'Hệ thống Nội bộ' }}</li>
            </ul>
          </div>

          <div class="detail-section">
            <h4>Trích xuất nội dung (Chunk)</h4>
            <div class="code-font chunk-preview">
              "{{ selectedNode.desc || '—' }}"
            </div>
          </div>

          <button class="btn btn-primary w-full mt-4">Xem Tài liệu Gốc</button>
        </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container { padding: 2rem; max-width: 1600px; margin: 0 auto; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
.page-header { margin-bottom: 1.5rem; flex-shrink: 0; }
.page-title { font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; }
.page-subtitle { color: var(--color-text-secondary); }

.search-box { position: relative; display: flex; align-items: center; }
.search-icon { position: absolute; left: 1rem; color: var(--color-text-secondary); }
.search-input { padding: 0.6rem 1rem 0.6rem 2.5rem; border: 1px solid var(--color-border); border-radius: 8px; background: var(--color-bg-base); color: var(--color-text-primary); font-family: inherit; width: 300px; outline: none; transition: border-color 0.2s; }
.search-input:focus { border-color: var(--color-primary); }

.main-split-layout {
  display: flex;
  gap: 1.5rem;
  flex: 1;
  min-height: 0;
  margin-bottom: 1rem;
}

.sidebar-panel {
  width: 280px;
  display: flex;
  flex-direction: column;
}
.sidebar-panel .panel-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
}
.sidebar-panel .panel-header h3 { font-size: 1rem; margin: 0; font-weight: 600; }
.category-list { list-style: none; overflow-y: auto; flex: 1; }
.category-list li {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  font-size: 0.95rem;
}
.category-list li:hover { background: rgba(0,0,0,0.02); }
[data-theme='dark'] .category-list li:hover { background: rgba(255,255,255,0.02); }
.category-list li.active {
  background: rgba(0, 86, 179, 0.05);
  border-left: 4px solid var(--color-primary);
  color: var(--color-primary);
}
[data-theme='dark'] .category-list li.active { background: rgba(59, 130, 246, 0.1); color: var(--color-primary-light); }

.graph-layout {
  display: flex;
  gap: 1.5rem;
  flex: 1;
}

/* Canvas */
.graph-canvas {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: var(--color-bg-base);
  background-image: radial-gradient(var(--color-border) 1px, transparent 1px);
  background-size: 20px 20px;
}
.edges-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.edge-line {
  stroke: var(--color-border);
  stroke-width: 2;
  stroke-dasharray: 4;
}
[data-theme='dark'] .edge-line { stroke: rgba(255,255,255,0.2); }
.edge-label {
  fill: var(--color-text-secondary);
  font-size: 12px;
  text-anchor: middle;
  background: var(--color-bg-base);
}

.nodes-layer {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
}
.graph-node {
  position: absolute;
  transform: translate(-50%, -50%);
  background: var(--color-bg-panel);
  border: 2px solid;
  border-radius: 30px;
  padding: 0.5rem 1rem 0.5rem 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  user-select: none;
}
.graph-node:hover { transform: translate(-50%, -50%) scale(1.05); box-shadow: 0 8px 15px rgba(0,0,0,0.15); z-index: 10; }
.graph-node.active { transform: translate(-50%, -50%) scale(1.1); box-shadow: 0 0 0 4px rgba(0, 86, 179, 0.2); z-index: 20; }
[data-theme='dark'] .graph-node.active { box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.3); }

.node-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.node-label { font-weight: 600; font-size: 0.9rem; color: var(--color-text-primary); white-space: nowrap; }

/* Right Panel */
.node-details {
  width: 350px;
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  overflow-y: auto;
}
.panel-title { font-size: 1.25rem; font-weight: 600; margin-bottom: 1.5rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--color-border); }

.detail-header { margin-bottom: 1.5rem; }
.node-icon-large { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.detail-title { font-size: 1.15rem; font-weight: 700; margin-bottom: 0.25rem; }
.badge { color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }

.detail-section { margin-bottom: 1.5rem; }
.detail-section h4 { font-size: 0.95rem; color: var(--color-text-secondary); margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px; }
.detail-section p { font-size: 0.95rem; line-height: 1.5; }

.meta-list { list-style: none; font-size: 0.9rem; }
.meta-list li { margin-bottom: 0.4rem; padding-bottom: 0.4rem; border-bottom: 1px dashed var(--color-border); }
.meta-list li:last-child { border-bottom: none; }

.chunk-preview {
  background: var(--color-bg-base);
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  font-size: 0.85rem;
  font-style: italic;
}
.code-font { font-family: 'Consolas', 'Courier New', Courier, monospace; }
.w-full { width: 100%; }
.mt-4 { margin-top: 1rem; }
</style>
