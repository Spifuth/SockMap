import { createRouter, createWebHistory } from 'vue-router'
import GraphView from './views/GraphView.vue'
import DocsView from './views/DocsView.vue'

const routes = [
  { path: '/', name: 'graph', component: GraphView },
  { path: '/docs', name: 'docs', component: DocsView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
