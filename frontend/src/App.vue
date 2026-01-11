<script setup>
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
</script>

<template>
  <div class="app-container">
    <header class="header">
      <div class="logo">
        <span class="logo-icon">🧦</span>
        <h1>SockMap</h1>
      </div>
      <nav class="nav">
        <router-link to="/" :class="['nav-link', { active: route.path === '/' }]">
          📊 Graph
        </router-link>
        <router-link to="/docs" :class="['nav-link', { active: route.path === '/docs' }]">
          📄 Documentation
        </router-link>
      </nav>
    </header>

    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 28px;
}

.logo h1 {
  font-size: 22px;
  font-weight: 600;
}

.nav {
  display: flex;
  gap: 8px;
}

.nav-link {
  padding: 8px 16px;
  border-radius: 6px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s;
}

.nav-link:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.nav-link.active {
  background: var(--accent-blue);
  color: white;
}

.main {
  flex: 1;
  overflow: hidden;
}
</style>
