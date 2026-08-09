<script setup lang="ts">
// 事件详情 + 礼金管理
import { ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  getEvent, createEvent, updateEvent, deleteEvent,
  getGifts, createGift, updateGift, deleteGift,
  getPersons, getEventTypes,
} from '@/api';
import type { GiftEvent, Gift, Person, EventRole, ParticipantRole, EventCreate } from '@/types';
import { formatDate, formatMoney, roleLabel, roleTagType } from '@/utils/format';

const router = useRouter();
const route = useRoute();

const id = computed(() => {
  const v = route.params.id;
  return v ? String(v) : null;
});
const isCreate = computed(() => id.value === null);
const loading = ref(false);
const submitting = ref(false);

const event = ref<GiftEvent | null>(null);
const gifts = ref<Gift[]>([]);
const persons = ref<Person[]>([]);
const eventTypes = ref<string[]>([]);

// 自己的人物 id
const selfPersonId = computed(() => {
  const self = persons.value.find((p) => p.is_self);
  return self?.id ?? null;
});

// 事件创建/编辑表单
const eventForm = ref<{
  title: string;
  event_type: string;
  date: string;
  role: EventRole;
  notes: string;
}>({
  title: '',
  event_type: '',
  date: new Date().toISOString().slice(0, 10),
  role: 'received',
  notes: '',
});

const eventFormRef = ref();
const eventRules = {
  title: [{ required: true, message: '请输入事件标题', trigger: 'blur' }],
  date: [{ required: true, message: '请选择日期', trigger: 'change' }],
};

// 根据事件角色，对方角色标签
const otherRoleLabel = computed<ParticipantRole>(() => {
  // received: 我收礼 → 对方是 giver(随礼人)
  // given: 我出礼 → 对方是 receiver(收礼人)
  return event.value?.role === 'given' ? 'receiver' : 'giver';
});

// 礼金弹窗
const giftDialogVisible = ref(false);
const editingGift = ref<Gift | null>(null);

// 事件编辑弹窗
const eventEditDialogVisible = ref(false);
const giftForm = ref<{
  amount: number;
  is_shared: boolean;
  notes: string;
  others: string[]; // 对方人物 id 列表
}>({
  amount: 0,
  is_shared: false,
  notes: '',
  others: [],
});

// 批量录入弹窗
const batchDialogVisible = ref(false);
const batchRows = ref<{ person_id: string | null; amount: number }[]>([]);

async function loadEvent() {
  if (!id.value) return;
  loading.value = true;
  try {
    const [ev, gs, ps, types] = await Promise.all([
      getEvent(id.value),
      getGifts({ event_id: id.value }),
      getPersons(),
      getEventTypes(),
    ]);
    event.value = ev;
    gifts.value = gs || [];
    persons.value = ps || [];
    eventTypes.value = types || [];
  } finally {
    loading.value = false;
  }
}

async function loadPersonsForCreate() {
  loading.value = true;
  try {
    const [ps, types] = await Promise.all([getPersons(), getEventTypes()]);
    persons.value = ps || [];
    eventTypes.value = types || [];
  } finally {
    loading.value = false;
  }
}

// 保存事件(创建或编辑)
async function handleSaveEvent() {
  try {
    await eventFormRef.value?.validate();
  } catch {
    return;
  }
  submitting.value = true;
  try {
    const payload: EventCreate = {
      title: eventForm.value.title,
      event_type: eventForm.value.event_type || undefined,
      date: eventForm.value.date,
      role: eventForm.value.role,
      notes: eventForm.value.notes,
    };
    if (id.value) {
      const updated = await updateEvent(id.value, payload);
      event.value = updated;
      eventEditDialogVisible.value = false;
      ElMessage.success('保存成功');
    } else {
      const created = await createEvent(payload);
      ElMessage.success('创建成功');
      router.replace(`/events/${created.id}`);
    }
  } finally {
    submitting.value = false;
  }
}

