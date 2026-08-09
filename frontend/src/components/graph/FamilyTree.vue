<script setup lang="ts">
// G6 v5 家庭单元族谱树组件（夫妻对节点）
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { Graph } from '@antv/g6';
import { useRouter } from 'vue-router';
import { getFamilyTree } from '@/api';
import type { HouseholdGraphData, PersonGroup, HouseholdNode } from '@/types';
import { groupLabel, genderLabel, calcAge } from '@/utils/format';

const props = defineProps<{
  anchorId: string | null;
  group: PersonGroup;
}>();

const emit = defineEmits<{
  (e: 'setAnchor', id: string): void;
}>();

const router = useRouter();

const containerRef = ref<HTMLDivElement | null>(null);
const loading = ref(false);
const empty = ref(false);
let graph: Graph | null = null;

// 选中的家庭单元(用于弹出框)
const selectedHousehold = ref<HouseholdNode | null>(null);
const popoverStyle = ref<{ left: string; top: string }>({ left: '0px', top: '0px' });

// 性别颜色
function genderColor(gender: string): string {
  if (gender === 'male') return '#4a90d9';
  if (gender === 'female') return '#e8788a';
  return '#999999';
}

// 构建家庭单元节点的 HTML 内容（含外框）
function buildHouseholdHTML(data: any): string {
  const members = data.members || [];
  const isAnchor = data.is_anchor;
  const borderColor = isAnchor ? '#d4a843' : '#d0d0d0';
  const bgColor = isAnchor ? 'rgba(212,168,67,0.12)' : '#ffffff';
  const borderWidth = isAnchor ? '3px' : '1.5px';

  // 单个成员的 HTML（两行：正式名(小名) / 称谓）
  function memberHTML(m: any): string {
    const color = genderColor(m.gender);
    const selfStar = m.is_self ? '<span style="color:#d4a843;font-size:11px;">★</span>' : '';
    const nick = m.nickname ? `<span style="color:#999;font-size:9px;">(${m.nickname})</span>` : '';
    const title = m.title ? `<div style="font-size:9px;color:#888;margin-top:1px;">${m.title}</div>` : '';
    return `<div style="display:flex;flex-direction:column;align-items:center;padding:0 4px;">
      <div style="width:34px;height:34px;border-radius:50%;background:${color};color:#fff;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,0.2);">${m.name ? m.name.charAt(0) : '?'}</div>
      <div style="margin-top:3px;font-size:10px;color:#333;max-width:64px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:center;">${selfStar}${m.name || ''}${nick}</div>
      ${title}
    </div>`;
  }

  // 夫妻之间的 ♥ 分隔符
  const heart = '<div style="display:flex;align-items:center;justify-content:center;color:#d4a843;font-size:16px;padding:0 2px;align-self:center;margin-top:-10px;">&#9829;</div>';

  // 用 join 拼接，确保 ♥ 在两个成员之间
  const inner = members.map(memberHTML).join(members.length === 2 ? heart : '');

  // 外框：带边框的圆角矩形
  return `<div style="display:flex;align-items:flex-start;justify-content:center;padding:8px 6px;border:${borderWidth} solid ${borderColor};background:${bgColor};border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">${inner}</div>`;
}

