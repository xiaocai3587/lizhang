<script setup lang="ts">
// G6 v5 朋友关系网(力导向图)
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { Graph } from '@antv/g6';
import { useRouter } from 'vue-router';
import { getFriendGraph } from '@/api';
import type { GraphData, GraphNode } from '@/types';
import { formatMoney } from '@/utils/format';

const router = useRouter();

const containerRef = ref<HTMLDivElement | null>(null);
const loading = ref(false);
const empty = ref(false);
let graph: Graph | null = null;

const searchKeyword = ref('');
const selectedNode = ref<GraphNode | null>(null);

// 节点大小计算
function nodeSize(totalAmount: number | undefined): number {
  const amount = totalAmount || 0;
  return Math.log(amount + 1) * 4 + 12;
}

// 转换数据
function transformData(data: GraphData) {
  const nodes = data.nodes.map((n) => ({
    id: String(n.id),
    data: { ...n },
  }));
  const edges = data.links.map((l, i) => ({
    id: `e-${i}`,
    source: String(l.source),
    target: String(l.target),
    data: { type: l.type, amount: l.amount },
  }));
  return { nodes, edges };
}

async function initGraph() {
  if (!containerRef.value) return;
  const container = containerRef.value;
  const width = container.clientWidth || 800;
  const height = container.clientHeight || 600;

  graph = new Graph({
    container,
    width,
    height,
    autoResize: true,
    layout: {
      type: 'force',
      preventOverlap: true,
      nodeSize: 40,
      link: { distance: 120 },
      node: { strength: -150 },
    } as any,
    node: {
      type: 'circle',
      style: (d: any) => {
        const data = d.data || {};
        const size = nodeSize(data.total_amount);
        return {
          size,
          fill: '#8b5cf6',
          stroke: data.is_self ? '#d4a843' : '#7c3aed',
          lineWidth: data.is_self ? 3 : 1.5,
          labelText: data.name || '',
          labelFontSize: 11,
          labelFill: '#2c2c2c',
          labelPosition: 'bottom',
          labelOffsetY: 4,
          cursor: 'pointer',
        };
      },
      state: {
        active: {
          fill: '#d4a843',
          stroke: '#c44536',
          lineWidth: 3,
          labelFill: '#c44536',
          labelFontWeight: 'bold',
        } as any,
        inactive: {
          opacity: 0.3,
        } as any,
      },
    },
    edge: {
      style: (d: any) => {
        const type = d.data?.type;
        const amount = d.data?.amount || 0;
        const isGift = type === 'gift';
        return {
          stroke: isGift ? '#d4a843' : '#b0b0b0',
          lineWidth: isGift ? Math.min(Math.log(amount + 1) * 1.5 + 1, 6) : 1,
          lineDash: isGift ? [5, 3] : undefined,
        };
      },
    },
    behaviors: ['zoom-canvas', 'drag-canvas', 'drag-element'],
  });

  graph.on('node:click', (evt: any) => {
    const id = evt.target?.id;
    if (id === undefined) return;
    selectNode(String(id));
  });

  graph.on('canvas:click', () => {
    selectedNode.value = null;
  });
}

// 选中节点(侧边栏)
function selectNode(id: string) {
  const nodeData = graph?.getNodeData(id);
  if (!nodeData) return;
  const data = (nodeData as any).data || {};
  selectedNode.value = {
    id: String(id),
    name: data.name || '',
    gender: data.gender || 'unknown',
    group: data.group || 'friends',
    is_self: !!data.is_self,
    birth_year: data.birth_year ?? '',
    depth: data.depth ?? 0,
    total_amount: data.total_amount,
  };
}

async function loadData() {
  if (!graph) return;
  loading.value = true;
  empty.value = false;
  selectedNode.value = null;
  try {
    const data = await getFriendGraph();
    if (!data.nodes || data.nodes.length === 0) {
      empty.value = true;
      graph.setData({ nodes: [], edges: [] });
      await graph.render();
      return;
    }
    const transformed = transformData(data);
    graph.setData(transformed as any);
    await graph.render();
    await graph.fitView({ when: 'always', direction: 'both' } as any);
  } finally {
    loading.value = false;
  }
}

