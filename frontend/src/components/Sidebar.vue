<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  nodes: {
    type: Array,
    default: () => [],
  },
})

const selectedNode = ref(null)
const filterType = ref('all')

const filteredNodes = computed(() => {
  if (filterType.value === 'all') return props.nodes
  return props.nodes.filter(n => n.type === filterType.value)
})

const containerCount = computed(() => props.nodes.filter(n => n.type === 'container').length)
const networkCount = computed(() => props.nodes.filter(n => n.type === 'network').length)
const volumeCount = computed(() => props.nodes.filter(n => n.type === 'volume').length)

const nodeIcon = (node) => {
  const icons = {
    reverse_proxy: '🔀', security: '🔐', database: '🗄️', cache: '⚡',
    monitoring: '📊', storage: '💾', messaging: '📨', frontend: '🖥️',
    backend: '⚙️', application: '📦', unknown: '📦'
  }
  if (node.type === 'container') return icons[node.category] || '📦'
  if (node.type === 'network') return '🌐'
  if (node.type === 'volume') return '💾'
  return '❓'
}

const statusColor = (status) => {
  const colors = { running: '#4ade80', exited: '#f87171', paused: '#fbbf24' }
  return colors[status] || '#9ca3af'
}

function selectNode(node) { selectedNode.value = node }
function goBack() { selectedNode.value = null }
</script>

<template>
  <aside class="sidebar">
    <template v-if="!selectedNode">
      <header class="header">
        <h2>📋 Stack Overview</h2>
        <div class="tabs">
          <button :class="{ active: filterType === 'all' }" @click="filterType = 'all'">All ({{ nodes.length }})</button>
          <button :class="{ active: filterType === 'container' }" @click="filterType = 'container'">📦 {{ containerCount }}</button>
          <button :class="{ active: filterType === 'network' }" @click="filterType = 'network'">🌐 {{ networkCount }}</button>
          <button :class="{ active: filterType === 'volume' }" @click="filterType = 'volume'">💾 {{ volumeCount }}</button>
        </div>
      </header>
      <div class="list">
        <div v-for="node in filteredNodes" :key="node.id" class="item" @click="selectNode(node)">
          <span class="icon">{{ nodeIcon(node) }}</span>
          <div class="info">
            <span class="name">{{ node.label }}</span>
            <span class="type">{{ node.type }}</span>
          </div>
          <span v-if="node.status" class="dot" :style="{ background: statusColor(node.status) }"></span>
          <span class="arrow">›</span>
        </div>
        <div v-if="filteredNodes.length === 0" class="empty">No items found</div>
      </div>
    </template>

    <template v-else>
      <button class="back" @click="goBack">← Back</button>
      <header class="detail-header">
        <span class="big-icon">{{ nodeIcon(selectedNode) }}</span>
        <div>
          <h2>{{ selectedNode.label }}</h2>
          <span class="type">{{ selectedNode.type }}</span>
        </div>
      </header>
      
      <div class="details">
        <div v-if="selectedNode.status" class="row">
          <strong>Status:</strong>
          <span :style="{ color: statusColor(selectedNode.status) }">● {{ selectedNode.status }}</span>
        </div>
        <div v-if="selectedNode.category" class="row">
          <strong>Category:</strong> {{ selectedNode.category }}
        </div>
        <div v-if="selectedNode.metadata?.image" class="row">
          <strong>Image:</strong>
          <code>{{ selectedNode.metadata.image }}</code>
        </div>
        <div v-if="selectedNode.metadata?.ip_addresses?.length" class="row">
          <strong>IPs:</strong>
          <span v-for="ip in selectedNode.metadata.ip_addresses" :key="ip">{{ ip }} </span>
        </div>
        <div v-if="selectedNode.metadata?.ports?.length" class="row">
          <strong>Ports:</strong>
          <span v-for="(p, i) in selectedNode.metadata.ports" :key="i">
            {{ p.host_port || '?' }}:{{ p.container_port }}/{{ p.protocol }}
          </span>
        </div>
        <div v-if="selectedNode.metadata?.dependencies?.length" class="row">
          <strong>Dependencies:</strong>
          <span v-for="d in selectedNode.metadata.dependencies" :key="d">→ {{ d }} </span>
        </div>
        <div v-if="selectedNode.metadata?.driver" class="row">
          <strong>Driver:</strong> {{ selectedNode.metadata.driver }}
        </div>
        <div v-if="selectedNode.metadata?.mountpoint" class="row">
          <strong>Mountpoint:</strong>
          <code>{{ selectedNode.metadata.mountpoint }}</code>
        </div>
        <div class="row">
          <strong>ID:</strong>
          <code>{{ selectedNode.id }}</code>
        </div>
      </div>
    </template>
  </aside>
</template>

<style scoped>
.sidebar {
  background: var(--bg-secondary);
  height: 100%;
  overflow-y: auto;
  padding: 16px;
}
.header h2 { font-size: 16px; margin-bottom: 12px; }
.tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.tabs button {
  padding: 6px 10px;
  border: none;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}
.tabs button:hover { background: var(--border-color); }
.tabs button.active { background: var(--accent-blue); color: white; }
.list { margin-top: 16px; }
.item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  margin-bottom: 6px;
  cursor: pointer;
}
.item:hover { background: var(--border-color); }
.icon { font-size: 20px; }
.info { flex: 1; }
.name { display: block; font-weight: 500; }
.type { font-size: 11px; color: var(--text-secondary); text-transform: uppercase; }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.arrow { color: var(--text-secondary); font-size: 18px; }
.empty { text-align: center; padding: 40px; color: var(--text-secondary); }
.back {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 16px;
}
.detail-header { display: flex; gap: 12px; align-items: center; margin-bottom: 20px; }
.big-icon { font-size: 36px; }
.detail-header h2 { font-size: 18px; word-break: break-all; }
.details { display: flex; flex-direction: column; gap: 12px; }
.row { font-size: 14px; }
.row strong { display: block; color: var(--text-secondary); font-size: 12px; margin-bottom: 4px; }
.row code {
  display: block;
  background: var(--bg-tertiary);
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
  word-break: break-all;
}
</style>