// 进入编辑事件模式
function startEditEvent() {
  if (!event.value) return;
  eventForm.value = {
    title: event.value.title,
    event_type: event.value.event_type || '',
    date: event.value.date,
    role: event.value.role,
    notes: event.value.notes || '',
  };
  eventEditDialogVisible.value = true;
}

// 打开添加礼金弹窗
function openAddGift() {
  editingGift.value = null;
  giftForm.value = { amount: 0, is_shared: false, notes: '', others: [] };
  giftDialogVisible.value = true;
}

// 打开编辑礼金弹窗
function openEditGift(g: Gift) {
  editingGift.value = g;
  const others = (g.participants || [])
    .filter((p) => p.role === otherRoleLabel.value)
    .map((p) => p.person_id);
  giftForm.value = {
    amount: g.amount,
    is_shared: g.is_shared,
    notes: g.notes || '',
    others,
  };
  giftDialogVisible.value = true;
}

// 提交礼金
async function handleSubmitGift() {
  if (!event.value) return;
  if (!giftForm.value.others.length) {
    ElMessage.warning('请至少选择一个人物');
    return;
  }
  if (!giftForm.value.amount || giftForm.value.amount <= 0) {
    ElMessage.warning('请输入金额');
    return;
  }
  submitting.value = true;
  try {
    // 构造参与者
    const otherRole = otherRoleLabel.value;
    const selfRole: ParticipantRole = otherRole === 'giver' ? 'receiver' : 'giver';
    const participants: { person_id: string; role: ParticipantRole }[] = [];
    giftForm.value.others.forEach((pid) => {
      participants.push({ person_id: pid, role: otherRole });
    });
    // 自动加入自己
    if (selfPersonId.value) {
      participants.push({ person_id: selfPersonId.value, role: selfRole });
    }
    const payload = {
      event_id: event.value.id,
      amount: giftForm.value.amount,
      is_shared: giftForm.value.is_shared,
      notes: giftForm.value.notes,
      participants,
    };
    if (editingGift.value) {
      await updateGift(editingGift.value.id, payload);
      ElMessage.success('修改成功');
    } else {
      await createGift(payload);
      ElMessage.success('添加成功');
    }
    giftDialogVisible.value = false;
    await loadEvent();
  } finally {
    submitting.value = false;
  }
}

// 删除礼金
async function handleDeleteGift(g: Gift) {
  try {
    await ElMessageBox.confirm('确定删除该礼金记录吗？', '删除确认', { type: 'warning' });
    await deleteGift(g.id);
    ElMessage.success('删除成功');
    await loadEvent();
  } catch {
    // 取消
  }
}

// 删除事件
async function handleDeleteEvent() {
  if (!event.value) return;
  try {
    await ElMessageBox.confirm(`确定删除事件「${event.value.title}」吗？`, '删除确认', { type: 'warning' });
    await deleteEvent(event.value.id);
    ElMessage.success('删除成功');
    router.push('/events');
  } catch {
    // 取消
  }
}

// 批量录入
function openBatch() {
  batchRows.value = [
    { person_id: null, amount: 0 },
    { person_id: null, amount: 0 },
    { person_id: null, amount: 0 },
  ];
  batchDialogVisible.value = true;
}

function addBatchRow() {
  batchRows.value.push({ person_id: null, amount: 0 });
}

function removeBatchRow(idx: number) {
  batchRows.value.splice(idx, 1);
}

async function handleSubmitBatch() {
  if (!event.value) return;
  const valid = batchRows.value.filter((r) => r.person_id && r.amount > 0);
  if (!valid.length) {
    ElMessage.warning('请至少填写一行有效数据');
    return;
  }
  submitting.value = true;
  try {
    const otherRole = otherRoleLabel.value;
    const selfRole: ParticipantRole = otherRole === 'giver' ? 'receiver' : 'giver';
    for (const row of valid) {
      const participants: { person_id: string; role: ParticipantRole }[] = [
        { person_id: row.person_id!, role: otherRole },
      ];
      if (selfPersonId.value) {
        participants.push({ person_id: selfPersonId.value, role: selfRole });
      }
      await createGift({
        event_id: event.value.id,
        amount: row.amount,
        is_shared: false,
        notes: '',
        participants,
      });
    }
    ElMessage.success(`成功添加 ${valid.length} 条礼金`);
    batchDialogVisible.value = false;
    await loadEvent();
  } finally {
    submitting.value = false;
  }
}

