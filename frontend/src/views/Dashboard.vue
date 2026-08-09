<script setup lang="ts">
// 仪表盘
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { getDashboardStats, getSuggestions } from '@/api';
import type { DashboardStats, Suggestion } from '@/types';
import { formatMoney, formatDate, roleLabel, roleTagType } from '@/utils/format';

const router = useRouter();
const loading = ref(false);
const stats = ref<DashboardStats | null>(null);
const suggestions = ref<Suggestion[]>([]);

const maxTrend = computed(() => {
  if (!stats.value?.monthly_trend) return 1;
  return Math.max(
    1,
    ...stats.value.monthly_trend.map((t) => Math.max(t.received, t.given))
  );
});

async function loadData() {
  loading.value = true;
  try {
    const [s, sg] = await Promise.all([getDashboardStats(), getSuggestions()]);
    stats.value = s;
    suggestions.value = sg || [];
  } finally {
    loading.value = false;
  }
}

function goEvent(id: string) {
  router.push(`/events/${id}`);
}

function goPerson(id: string) {
  router.push(`/persons/${id}`);
}

onMounted(loadData);
</script>

<template>
  <div class="page-container" v-loading="loading">
    <h1 class="page-title">仪表盘</h1>

    <!-- 统计卡片 -->
    <div class="stat-grid" v-if="stats">
      <div class="stat-card">
        <div class="stat-label">人物总数</div>
        <div class="stat-value">{{ stats.persons_count }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">事件总数</div>
        <div class="stat-value">{{ stats.events_count }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">收礼总额</div>
        <div class="stat-value gold">¥{{ formatMoney(stats.total_received) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">出礼总额</div>
        <div class="stat-value accent">¥{{ formatMoney(stats.total_given) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">净差额</div>
        <div class="stat-value" :class="stats.net >= 0 ? 'gold' : 'accent'">
          {{ stats.net >= 0 ? '+' : '' }}¥{{ formatMoney(stats.net) }}
        </div>
      </div>
    </div>

    <div class="dashboard-grid" v-if="stats">
      <!-- 最近事件 -->
      <div class="dashboard-card span-2">
        <div class="card-header">
          <h2 class="card-title">最近事件</h2>
          <el-button text type="primary" @click="router.push('/events')">查看全部</el-button>
        </div>
        <el-table
          :data="stats.recent_events"
          stripe
          @row-click="(row: any) => goEvent(row.id)"
          style="cursor: pointer"
        >
          <el-table-column prop="title" label="事件" min-width="140" />
          <el-table-column label="日期" width="110">
            <template #default="{ row }">{{ formatDate(row.date) }}</template>
          </el-table-column>
          <el-table-column label="角色" width="80">
            <template #default="{ row }">
              <el-tag :type="roleTagType(row.role)" size="small">{{ roleLabel(row.role) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="笔数" width="70" prop="gift_count" />
          <el-table-column label="金额" width="100">
            <template #default="{ row }">¥{{ formatMoney(row.gift_total) }}</template>
          </el-table-column>
        </el-table>
        <div v-if="!stats.recent_events?.length" class="empty-state">暂无事件记录</div>
      </div>

      <!-- 回礼建议 -->
      <div class="dashboard-card">
        <div class="card-header">
          <h2 class="card-title">回礼建议</h2>
        </div>
        <div class="suggestion-list">
          <div
            v-for="s in suggestions"
            :key="s.person_id"
            class="suggestion-item"
            @click="goPerson(s.person_id)"
          >
            <div class="suggestion-name">{{ s.person_name }}</div>
            <div class="suggestion-amount">建议 ¥{{ formatMoney(s.suggested_amount) }}</div>
            <div class="suggestion-reason">{{ s.reason }}</div>
          </div>
          <div v-if="!suggestions.length" class="empty-state">暂无建议</div>
        </div>
      </div>

      <!-- 月度趋势 -->
      <div class="dashboard-card span-2">
        <div class="card-header">
          <h2 class="card-title">月度趋势</h2>
        </div>
        <div class="trend-chart" v-if="stats.monthly_trend?.length">
          <div class="trend-bars">
            <div v-for="t in stats.monthly_trend" :key="t.month" class="trend-bar-group">
              <div class="trend-bars-pair">
                <div class="trend-bar-wrap">
                  <span v-if="t.received > 0" class="trend-value gold">¥{{ formatMoney(t.received) }}</span>
                  <div
                    class="trend-bar bar-received"
                    :style="{ height: (t.received / maxTrend) * 180 + 'px' }"
                    :title="`收礼 ¥${formatMoney(t.received)}`"
                  ></div>
                </div>
                <div class="trend-bar-wrap">
                  <span v-if="t.given > 0" class="trend-value accent">¥{{ formatMoney(t.given) }}</span>
                  <div
                    class="trend-bar bar-given"
                    :style="{ height: (t.given / maxTrend) * 180 + 'px' }"
                    :title="`出礼 ¥${formatMoney(t.given)}`"
                  ></div>
                </div>
              </div>
              <div class="trend-label">{{ t.month }}</div>
            </div>
          </div>
          <div class="trend-legend">
            <span class="legend-item"><i class="dot gold"></i>收礼</span>
            <span class="legend-item"><i class="dot accent"></i>出礼</span>
          </div>
        </div>
        <div v-else class="empty-state">暂无趋势数据</div>
      </div>

      <!-- TOP往来人物 -->
      <div class="dashboard-card">
        <div class="card-header">
          <h2 class="card-title">往来 TOP</h2>
        </div>
        <div class="top-list">
          <div
            v-for="(p, idx) in stats.top_persons"
            :key="p.person_id"
            class="top-item"
            @click="goPerson(p.person_id)"
          >
            <span class="top-rank">{{ idx + 1 }}</span>
            <span class="top-name">{{ p.name }}</span>
            <span class="top-amount">¥{{ formatMoney(p.total_amount) }}</span>
          </div>
          <div v-if="!stats.top_persons?.length" class="empty-state">暂无数据</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.dashboard-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
}

.span-2 {
  grid-column: span 2;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 360px;
  overflow-y: auto;
  padding-right: 4px;
}

.suggestion-item {
  padding: 10px;
  border-radius: var(--radius);
  background: var(--bg-hover);
  cursor: pointer;
  transition: background 0.2s;
}

.suggestion-item:hover {
  background: var(--accent-light);
}

.suggestion-name {
  font-weight: 600;
  color: var(--text);
}

.suggestion-amount {
  color: var(--gold);
  font-weight: 600;
  font-size: 14px;
  margin: 2px 0;
}

.suggestion-reason {
  font-size: 12px;
  color: var(--text-muted);
}

.trend-chart {
  display: flex;
  flex-direction: column;
}

.trend-bars {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  min-height: 200px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.trend-bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 50px;
}

.trend-bars-pair {
  display: flex;
  gap: 4px;
  align-items: flex-end;
  height: 180px;
}

.trend-bar {
  width: 18px;
  min-height: 2px;
  border-radius: 3px 3px 0 0;
  transition: height 0.3s ease;
}

.trend-bar-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 3px;
  height: 100%;
}

.trend-value {
  font-size: 10px;
  font-weight: 600;
  white-space: nowrap;
  line-height: 1;
}

.trend-value.gold {
  color: var(--gold);
}

.trend-value.accent {
  color: var(--accent);
}

.bar-received {
  background: var(--gold);
}

.bar-given {
  background: var(--accent);
}

.trend-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}

.trend-legend {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--text-muted);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.dot.gold {
  background: var(--gold);
}

.dot.accent {
  background: var(--accent);
}

.top-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.top-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: var(--radius);
  background: var(--bg-hover);
  cursor: pointer;
}

.top-item:hover {
  background: var(--accent-light);
}

.top-rank {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.top-name {
  flex: 1;
  color: var(--text);
  font-size: 14px;
}

.top-amount {
  color: var(--gold);
  font-weight: 600;
  font-size: 13px;
}

@media (max-width: 1024px) {
  .stat-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  .span-2 {
    grid-column: span 1;
  }
}

@media (max-width: 768px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