// 计算节点坐标：父系左侧、自己中间、母系右侧，按代数(y轴)分层
function layoutNodes(data: HouseholdGraphData) {
  const NODE_W = 160;
  const NODE_GAP = 25;
  const DEPTH_GAP = 175;

  // 按 depth 分组
  const byDepth = new Map<number, HouseholdNode[]>();
  for (const n of data.nodes) {
    if (!byDepth.has(n.depth)) byDepth.set(n.depth, []);
    byDepth.get(n.depth)!.push(n);
  }

  const depths = [...byDepth.keys()].sort((a, b) => a - b);
  const minDepth = depths[0] || 0;
  const positions = new Map<string, { x: number; y: number }>();

  // 估算各 side 在每层的最大宽度，用于左右偏移
  for (const depth of depths) {
    const group = byDepth.get(depth)!;
    const paternal = group.filter((n) => n.side === 'paternal');
    const selfNodes = group.filter((n) => n.side === 'self');
    const maternal = group.filter((n) => n.side === 'maternal');

    const y = (depth - minDepth) * DEPTH_GAP;
    const step = NODE_W + NODE_GAP;

    // 父系：从中间向左排列
    paternal.forEach((n, i) => {
      positions.set(n.id, { x: -(i + 1) * step, y });
    });

    // 自己：放中间
    selfNodes.forEach((n, i) => {
      positions.set(n.id, { x: (i - selfNodes.length / 2 + 0.5) * step, y });
    });

    // 母系：从中间向右排列
    maternal.forEach((n, i) => {
      positions.set(n.id, { x: (i + 1) * step, y });
    });
  }

  return positions;
}

// 转换 API 数据为 G6 格式（含坐标）
function transformData(data: HouseholdGraphData) {
  const posMap = layoutNodes(data);

  const nodes = data.nodes.map((n) => {
    const pos = posMap.get(n.id) || { x: 0, y: 0 };
    return {
      id: String(n.id),
      data: { ...n },
      style: { x: pos.x, y: pos.y },
    };
  });
  const edges = data.links.map((l, i) => ({
    id: `e-${i}`,
    source: String(l.source),
    target: String(l.target),
    data: { type: l.type },
  }));
  return { nodes, edges };
}

// 初始化图
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
    // 不使用自动布局，用节点自带的 x/y 坐标
    node: {
      type: 'html',
      style: (d: any) => {
        const data = d.data || {};
        const memberCount = (data.members || []).length;
        const w = memberCount === 2 ? 160 : 90;
        return {
          size: [w, 88],
          fill: 'transparent',
          stroke: 'transparent',
          cursor: 'pointer',
          innerHTML: buildHouseholdHTML(data),
        };
      },
    },
    edge: {
      style: {
        stroke: '#b0b0b0',
        lineWidth: 1.5,
        endArrow: false,
      },
    },
    behaviors: ['zoom-canvas', 'drag-canvas', 'drag-element'],
  });

  // 点击节点
  graph.on('node:click', (evt: any) => {
    const id = evt.target?.id;
    if (id === undefined) return;
    showNodePopover(String(id), evt);
  });

  // 点击画布空白处关闭弹窗
  graph.on('canvas:click', () => {
    selectedHousehold.value = null;
  });
}

// 显示节点弹窗
function showNodePopover(id: string, evt: any) {
  const nodeData = graph?.getNodeData(id);
  if (!nodeData) return;
  const data = (nodeData as any).data || {};
  selectedHousehold.value = {
    id: String(id),
    members: data.members || [],
    depth: data.depth ?? 0,
    is_anchor: !!data.is_anchor,
  };
  try {
    const rect = containerRef.value?.getBoundingClientRect();
    if (rect && evt.client) {
      popoverStyle.value = {
        left: `${evt.client.x - rect.left}px`,
        top: `${evt.client.y - rect.top}px`,
      };
    }
  } catch {
    // ignore
  }
}

