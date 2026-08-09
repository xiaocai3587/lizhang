<script setup lang="ts">
// 人物列表
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessageBox, ElMessage } from 'element-plus';
import { getPersons, deletePerson } from '@/api';
import type { Person, PersonGroup } from '@/types';
import { groupLabel, groupTagType, genderLabel, calcAge, getInitial, getColorFromName } from '@/utils/format';

const router = useRouter();
const loading = ref(false);
const persons = ref<Person[]>([]);
const search = ref('');
const groupFilter = ref<PersonGroup | ''>('');

const groupOptions: { value: PersonGroup | ''; label: string }[] = [
  { value: '', label: '全部' },
  { value: 'my_family', label: '我的家族' },
  { value: 'wife_family', label: '老婆家族' },
  { value: 'friends', label: '朋友' },
];

const filtered = computed(() => {
  return persons.value.filter((p) => {
    if (groupFilter.value && p.group !== groupFilter.value) return false;
    if (search.value && !p.name.includes(search.value)) return false;
    return true;
  });
});

async function loadData() {
  loading.value = true;
  try {
    const params: { search?: string; group?: PersonGroup | '' } = {};
    if (search.value) params.search = search.value;
    if (groupFilter.value) params.group = groupFilter.value;
    persons.value = await getPersons(params);
  } finally {
    loading.value = false;
  }
}

async function handleDelete(p: Person) {
  try {
    await ElMessageBox.confirm(`确定删除人物「${p.name}」吗？相关礼金记录也可能受影响。`, '删除确认', {
      type: 'warning',
    });
    await deletePerson(p.id);
    ElMessage.success('删除成功');
    await loadData();
  } catch (e) {
    // 取消或失败
  }
}

onMounted(loadData);
</script>

<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header">
      <h1 class="page-title">人物</h1>
      <el-button type="primary" @click="router.push('/persons/new')">+ 新增人物</el-button>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <el-input v-model="search" placeholder="搜索姓名" clearable style="max-width: 240px" @input="loadData" @clear="loadData" />
      <el-radio-group v-model="groupFilter" @change="loadData">
        <el-radio-button v-for="o in groupOptions" :key="o.value" :value="o.value">{{ o.label }}</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 桌面表格 -->
    <el-table :data="filtered" stripe class="hide-mobile" @row-click="(row: Person) => router.push(`/persons/${row.id}`)" style="cursor: pointer">
      <el-table-column label="姓名" min-width="140">
        <template #default="{ row }">
          <div class="name-cell">
            <span class="avatar" :style="{ background: getColorFromName(row.name) }">{{ getInitial(row.name) }}</span>
            <span>{{ row.name }}</span>
            <el-tag v-if="row.is_self" size="small" type="warning">我</el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="分组" width="120">
        <template #default="{ row }">
          <el-tag :type="groupTagType(row.group)" size="small">{{ groupLabel(row.group) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="性别" width="80">
        <template #default="{ row }">
          <span :class="['gender-badge', row.gender]">{{ genderLabel(row.gender) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="出生年份" width="100">
        <template #default="{ row }">{{ row.birth_year || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="right">
        <template #default="{ row }">
          <el-button text type="primary" @click.stop="router.push(`/persons/${row.id}`)">详情</el-button>
          <el-button text type="primary" @click.stop="router.push(`/persons/${row.id}/edit`)">编辑</el-button>
          <el-button text type="danger" @click.stop="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 移动端卡片 -->
    <div class="mobile-cards hide-desktop">
      <div v-for="p in filtered" :key="p.id" class="person-card" @click="router.push(`/persons/${p.id}`)">
        <div class="card-top">
          <span class="avatar" :style="{ background: getColorFromName(p.name) }">{{ getInitial(p.name) }}</span>
          <div class="card-info">
            <div class="card-name">{{ p.name }} <el-tag v-if="p.is_self" size="small" type="warning">我</el-tag></div>
            <div class="card-meta">
              <el-tag :type="groupTagType(p.group)" size="small">{{ groupLabel(p.group) }}</el-tag>
              <span class="gender-badge" :class="p.gender">{{ genderLabel(p.gender) }}</span>
              <span v-if="p.birth_year" class="muted">{{ calcAge(p.birth_year) }}</span>
            </div>
          </div>
        </div>
        <div class="card-actions">
          <el-button size="small" @click.stop="router.push(`/persons/${p.id}/edit`)">编辑</el-button>
          <el-button size="small" type="danger" @click.stop="handleDelete(p)">删除</el-button>
        </div>
      </div>
      <div v-if="!filtered.length" class="empty-state">暂无人物数据</div>
    </div>
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

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.gender-badge {
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.mobile-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.person-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 14px;
  cursor: pointer;
}

.card-top {
  display: flex;
  gap: 12px;
  align-items: center;
}

.card-info {
  flex: 1;
}

.card-name {
  font-weight: 600;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  flex-wrap: wrap;
}

.muted {
  color: var(--text-muted);
  font-size: 12px;
}

.card-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  justify-content: flex-end;
}
</style>
