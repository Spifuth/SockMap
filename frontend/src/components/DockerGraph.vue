<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
})

const svgRef = ref(null)
let simulation = null
const nodePositions = new Map()

const categoryColors = {
  reverse_proxy: '#ff6b6b',
  security: '#ffd93d',
  database: '#6bcb77',
  cache: '#4d96ff',
  monitoring: '#9b59b6',
  storage: '#e67e22',
  messaging: '#1abc9c',
  frontend: '#3498db',
  backend: '#2ecc71',
  application: '#58a6ff',
  unknown: '#8b949e',
}

function initGraph() {
  if (!svgRef.value) return
  if (!props.data?.nodes?.length) return

  try {
    const svg = d3.select(svgRef.value)
    svg.selectAll('*').remove()

    const width = svgRef.value.clientWidth || 800
    const height = svgRef.value.clientHeight || 600

    const tierHeight = height / 8
    const getYForTier = (tier) => 80 + (tier ?? 2) * tierHeight

    const nodes = props.data.nodes.map((node) => {
      const saved = nodePositions.get(node.id)
      return {
        ...node,
        x: saved?.x ?? (width / 2 + (Math.random() - 0.5) * 400),
        y: saved?.y ?? (getYForTier(node.tier) + (Math.random() - 0.5) * 50),
        fx: saved?.fx ?? null,
        fy: saved?.fy ?? null
      }
    })

    const edges = props.data.edges.map(e => ({
      source: e.source,
      target: e.target,
      type: e.type,
      label: e.label
    }))

    const zoom = d3.zoom()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => container.attr('transform', event.transform))

    svg.call(zoom)
    const container = svg.append('g')

    // Arrow markers
    const defs = svg.append('defs')
    defs.selectAll('marker')
      .data(['network', 'volume', 'dep'])
      .join('marker')
      .attr('id', d => `arrow-${d}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 30)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('fill', d => d === 'network' ? '#9b59b6' : d === 'volume' ? '#f1c40f' : '#e74c3c')
      .attr('d', 'M0,-5L10,0L0,5')

    // Simulation
    simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id(d => d.id).distance(120).strength(0.3))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('x', d3.forceX(width / 2).strength(0.03))
      .force('y', d3.forceY(d => getYForTier(d.tier)).strength(0.2))
      .force('collision', d3.forceCollide().radius(50))

    // Links
    const links = container.append('g')
      .selectAll('line')
      .data(edges)
      .join('line')
      .attr('stroke', d => d.type === 'network_connection' ? '#9b59b6' : d.type === 'volume_mount' ? '#f1c40f' : '#e74c3c')
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', d => d.type === 'network_connection' ? 'url(#arrow-network)' : d.type === 'volume_mount' ? 'url(#arrow-volume)' : 'url(#arrow-dep)')

    // Node groups
    const nodeGroups = container.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'grab')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.1).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0)
          nodePositions.set(d.id, { x: d.x, y: d.y, fx: d.fx, fy: d.fy })
        }))

    // Draw shapes based on type
    nodeGroups.each(function(d) {
      const g = d3.select(this)
      const color = d.type === 'container' ? (categoryColors[d.category] || '#58a6ff')
                  : d.type === 'network' ? '#9b59b6'
                  : '#f1c40f'

      if (d.type === 'container') {
        g.append('rect')
          .attr('x', -25).attr('y', -25)
          .attr('width', 50).attr('height', 50)
          .attr('rx', 8)
          .attr('fill', color)
          .attr('stroke', '#fff')
          .attr('stroke-width', 2)
      } else if (d.type === 'network') {
        g.append('circle')
          .attr('r', 22)
          .attr('fill', color)
          .attr('stroke', '#fff')
          .attr('stroke-width', 2)
      } else {
        g.append('polygon')
          .attr('points', '0,-28 28,24 -28,24')
          .attr('fill', color)
          .attr('stroke', '#fff')
          .attr('stroke-width', 2)
      }
    })

    // Icons
    nodeGroups.append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-size', '18px')
      .text(d => {
        if (d.type === 'network') return '🌐'
        if (d.type === 'volume') return '💾'
        const icons = { reverse_proxy: '🔀', security: '🔐', database: '🗄️', cache: '⚡', monitoring: '📊', messaging: '📨', application: '📦' }
        return icons[d.category] || '📦'
      })

    // Labels
    nodeGroups.append('text')
      .attr('dy', 45)
      .attr('text-anchor', 'middle')
      .attr('fill', '#e0e0e0')
      .attr('font-size', '11px')
      .text(d => d.label.length > 18 ? d.label.slice(0, 16) + '...' : d.label)

    // Tick
    simulation.on('tick', () => {
      links
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)
      nodeGroups.attr('transform', d => `translate(${d.x},${d.y})`)
    })

  } catch (err) {
    console.error('Graph error:', err)
  }
}

watch(() => props.data, () => {
  if (props.data?.nodes?.length) initGraph()
}, { deep: true })

onMounted(() => {
  setTimeout(initGraph, 100)
  window.addEventListener('resize', initGraph)
})

onUnmounted(() => {
  window.removeEventListener('resize', initGraph)
  if (simulation) simulation.stop()
})
</script>

<template>
  <div class="graph-wrapper">
    <svg ref="svgRef" class="graph-svg"></svg>
    <div class="legend">
      <div><span style="color:#ff6b6b">■</span> Reverse Proxy</div>
      <div><span style="color:#6bcb77">■</span> Database</div>
      <div><span style="color:#9b59b6">■</span> Monitoring</div>
      <div><span style="color:#1abc9c">■</span> Messaging</div>
      <div><span style="color:#58a6ff">■</span> Application</div>
      <div><span style="color:#9b59b6">●</span> Network</div>
      <div><span style="color:#f1c40f">▲</span> Volume</div>
    </div>
  </div>
</template>

<style scoped>
.graph-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  background: var(--bg-primary);
}
.graph-svg {
  width: 100%;
  height: 100%;
}
.legend {
  position: absolute;
  bottom: 16px;
  right: 16px;
  background: rgba(0,0,0,0.7);
  padding: 12px;
  border-radius: 8px;
  font-size: 12px;
  color: #fff;
}
.legend div {
  margin: 4px 0;
}
</style>