// 加载数据
async function loadData() {
  if (!graph) return;
  loading.value = true;
  empty.value = false;
  selectedHousehold.value = null;
  try {
    const params: { anchor_id?: string; group: PersonGroup } = { group: props.group };
    if (props.anchorId) params.anchor_id = props.anchorId;
    const data = await getFamilyTree(params);
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

// 跳转详情（跳到家庭中第一个成员）
function goDetail(personId?: string) {
  const pid = personId || selectedHousehold.value?.members?.[0]?.id;
  if (pid) {
    router.push(`/persons/${pid}`);
  }
}

// 设为锚点（用家庭中第一个成员作为锚点）
function setAnchor(personId?: string) {
  const pid = personId || selectedHousehold.value?.members?.[0]?.id;
  if (pid) {
    emit('setAnchor', pid);
    selectedHousehold.value = null;
  }
}

onMounted(async () => {
  await nextTick();
  await initGraph();
  await loadData();
});

watch(
  () => [props.anchorId, props.group],
  () => {
    loadData();
  }
);

onBeforeUnmount(() => {
  if (graph) {
    graph.destroy();
    graph = null;
  }
});
</script>

<template>
  <div class="family-tree-wrapper">
    <div ref="containerRef" class="graph-container" v-loading="loading"></div>

    <!-- 空状态 -->
    <div v-if="empty && !loading" class="empty-state">
      <p>暂无族谱数据</p>
      <p style="font-size: 13px">请先添加人物和关系</p>
    </div>

    <!-- 节点弹窗 -->
    <div v-if="selectedHousehold" class="node-popover" :style="popoverStyle" @click.stop>
      <div class="popover-header">
        <span class="popover-name">
          {{ selectedHousehold.members.map((m) => m.name).join(' ♥ ') }}
        </span>
        <button class="popover-close" @click="selectedHousehold = null">×</button>
      </div>
      <div class="popover-body">
        <div v-for="m in selectedHousehold.members" :key="m.id" class="member-row">
          <span class="member-avatar" :style="{ background: genderColor(m.gender) }">
            {{ m.name ? m.name.charAt(0) : '?' }}
          </span>
          <div class="member-info">
            <span class="member-name">
              {{ m.name }}<span v-if="m.nickname" class="member-nick">（{{ m.nickname }}）</span><span v-if="m.is_self" class="self-star">★</span>
              <el-tag v-if="m.title" size="small" type="info" class="member-title-tag">{{ m.title }}</el-tag>
            </span>
            <span class="member-meta">
              {{ genderLabel(m.gender) }}
              {{ m.birth_year ? ' · ' + calcAge(m.birth_year) : '' }}
            </span>
          </div>
          <div class="member-actions">
            <el-button size="small" link @click="goDetail(m.id)">详情</el-button>
            <el-button size="small" link @click="setAnchor(m.id)">设为锚点</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 图例 -->
    <div class="legend">
      <div class="legend-item">
        <span class="dot" style="background:#4a90d9"></span> 男
      </div>
      <div class="legend-item">
        <span class="dot" style="background:#e8788a"></span> 女
      </div>
      <div class="legend-item">
        <span class="dot" style="background:#d4a843"></span> 锚点家庭
      </div>
      <div class="legend-item">
        <span style="color:#d4a843;font-size:14px">♥</span> 夫妻
      </div>
    </div>
  </div>
</template>

<style scoped>
.family-tree-wrapper {
  position: relative;
}

.family-tree-wrapper .graph-container {
  height: 600px;
}

.legend {
  position: absolute;
  top: 12px;
  left: 12px;
  display: flex;
  gap: 16px;
  background: var(--bg-elevated, #fff);
  border: 1px solid var(--border, #e0e0e0);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 12px;
  color: var(--text, #333);
  z-index: 5;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend .dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.node-popover {
  position: absolute;
  z-index: 10;
  min-width: 240px;
  background: var(--bg-elevated, #fff);
  border: 1px solid var(--border, #e0e0e0);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  padding: 14px;
  transform: translate(12px, 12px);
}

.popover-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-light, #eee);
}

.popover-name {
  font-weight: 600;
  color: var(--text, #333);
  font-size: 15px;
}

.popover-close {
  background: none;
  border: none;
  font-size: 20px;
  line-height: 1;
  color: var(--text-muted, #999);
  cursor: pointer;
  padding: 0 4px;
}

.popover-close:hover {
  color: var(--accent, #c44536);
}

.popover-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.member-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.member-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.member-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.member-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text, #333);
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.member-nick {
  font-size: 12px;
  color: var(--text-muted, #999);
  font-weight: 400;
}

.member-title-tag {
  font-size: 11px;
}

.self-star {
  color: #d4a843;
  margin-left: 2px;
}

.member-meta {
  font-size: 12px;
  color: var(--text-muted, #999);
}

.member-actions {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.empty-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: var(--text-muted, #999);
}
</style>