// 礼金参与者文本
function giversText(g: Gift): string {
  return (g.participants?.filter((p) => p.role === 'giver') || [])
    .map((p) => p.person_name || persons.value.find((x) => x.id === p.person_id)?.name || `#${p.person_id}`)
    .join('、') || '-';
}
function receiversText(g: Gift): string {
  return (g.participants?.filter((p) => p.role === 'receiver') || [])
    .map((p) => p.person_name || persons.value.find((x) => x.id === p.person_id)?.name || `#${p.person_id}`)
    .join('、') || '-';
}

onMounted(() => {
  if (isCreate.value) {
    loadPersonsForCreate();
  } else {
    loadEvent();
  }
});
</script>

<template>
  <div class="page-container" v-loading="loading">
    <!-- 创建事件模式 -->
    <template v-if="isCreate">
      <h1 class="page-title">新增事件</h1>
      <div class="form-wrapper">
        <el-form ref="eventFormRef" :model="eventForm" :rules="eventRules" label-width="90px">
          <el-form-item label="标题" prop="title">
            <el-input v-model="eventForm.title" placeholder="如 张三婚礼" maxlength="100" />
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="eventForm.event_type" placeholder="选择或输入类型" allow-create filterable clearable style="width:100%">
              <el-option v-for="t in eventTypes" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item>
          <el-form-item label="日期" prop="date">
            <el-date-picker v-model="eventForm.date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width:100%" />
          </el-form-item>
          <el-form-item label="角色">
            <el-radio-group v-model="eventForm.role">
              <el-radio value="received">收礼</el-radio>
              <el-radio value="given">出礼</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="eventForm.notes" type="textarea" :rows="3" maxlength="500" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="submitting" @click="handleSaveEvent">创建</el-button>
            <el-button @click="router.back()">取消</el-button>
          </el-form-item>
        </el-form>
      </div>
    </template>

    <!-- 事件详情模式 -->
    <template v-else-if="event">
      <div class="page-header">
        <h1 class="page-title">{{ event.title }}</h1>
        <div class="header-actions">
          <el-button type="primary" @click="openAddGift">+ 添加礼金</el-button>
          <el-button @click="openBatch">批量录入</el-button>
        </div>
      </div>

      <!-- 事件信息卡片 -->
      <div class="event-info-card">
        <div class="info-row">
          <span class="info-label">日期:</span><span>{{ formatDate(event.date) }}</span>
          <span class="info-label" style="margin-left:24px">类型:</span>
          <el-tag size="small">{{ event.event_type || '-' }}</el-tag>
          <span class="info-label" style="margin-left:24px">角色:</span>
          <el-tag :type="roleTagType(event.role)" size="small">{{ roleLabel(event.role) }}</el-tag>
        </div>
        <div class="info-row" v-if="event.notes">
          <span class="info-label">备注:</span><span>{{ event.notes }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">礼金合计:</span>
          <span class="gold">¥{{ formatMoney(event.gift_total) }} ({{ event.gift_count }}笔)</span>
        </div>
        <div class="info-actions">
          <el-button text type="primary" @click="startEditEvent">编辑事件</el-button>
          <el-button text type="danger" @click="handleDeleteEvent">删除事件</el-button>
        </div>
      </div>

      <!-- 礼金列表 -->
      <h2 class="section-title">礼金列表</h2>
      <el-table :data="gifts" stripe>
        <el-table-column label="随礼人" min-width="150">
          <template #default="{ row }">{{ giversText(row) }}</template>
        </el-table-column>
        <el-table-column label="收礼人" min-width="150">
          <template #default="{ row }">{{ receiversText(row) }}</template>
        </el-table-column>
        <el-table-column label="金额" width="120">
          <template #default="{ row }">¥{{ formatMoney(row.amount) }}</template>
        </el-table-column>
        <el-table-column label="共同" width="70">
          <template #default="{ row }">{{ row.is_shared ? '是' : '否' }}</template>
        </el-table-column>
        <el-table-column label="备注" prop="notes" min-width="140" />
        <el-table-column label="操作" width="140" align="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="openEditGift(row)">编辑</el-button>
            <el-button text type="danger" @click="handleDeleteGift(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!gifts.length" class="empty-state">暂无礼金记录，点击「添加礼金」开始记录</div>
    </template>

    <!-- 事件编辑弹窗 -->
    <el-dialog v-model="eventEditDialogVisible" title="编辑事件" width="480px">
      <el-form ref="eventFormRef" :model="eventForm" :rules="eventRules" label-width="90px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="eventForm.title" placeholder="如 张三婚礼" maxlength="100" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="eventForm.event_type" placeholder="选择或输入类型" allow-create filterable clearable style="width:100%">
            <el-option v-for="t in eventTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期" prop="date">
          <el-date-picker v-model="eventForm.date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width:100%" />
        </el-form-item>
        <el-form-item label="角色">
          <el-radio-group v-model="eventForm.role">
            <el-radio value="received">收礼</el-radio>
            <el-radio value="given">出礼</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="eventForm.notes" type="textarea" :rows="3" maxlength="500" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="eventEditDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSaveEvent">保存</el-button>
      </template>
    </el-dialog>

    <!-- 礼金弹窗 -->
    <el-dialog v-model="giftDialogVisible" :title="editingGift ? '编辑礼金' : '添加礼金'" width="480px">
      <el-form :model="giftForm" label-width="90px">
        <el-form-item :label="otherRoleLabel === 'giver' ? '随礼人' : '收礼人'">
          <el-select v-model="giftForm.others" multiple filterable placeholder="选择人物" style="width:100%">
            <el-option v-for="p in persons" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额">
          <el-input-number v-model="giftForm.amount" :min="0" :precision="2" controls-position="right" style="width:100%" />
        </el-form-item>
        <el-form-item label="是否共同">
          <el-switch v-model="giftForm.is_shared" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="giftForm.notes" type="textarea" :rows="2" maxlength="200" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="giftDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmitGift">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批量录入弹窗 -->
    <el-dialog v-model="batchDialogVisible" title="批量录入礼金" width="560px">
      <p class="batch-tip">每行填写一位{{ otherRoleLabel === 'giver' ? '随礼人' : '收礼人' }}和金额，提交后将批量创建礼金记录。</p>
      <el-table :data="batchRows" border size="small">
        <el-table-column label="人物" min-width="200">
          <template #default="{ row }">
            <el-select v-model="row.person_id" filterable placeholder="选择人物" size="small" style="width:100%">
              <el-option v-for="p in persons" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="160">
          <template #default="{ row }">
            <el-input-number v-model="row.amount" :min="0" :precision="2" size="small" controls-position="right" style="width:100%" />
          </template>
        </el-table-column>
        <el-table-column label="" width="70" align="center">
          <template #default="{ $index }">
            <el-button text type="danger" size="small" @click="removeBatchRow($index)">删</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-button size="small" style="margin-top:8px" @click="addBatchRow">+ 添加行</el-button>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmitBatch">批量提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}
.page-header .page-title {
  margin: 0;
}
.header-actions {
  display: flex;
  gap: 8px;
}
.form-wrapper {
  max-width: 600px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
}
.event-info-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  margin-bottom: 24px;
}
.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.info-label {
  color: var(--text-muted);
  font-size: 13px;
}
.gold {
  color: var(--gold);
  font-weight: 600;
}
.info-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 12px 0;
}
.batch-tip {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0 0 12px 0;
}
</style>
