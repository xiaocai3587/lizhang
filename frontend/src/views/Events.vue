<script setup lang="ts">
// 事件列表
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessageBox, ElMessage } from 'element-plus';
import { getEvents, deleteEvent } from '@/api';
import type { GiftEvent, EventRole } from '@/types';
import { formatDate, roleLabel, roleTagType } from '@/utils/format';

const router = useRouter();
const loading = ref(false);
const events = ref<GiftEvent[]>([]);
const search = ref('');
const roleFilter = ref<EventRole | ''>('');

const roleOptions: { value: EventRole | ''; label: string }[] = [
  { value: '', label: '全部' },
  { value: 'received', label: '收礼' },
  { value: 'given', label: '出礼' },
];

async function loadData() {
  loading.value = true;
  try {
    const params: { search?: string; role?: EventRole | '' } = {};
    if (search.value) params.search = search.value;
    if (roleFilter.value) params.role = roleFilter.value;
    events.value = await getEvents(params);
  } finally {
    loading.value = false;
  }
}

async function handleDelete(e: GiftEvent) {
  try {
    await ElMessageBox.confirm(`确定删除事件「${e.title}」吗？相关礼金记录也将删除。`, '删除确认', { type: 'warning' });
    await deleteEvent(e.id);
    ElMessage.success('删除成功');
    await loadData();
  } catch {
    // 取消
  }
}

onMounted(loadData);
</script>

<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header">
      <h1 class="page-title">事件</h1>
      <el-button type="primary" @click="router.push('/events/new')">+ 新增事件</el-button>
    </div>

    <div class="filter-bar">
      <el-input v-model="search" placeholder="搜索事件标题" clearable style="max-width: 240px" @input="loadData" @clear="loadData" />
      <el-radio-group v-model="roleFilter" @change="loadData">
        <el-radio-button v-for="o in roleOptions" :key="o.value" :value="o.value">{{ o.label }}</el-radio-button>
      </el-radio-group>
    </div>

    <el-table :data="events" stripe @row-click="(row: GiftEvent) => router.push(`/events/${row.id}`)" style="cursor: pointer">
      <el-table-column label="日期" width="120">
        <template #default="{ row }">{{ formatDate(row.date) }}</template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="160" />
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ row.event_type || '-' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="角色" width="90">
        <template #default="{ row }">
          <el-tag :type="roleTagType(row.role)" size="small">{{ roleLabel(row.role) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="笔数" width="80" prop="gift_count" />
      <el-table-column label="金额" width="120">
        <template #default="{ row }">¥{{ Number(row.gift_total || 0).toLocaleString() }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="right">
        <template #default="{ row }">
          <el-button text type="primary" @click.stop="router.push(`/events/${row.id}`)">详情</el-button>
          <el-button text type="danger" @click.stop="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div v-if="!events.length" class="empty-state">暂无事件记录</div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.page-header .page-title {
  margin: 0;
}
.filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
</style>
