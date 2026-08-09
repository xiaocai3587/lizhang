<script setup lang="ts">
// 礼金记录列表
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getGifts, getEvents, getPersons } from '@/api';
import type { Gift, GiftEvent, Person } from '@/types';
import { formatDate, formatMoney } from '@/utils/format';

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const gifts = ref<Gift[]>([]);
const events = ref<GiftEvent[]>([]);
const persons = ref<Person[]>([]);

const eventFilter = ref<string>('');
const personFilter = ref<string>('');

// 礼金关联的事件(用于显示日期/标题)
const eventMap = computed(() => {
  const m = new Map<string, GiftEvent>();
  events.value.forEach((e) => m.set(e.id, e));
  return m;
});

const personMap = computed(() => {
  const m = new Map<string, Person>();
  persons.value.forEach((p) => m.set(p.id, p));
  return m;
});

// 带事件信息 + 格式化的礼金列表
const rows = computed(() => {
  return gifts.value.map((g) => {
    const ev = eventMap.value.get(g.event_id);
    return {
      ...g,
      event_title: ev?.title || `#${g.event_id}`,
      event_date: ev?.date || '',
      givers: (g.participants?.filter((p) => p.role === 'giver') || []).map((p) => p.person_name || personMap.value.get(p.person_id)?.name || `#${p.person_id}`).join('、'),
      receivers: (g.participants?.filter((p) => p.role === 'receiver') || []).map((p) => p.person_name || personMap.value.get(p.person_id)?.name || `#${p.person_id}`).join('、'),
    };
  });
});

async function loadGifts() {
  loading.value = true;
  try {
    const params: { event_id?: string; person_id?: string } = {};
    if (eventFilter.value) params.event_id = eventFilter.value;
    if (personFilter.value) params.person_id = personFilter.value;
    gifts.value = await getGifts(params);
  } finally {
    loading.value = false;
  }
}

async function loadFilters() {
  const [es, ps] = await Promise.all([getEvents(), getPersons()]);
  events.value = es || [];
  persons.value = ps || [];
}

async function onFilterChange() {
  await loadGifts();
}

onMounted(async () => {
  // 支持从 URL 传入 person_id
  const pid = route.query.person_id;
  if (pid) personFilter.value = String(pid);
  await Promise.all([loadFilters(), loadGifts()]);
});
</script>

<template>
  <div class="page-container" v-loading="loading">
    <h1 class="page-title">礼金记录</h1>

    <div class="filter-bar">
      <el-select v-model="eventFilter" placeholder="按事件筛选" clearable filterable style="width: 220px" @change="onFilterChange">
        <el-option v-for="e in events" :key="e.id" :label="e.title" :value="e.id" />
      </el-select>
      <el-select v-model="personFilter" placeholder="按人物筛选" clearable filterable style="width: 200px" @change="onFilterChange">
        <el-option v-for="p in persons" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-button @click="loadGifts">刷新</el-button>
    </div>

    <el-table :data="rows" stripe>
      <el-table-column label="日期" width="120">
        <template #default="{ row }">{{ formatDate(row.event_date) }}</template>
      </el-table-column>
      <el-table-column label="事件" min-width="140">
        <template #default="{ row }">
          <el-button text type="primary" @click="router.push(`/events/${row.event_id}`)">{{ row.event_title }}</el-button>
        </template>
      </el-table-column>
      <el-table-column label="随礼人" min-width="140" prop="givers" />
      <el-table-column label="收礼人" min-width="140" prop="receivers" />
      <el-table-column label="金额" width="120">
        <template #default="{ row }">¥{{ formatMoney(row.amount) }}</template>
      </el-table-column>
      <el-table-column label="共同" width="70">
        <template #default="{ row }">{{ row.is_shared ? '是' : '否' }}</template>
      </el-table-column>
      <el-table-column label="备注" prop="notes" min-width="140" />
    </el-table>
    <div v-if="!rows.length" class="empty-state">暂无礼金记录</div>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
</style>
