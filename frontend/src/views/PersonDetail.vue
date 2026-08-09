<script setup lang="ts">
// 人物详情
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  getPerson, getPersonStats, getRelations, getGifts,
  getPersons, createRelation, deleteRelation, updatePerson,
} from '@/api';
import type { Person, PersonStats, Relation, Gift, RelationType } from '@/types';
import {
  groupLabel, groupTagType, genderLabel, calcAge, getInitial, getColorFromName,
  formatMoney, formatDate, relationLabel,
} from '@/utils/format';

const router = useRouter();
const route = useRoute();
const id = String(route.params.id);

const loading = ref(false);
const person = ref<Person | null>(null);
const stats = ref<PersonStats | null>(null);
const relations = ref<Relation[]>([]);
const gifts = ref<Gift[]>([]);

// 所有人物(用于添加关系时选择)
const allPersons = ref<Person[]>([]);

// 添加关系弹窗
const relationDialogVisible = ref(false);
const relationSubmitting = ref(false);
const relationForm = ref<{
  from_id: string;
  to_id: string;
  type: RelationType;
  notes: string;
}>({
  from_id: id,
  to_id: '',
  type: 'parent_child',
  notes: '',
});

// 关系类型选项
const relationTypeOptions: { value: RelationType; label: string; desc: string }[] = [
  { value: 'parent_child', label: '亲子', desc: 'from 是 to 的父母（from → to）' },
  { value: 'spouse', label: '配偶', desc: '夫妻关系（双向）' },
  { value: 'sibling', label: '兄弟姐妹', desc: '兄妹姐弟关系（双向）' },
];

async function loadData() {
  loading.value = true;
  try {
    const [p, s, rs, gs] = await Promise.all([
      getPerson(id),
      getPersonStats(id),
      getRelations(id),
      getGifts({ person_id: id }),
    ]);
    person.value = p;
    stats.value = s;
    relations.value = rs || [];
    gifts.value = gs || [];
  } finally {
    loading.value = false;
  }
}

// 加载所有人(打开弹窗时按需加载)
async function loadAllPersons() {
  if (allPersons.value.length) return;
  try {
    allPersons.value = await getPersons();
  } catch {
    // ignore
  }
}

// 切换礼金状态（正常往来 ↔ 已平账/不来往）
async function toggleGiftStatus() {
  if (!person.value) return;
  const newStatus = person.value.gift_status === 'excluded' ? 'normal' : 'excluded';
  const actionText = newStatus === 'excluded' ? '标记为「已平账/不来往」' : '恢复「正常往来」';
  try {
    await ElMessageBox.confirm(
      `确定将「${person.value.name}」${actionText}？` +
      (newStatus === 'excluded' ? '该人物将不再出现在回礼建议中。' : '该人物将重新出现在回礼建议中（若仍欠礼）。'),
      '提示',
      { type: 'warning' }
    );
  } catch {
    return;
  }
  try {
    await updatePerson(id, { gift_status: newStatus });
    person.value.gift_status = newStatus;
    ElMessage.success(`已${actionText}`);
  } catch {
    ElMessage.error('操作失败');
  }
}

// 礼金参与者文本
function participantsText(g: Gift, role: 'giver' | 'receiver'): string {
  const list = g.participants?.filter((p) => p.role === role) || [];
  return list.map((p) => p.person_name || `#${p.person_id}`).join('、') || '-';
}

// 打开添加关系弹窗
async function openAddRelation() {
  relationForm.value = {
    from_id: id,
    to_id: '',
    type: 'parent_child',
    notes: '',
  };
  await loadAllPersons();
  relationDialogVisible.value = true;
}

// 提交添加关系
async function submitRelation() {
  if (!relationForm.value.from_id || !relationForm.value.to_id) {
    ElMessage.warning('请选择关系双方');
    return;
  }
  if (relationForm.value.from_id === relationForm.value.to_id) {
    ElMessage.warning('不能和自己建立关系');
    return;
  }
  relationSubmitting.value = true;
  try {
    await createRelation({
      from_id: relationForm.value.from_id,
      to_id: relationForm.value.to_id,
      type: relationForm.value.type,
      notes: relationForm.value.notes,
    });
    ElMessage.success('关系已添加');
    relationDialogVisible.value = false;
    await loadData();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '添加失败');
  } finally {
    relationSubmitting.value = false;
  }
}

// 删除关系
async function removeRelation(row: Relation) {
  try {
    await ElMessageBox.confirm(
      `确定删除该关系：${row.from_name || row.from_id} ↔ ${row.to_name || row.to_id}（${relationLabel(row.type)}）？`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    );
  } catch {
    return;
  }
  try {
    await deleteRelation(row.id);
    ElMessage.success('已删除');
    await loadData();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败');
  }
}

// 关系类型方向描述(辅助用户理解 from/to)
function relationDirection(type: RelationType): string {
  if (type === 'parent_child') return '父母 → 子女';
  if (type === 'spouse') return '夫妻';
  return '兄弟姐妹';
}

onMounted(loadData);
</script>

