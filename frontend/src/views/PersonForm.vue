<script setup lang="ts">
// 人物新增/编辑表单
import { ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { getPerson, createPerson, updatePerson } from '@/api';
import type { PersonGroup, Gender, GiftStatus, PersonCreate } from '@/types';

const router = useRouter();
const route = useRoute();

const id = computed(() => {
  const v = route.params.id;
  return v ? String(v) : null;
});
const isEdit = computed(() => id.value !== null);
const loading = ref(false);
const submitting = ref(false);

const form = ref<{
  name: string;
  nickname: string;
  group: PersonGroup;
  gender: Gender;
  birth_year: number | null;
  is_self: boolean;
  title: string;
  gift_status: GiftStatus;
  notes: string;
}>({
  name: '',
  nickname: '',
  group: 'my_family',
  gender: 'male',
  birth_year: null,
  is_self: false,
  title: '',
  gift_status: 'normal',
  notes: '',
});

const groupOptions: { value: PersonGroup; label: string }[] = [
  { value: 'my_family', label: '我的家族' },
  { value: 'wife_family', label: '老婆家族' },
  { value: 'friends', label: '朋友' },
];

const genderOptions: { value: Gender; label: string }[] = [
  { value: 'male', label: '男' },
  { value: 'female', label: '女' },
  { value: 'unknown', label: '未知' },
];

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  group: [{ required: true, message: '请选择分组', trigger: 'change' }],
};

const formRef = ref();

async function loadData() {
  if (!id.value) return;
  loading.value = true;
  try {
    const p = await getPerson(id.value);
    form.value = {
      name: p.name,
      nickname: p.nickname || '',
      group: p.group,
      gender: p.gender,
      birth_year: p.birth_year ? Number(p.birth_year) : null,
      is_self: p.is_self,
      title: p.title || '',
      gift_status: (p.gift_status || 'normal') as GiftStatus,
      notes: p.notes || '',
    };
  } finally {
    loading.value = false;
  }
}

async function handleSubmit() {
  try {
    await formRef.value?.validate();
  } catch {
    return;
  }
  submitting.value = true;
  try {
    const payload: PersonCreate = {
      name: form.value.name,
      nickname: form.value.nickname,
      group: form.value.group,
      gender: form.value.gender,
      birth_year: form.value.birth_year === null ? '' : String(form.value.birth_year),
      is_self: form.value.is_self,
      title: form.value.title,
      gift_status: form.value.gift_status,
      notes: form.value.notes,
    };
    if (id.value) {
      await updatePerson(id.value, payload);
      ElMessage.success('修改成功');
      router.push(`/persons/${id.value}`);
    } else {
      const created = await createPerson(payload);
      ElMessage.success('创建成功');
      router.push(`/persons/${created.id}`);
    }
  } finally {
    submitting.value = false;
  }
}

function handleCancel() {
  router.back();
}

onMounted(loadData);
</script>

<template>
  <div class="page-container" v-loading="loading">
    <h1 class="page-title">{{ isEdit ? '编辑人物' : '新增人物' }}</h1>
    <div class="form-wrapper">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" label-position="right">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" maxlength="50" />
        </el-form-item>
        <el-form-item label="小名">
          <el-input v-model="form.nickname" placeholder="小名/昵称（可选）" maxlength="50" />
        </el-form-item>
        <el-form-item label="分组" prop="group">
          <el-select v-model="form.group" placeholder="请选择分组" style="width: 100%">
            <el-option v-for="o in groupOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio v-for="o in genderOptions" :key="o.value" :value="o.value">{{ o.label }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="出生年份">
          <el-input-number v-model="form.birth_year" :min="1900" :max="new Date().getFullYear()" placeholder="如 1990" controls-position="right" />
        </el-form-item>
        <el-form-item label="是否自己">
          <el-checkbox v-model="form.is_self">标记为「我」</el-checkbox>
        </el-form-item>
        <el-form-item label="称谓">
          <el-input v-model="form.title" placeholder="留空则自动推算（如 大舅、堂哥）" maxlength="20" />
          <div class="form-tip">关系图中显示的称谓，留空时系统根据关系自动推算</div>
        </el-form-item>
        <el-form-item label="礼金状态">
          <el-radio-group v-model="form.gift_status">
            <el-radio value="normal">正常往来</el-radio>
            <el-radio value="excluded">已平账/不来往</el-radio>
          </el-radio-group>
          <div class="form-tip">标记为「已平账/不来往」的人不会出现在回礼建议列表中</div>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="备注信息" maxlength="500" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">{{ isEdit ? '保存' : '创建' }}</el-button>
          <el-button @click="handleCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.form-wrapper {
  max-width: 600px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.form-tip {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.4;
  margin-top: 4px;
}
</style>
