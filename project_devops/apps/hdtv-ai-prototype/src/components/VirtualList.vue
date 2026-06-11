<script setup>
/**
 * T-38: VirtualList — lightweight virtual scroller (zero external deps).
 *
 * Renders only rows visible in the container plus an overscan buffer.
 * Dramatically reduces DOM node count for large datasets (1000+ dossiers).
 *
 * Usage:
 *   <VirtualList :items="dossiers" :item-height="52" :height="480">
 *     <template #default="{ item, index }">
 *       <div>…</div>
 *     </template>
 *   </VirtualList>
 *
 * Props:
 *   items       — full data array
 *   itemHeight  — fixed row height in px (required for offset math)
 *   height      — visible container height in px (default 480)
 *   overscan    — extra rows above/below viewport (default 5)
 *   keyField    — field used as :key (default 'id')
 *
 * Emits:
 *   scroll-end  — when scroll position is within 100px of bottom
 *                 (throttled: at most once per 200ms to prevent spam)
 */
import { computed, ref } from 'vue'

const props = defineProps({
  items:      { type: Array,  required: true },
  itemHeight: { type: Number, required: true },
  height:     { type: Number, default: 480 },
  overscan:   { type: Number, default: 5 },
  keyField:   { type: String, default: 'id' },
})

const emit = defineEmits(['scroll-end'])

const containerRef = ref(null)
const scrollTop    = ref(0)

// ---------------------------------------------------------------------------
// Derived geometry — all computed from scrollTop + props (no watchers needed)
// ---------------------------------------------------------------------------
const totalHeight = computed(() => props.items.length * props.itemHeight)

const startIndex = computed(() => {
  const raw = Math.floor(scrollTop.value / props.itemHeight) - props.overscan
  return Math.max(0, raw)
})

const endIndex = computed(() => {
  const visibleCount = Math.ceil(props.height / props.itemHeight)
  const raw = startIndex.value + visibleCount + props.overscan * 2
  return Math.min(props.items.length - 1, raw)
})

const visibleItems = computed(() =>
  props.items.slice(startIndex.value, endIndex.value + 1).map((item, i) => ({
    item,
    index:   startIndex.value + i,
    offsetY: (startIndex.value + i) * props.itemHeight,
  })),
)

// ---------------------------------------------------------------------------
// Scroll handler — throttled scroll-end emit (500ms) to prevent API spam.
// Only fires when genuinely near the bottom AND items actually exist.
// ---------------------------------------------------------------------------
let _scrollEndThrottle = 0

function onScroll(e) {
  scrollTop.value = e.target.scrollTop

  const el = e.target
  // Guard: only emit when there are items to load and container is scrollable
  if (props.items.length === 0 || el.scrollHeight <= el.clientHeight) return

  const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 100
  if (nearBottom) {
    const now = Date.now()
    if (now - _scrollEndThrottle > 500) {
      _scrollEndThrottle = now
      emit('scroll-end')
    }
  }
}

// Expose scrollToIndex so parents can imperatively scroll (e.g. search result)
function scrollToIndex(index) {
  if (containerRef.value) {
    containerRef.value.scrollTop = index * props.itemHeight
  }
}

defineExpose({ scrollToIndex })
</script>

<template>
  <div
    ref="containerRef"
    class="virtual-list-container"
    :style="{ height: height + 'px', overflowY: 'auto', position: 'relative' }"
    @scroll.passive="onScroll"
  >
    <!-- Full-height spacer — keeps native scrollbar proportional -->
    <div :style="{ height: totalHeight + 'px', position: 'relative' }">
      <div
        v-for="{ item, index, offsetY } in visibleItems"
        :key="item[keyField] ?? index"
        :style="{
          position: 'absolute',
          top:      offsetY + 'px',
          left:     0,
          right:    0,
          height:   itemHeight + 'px',
        }"
      >
        <slot :item="item" :index="index" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.virtual-list-container {
  -webkit-overflow-scrolling: touch; /* smooth on iOS */
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) transparent;
  /* Prevent layout shift when scrollbar appears/disappears */
  overflow-y: scroll;
}
.virtual-list-container::-webkit-scrollbar {
  width: 6px;
}
.virtual-list-container::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}
.virtual-list-container::-webkit-scrollbar-track {
  background: transparent;
}
</style>
