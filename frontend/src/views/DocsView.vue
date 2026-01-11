<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { marked } from 'marked'

const loading = ref(true)
const error = ref(null)
const docs = ref(null)
const activeSection = ref('overview')

const sections = [
  { id: 'overview', label: '📊 Overview', icon: '📊' },
  { id: 'architecture', label: '🏗️ Architecture', icon: '🏗️' },
  { id: 'containers', label: '📦 Containers', icon: '📦' },
  { id: 'networks', label: '🌐 Networks', icon: '🌐' },
  { id: 'volumes', label: '💾 Volumes', icon: '💾' },
  { id: 'full', label: '📄 Full Document', icon: '📄' },
]

async function fetchDocs() {
  loading.value = true
  try {
    const response = await fetch('/api/docker/docs')
    if (!response.ok) throw new Error('Failed to fetch documentation')
    docs.value = await response.json()
    error.value = null
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const currentMarkdown = computed(() => {
  if (!docs.value) return ''
  return docs.value[activeSection.value] || docs.value.full || ''
})

const renderedHtml = computed(() => {
  if (!currentMarkdown.value) return ''
  return marked(currentMarkdown.value)
})

async function downloadMarkdown() {
  const content = docs.value?.full || docs.value?.markdown || ''
  const blob = new Blob([content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'docker-stack-documentation.md'
  a.click()
  URL.revokeObjectURL(url)
}

async function downloadSection() {
  const content = currentMarkdown.value
  const blob = new Blob([content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `docker-${activeSection.value}.md`
  a.click()
  URL.revokeObjectURL(url)
}

async function copyToClipboard() {
  await navigator.clipboard.writeText(currentMarkdown.value)
  showToast('Copied to clipboard!')
}

const toastMessage = ref('')
const showToastFlag = ref(false)

function showToast(msg) {
  toastMessage.value = msg
  showToastFlag.value = true
  setTimeout(() => {
    showToastFlag.value = false
  }, 2000)
}

onMounted(() => fetchDocs())
</script>

<template>
  <div class="docs-view">
    <!-- Sidebar Navigation -->
    <aside class="docs-sidebar">
      <div class="sidebar-header">
        <h3>📚 Documentation</h3>
      </div>
      <nav class="sidebar-nav">
        <button
          v-for="section in sections"
          :key="section.id"
          :class="['nav-item', { active: activeSection === section.id }]"
          @click="activeSection = section.id"
        >
          <span class="nav-icon">{{ section.icon }}</span>
          <span class="nav-label">{{ section.label.replace(/^.+\s/, '') }}</span>
        </button>
      </nav>
      <div class="sidebar-actions">
        <button @click="fetchDocs" :disabled="loading" class="action-btn">
          🔄 Refresh
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="docs-main">
      <!-- Toolbar -->
      <div class="toolbar">
        <div class="toolbar-left">
          <span class="current-section">{{ sections.find(s => s.id === activeSection)?.label }}</span>
        </div>
        <div class="toolbar-right">
          <button @click="downloadSection" class="btn" :disabled="!docs">
            📥 Download Section
          </button>
          <button @click="downloadMarkdown" class="btn" :disabled="!docs">
            📄 Download Full
          </button>
          <button @click="copyToClipboard" class="btn" :disabled="!docs">
            📋 Copy
          </button>
        </div>
      </div>

      <!-- Content Area -->
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Generating documentation...</p>
      </div>

      <div v-else-if="error" class="error">
        <span class="error-icon">⚠️</span>
        <p>{{ error }}</p>
        <button @click="fetchDocs" class="btn">Retry</button>
      </div>

      <div v-else class="docs-content">
        <div class="markdown-body" v-html="renderedHtml"></div>
      </div>
    </main>

    <!-- Toast notification -->
    <Transition name="toast">
      <div v-if="showToastFlag" class="toast">
        {{ toastMessage }}
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.docs-view {
  display: flex;
  height: 100%;
  background: var(--bg-primary);
}

/* Sidebar */
.docs-sidebar {
  width: 220px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.sidebar-nav {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  border-radius: 6px;
  text-align: left;
  font-size: 13px;
  transition: all 0.15s ease;
}

.nav-item:hover {
  background: var(--bg-tertiary);
}

.nav-item.active {
  background: var(--accent-blue);
  color: white;
}

.nav-icon {
  font-size: 16px;
}

.sidebar-actions {
  padding: 12px;
  border-top: 1px solid var(--border-color);
}

.action-btn {
  width: 100%;
  padding: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.action-btn:hover {
  background: var(--bg-tertiary);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Main content */
.docs-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
}

.toolbar-left {
  font-weight: 600;
  font-size: 14px;
}

.current-section {
  color: var(--accent-blue);
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.btn {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 12px;
  transition: all 0.15s ease;
}

.btn:hover {
  background: var(--border-color);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Loading */
.loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--text-secondary);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error */
.error {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--accent-red);
}

.error-icon {
  font-size: 48px;
}

/* Content */
.docs-content {
  flex: 1;
  overflow-y: auto;
  padding: 32px 48px;
}

.markdown-body {
  max-width: 900px;
  margin: 0 auto;
  line-height: 1.7;
}

/* Markdown styles */
.markdown-body :deep(h1) {
  font-size: 2em;
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 12px;
  margin-bottom: 24px;
}

.markdown-body :deep(h2) {
  font-size: 1.5em;
  margin-top: 40px;
  margin-bottom: 16px;
  color: var(--accent-blue);
}

.markdown-body :deep(h3) {
  font-size: 1.25em;
  margin-top: 28px;
  margin-bottom: 12px;
}

.markdown-body :deep(h4) {
  font-size: 1.1em;
  margin-top: 20px;
  color: var(--text-secondary);
}

.markdown-body :deep(p) {
  margin: 12px 0;
}

.markdown-body :deep(code) {
  background: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-body :deep(pre) {
  background: var(--bg-tertiary);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 16px 0;
  border: 1px solid var(--border-color);
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 13px;
  line-height: 1.5;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  text-align: left;
}

.markdown-body :deep(th) {
  background: var(--bg-tertiary);
  font-weight: 600;
}

.markdown-body :deep(tr:nth-child(even)) {
  background: var(--bg-secondary);
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 12px 0;
  padding-left: 24px;
}

.markdown-body :deep(li) {
  margin: 6px 0;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid var(--accent-blue);
  margin: 16px 0;
  padding: 8px 16px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-color);
  margin: 32px 0;
}

.markdown-body :deep(a) {
  color: var(--accent-blue);
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

/* Toast */
.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--accent-green);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 1000;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
</style>