// 搜索高亮
function handleSearch() {
  if (!graph) return;
  const keyword = searchKeyword.value.trim().toLowerCase();
  const allNodes = graph.getNodeData() || [];
  if (!keyword) {
    // 清除所有状态
    allNodes.forEach((n: any) => {
      graph?.setElementState(n.id, []);
    });
    return;
  }
  const matched: string[] = [];
  allNodes.forEach((n: any) => {
    const data = n.data || {};
    const name = String(data.name || '').toLowerCase();
    if (name.includes(keyword)) {
      matched.push(n.id);
      graph?.setElementState(n.id, ['active']);
    } else {
      graph?.setElementState(n.id, ['inactive']);
    }
  });
  // 聚焦第一个匹配
  if (matched.length > 0) {
    graph.focusElement(matched[0]);
  }
}

watch(searchKeyword, () => {
  handleSearch();
});

function goDetail() {
  if (selectedNode.value) {
    router.push(`/persons/${selectedNode.value.id}`);
  }
}

function goGifts() {
  if (selectedNode.value) {
    router.push(`/gifts?person_id=${selectedNode.value.id}`);
  }
}

onMounted(async () => {
  await nextTick();
  await initGraph();
  await loadData();
});

onBeforeUnmount(() => {
  if (graph) {
    graph.destroy();
    graph = null;
  }
});
</script>

<template>
  <div class="friend-graph-wrapper">
    <!-- 搜索框 -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索朋友姓名..."
        clearable
        :prefix-icon="null"
      />
      <span class="search-hint">输入姓名高亮匹配节点</span>
    </div>

    <div class="graph-body">
      <div ref="containerRef" class="graph-container" v-loading="loading"></div>

      <!-- 空状态 -->
      <div v-if="empty && !loading" class="empty-state">
        <p>暂无朋友关系数据</p>
        <p style="font-size: 13px">请先添加朋友和礼金记录</p>
      </div>

      <!-- 侧边栏: 节点详情 -->
      <transition name="slide-right">
        <div v-if="selectedNode" class="side-panel">
          <div class="panel-header">
            <span class="panel-name">{{ selectedNode.name }}</span>
            <button class="panel-close" @click="selectedNode = null">×</button>
          </div>
          <div class="panel-body">
            <div v-if="selectedNode.is_self" class="self-badge">★ 我</div>
            <div class="panel-row" v-if="selectedNode.total_amount !== undefined">
              <span class="label">往来总额:</span>
              <span class="value gold">¥{{ formatMoney(selectedNode.total_amount) }}</span>
            </div>
            <div class="panel-row">
              <span class="label">ID:</span>
              <span>{{ selectedNode.id }}</span>
            </div>
          </div>
          <div class="panel-actions">
            <el-button size="small" type="primary" @click="goDetail">查看详情</el-button>
            <el-button size="small" @click="goGifts">往来记录</el-button>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.friend-graph-wrapper {
  position: relative;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.search-bar .el-input {
  max-width: 300px;
}

.search-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.graph-body {
  position: relative;
}

.graph-body .graph-container {
  height: 600px;
}

.side-panel {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 220px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
  padding: 14px;
  z-index: 10;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-light);
}

.panel-name {
  font-weight: 600;
  color: var(--text);
  font-size: 16px;
}

.panel-close {
  background: none;
  border: none;
  font-size: 20px;
  line-height: 1;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0 4px;
}

.panel-close:hover {
  color: var(--accent);
}

.panel-body {
  font-size: 13px;
  color: var(--text);
}

.panel-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.panel-row .label {
  color: var(--text-muted);
}

.panel-row .value.gold {
  color: var(--gold);
  font-weight: 600;
}

.self-badge {
  display: inline-block;
  margin-bottom: 8px;
  padding: 2px 8px;
  background: var(--gold-light);
  color: var(--gold);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
}

.panel-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid var(--border-light);
}

.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.25s ease;
}

.slide-right-enter-from,
.slide-right-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