<template>
  <div class="page-container" v-loading="loading">
    <template v-if="person">
      <!-- 头部 -->
      <div class="detail-header">
        <span class="avatar" :style="{ background: getColorFromName(person.name) }">{{ getInitial(person.name) }}</span>
        <div class="header-info">
          <div class="header-name">
            {{ person.name }}
            <el-tag v-if="person.is_self" size="small" type="warning">我</el-tag>
          </div>
          <div class="header-meta">
            <el-tag :type="groupTagType(person.group)" size="small">{{ groupLabel(person.group) }}</el-tag>
            <span :class="['gender-badge', person.gender]">{{ genderLabel(person.gender) }}</span>
            <span v-if="person.birth_year" class="muted">出生 {{ person.birth_year }} ({{ calcAge(person.birth_year) }})</span>
            <el-tag v-if="person.gift_status === 'excluded'" type="info" size="small" effect="dark">已平账/不来往</el-tag>
          </div>
          <div v-if="person.notes" class="header-notes">{{ person.notes }}</div>
        </div>
        <div class="header-actions">
          <el-button
            :type="person.gift_status === 'excluded' ? 'success' : 'warning'"
            plain
            @click="toggleGiftStatus"
          >
            {{ person.gift_status === 'excluded' ? '恢复往来' : '标记平账/不来往' }}
          </el-button>
          <el-button type="primary" @click="router.push(`/persons/${id}/edit`)">编辑</el-button>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="stat-grid" v-if="stats">
        <div class="stat-card">
          <div class="stat-label">给我随礼</div>
          <div class="stat-value gold">¥{{ formatMoney(stats.total_received) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">我给TA随礼</div>
          <div class="stat-value accent">¥{{ formatMoney(stats.total_gave) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">净差</div>
          <div class="stat-value" :class="stats.net >= 0 ? 'gold' : 'accent'">
            {{ stats.net >= 0 ? '+' : '' }}¥{{ formatMoney(stats.net) }}
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">礼金笔数</div>
          <div class="stat-value">{{ stats.gift_count }}</div>
        </div>
      </div>

      <!-- 关系列表 -->
      <div class="section">
        <div class="section-header">
          <h2 class="section-title">关系</h2>
          <el-button type="primary" size="small" @click="openAddRelation">添加关系</el-button>
        </div>
        <el-table :data="relations" stripe>
          <el-table-column label="关系人" min-width="180">
            <template #default="{ row }">
              <span>{{ row.from_name || `#${row.from_id}` }} ↔ {{ row.to_name || `#${row.to_id}` }}</span>
            </template>
          </el-table-column>
          <el-table-column label="类型" width="120">
            <template #default="{ row }">{{ relationLabel(row.type) }}</template>
          </el-table-column>
          <el-table-column label="备注" prop="notes" min-width="160" />
          <el-table-column label="操作" width="90" fixed="right">
            <template #default="{ row }">
              <el-button text type="danger" size="small" @click="removeRelation(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="!relations.length" class="empty-state">暂无关系记录</div>
      </div>

      <!-- 礼金往来 -->
      <div class="section">
        <h2 class="section-title">礼金往来</h2>
        <el-table :data="gifts" stripe>
          <el-table-column label="随礼人" min-width="140">
            <template #default="{ row }">{{ participantsText(row, 'giver') }}</template>
          </el-table-column>
          <el-table-column label="收礼人" min-width="140">
            <template #default="{ row }">{{ participantsText(row, 'receiver') }}</template>
          </el-table-column>
          <el-table-column label="金额" width="120">
            <template #default="{ row }">¥{{ formatMoney(row.amount) }}</template>
          </el-table-column>
          <el-table-column label="共同" width="70">
            <template #default="{ row }">{{ row.is_shared ? '是' : '否' }}</template>
          </el-table-column>
          <el-table-column label="事件" width="100">
            <template #default="{ row }">
              <el-button text type="primary" @click="router.push(`/events/${row.event_id}`)">查看</el-button>
            </template>
          </el-table-column>
          <el-table-column label="备注" prop="notes" min-width="140" />
        </el-table>
        <div v-if="!gifts.length" class="empty-state">暂无礼金记录</div>
      </div>
    </template>

    <!-- 添加关系弹窗 -->
    <el-dialog v-model="relationDialogVisible" title="添加关系" width="480px">
      <el-form :model="relationForm" label-width="80px">
        <el-form-item label="关系类型">
          <el-select v-model="relationForm.type" style="width: 100%">
            <el-option
              v-for="opt in relationTypeOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            >
              <span style="float: left">{{ opt.label }}</span>
              <span style="float: right; color: #999; font-size: 12px">{{ opt.desc }}</span>
            </el-option>
          </el-select>
          <div class="form-hint">{{ relationDirection(relationForm.type) }}</div>
        </el-form-item>

        <el-form-item label="甲方">
          <el-select v-model="relationForm.from_id" filterable style="width: 100%">
            <el-option
              v-for="p in allPersons"
              :key="p.id"
              :label="p.name + (p.is_self ? ' (我)' : '')"
              :value="p.id"
            />
          </el-select>
          <div class="form-hint" v-if="relationForm.type === 'parent_child'">甲方 = 父母一方</div>
        </el-form-item>

        <el-form-item label="乙方">
          <el-select v-model="relationForm.to_id" filterable style="width: 100%">
            <el-option
              v-for="p in allPersons"
              :key="p.id"
              :label="p.name + (p.is_self ? ' (我)' : '')"
              :value="p.id"
            />
          </el-select>
          <div class="form-hint" v-if="relationForm.type === 'parent_child'">乙方 = 子女</div>
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="relationForm.notes" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="relationDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="relationSubmitting" @click="submitRelation">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.detail-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 16px;
}

.avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 22px;
  flex-shrink: 0;
}

.header-info {
  flex: 1;
}

.header-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: stretch;
}

.header-name {
  font-size: 22px;
  font-weight: 600;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.muted {
  color: var(--text-muted);
  font-size: 13px;
}

.header-notes {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-muted);
  background: var(--bg-hover);
  padding: 8px 12px;
  border-radius: var(--radius);
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.form-hint {
  font-size: 12px;
  color: var(--text-muted, #999);
  margin-top: 4px;
  line-height: 1.4;
}

.gender-badge {
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 12px;
}

@media (max-width: 768px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .detail-header {
    flex-wrap: wrap;
  }
}
</style>
