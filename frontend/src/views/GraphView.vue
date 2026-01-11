<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import DockerGraph from '../components/DockerGraph.vue'
import Sidebar from '../components/Sidebar.vue'

const graphData = ref({ nodes: [], edges: [] })
const loading = ref(true)
const error = ref(null)
const autoRefresh = ref(false)
let refreshInterval = null

async function fetchGraphData() {
  try {
    const response = await fetch('/api/docker/graph')
    if (!response.ok) throw new Error('Failed to fetch Docker data')
    graphData.value = await response.json()
    error.value = null
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    refreshInterval = setInterval(fetchGraphData, 5000)
  } else {
    clearInterval(refreshInterval)
  }
}

onMounted(() => fetchGraphData())
onUnmounted(() => clearInterval(refreshInterval))
</script>

<template>
  <div class="graph-view">
    <div v-if="error" class="error-banner">
      ⚠️ {{ error }}
    </div>

    <div class="toolbar">
      <button @click="fetchGraphData" :disabled="loading" class="btn">
        {{ loading ? '⏳' : '🔄' }} Refresh
      </button>
      <button @click="toggleAutoRefresh" :class="['btn', { active: autoRefresh }]">
        {{ autoRefresh ? '⏸️' : '▶️' }} Auto
      </button>
      <span class="stats">{{ graphData.nodes.length }} nodes · {{ graphData.edges.length }} connections</span>
    </div>

    <div class="content">
      <DockerGraph :data="graphData" class="graph" />
      <Sidebar :nodes="graphData.nodes" class="sidebar" />
    </div>
  </div>
</template>

<style scoped>
.graph-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.error-banner {
  background: rgba(248, 81, 73, 0.1);
  border-bottom: 1px solid var(--accent-red);
  color: var(--accent-red);
  padding: 8px 16px;
  text-align: center;
}
.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
}
.btn {
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 13px;
}
.btn:hover { background: var(--border-color); }
.btn.active { background: var(--accent-green); border-color: var(--accent-green); }
.stats { margin-left: auto; font-size: 13px; color: var(--text-secondary); }
.content { flex: 1; display: flex; overflow: hidden; }
.graph { flex: 1; }
.sidebar { width: 320px; border-left: 1px solid var(--border-color); }
</style>
