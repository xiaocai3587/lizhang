<script setup lang="ts">
// 设置
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useTheme } from '@/stores/theme';
import { exportData, importData } from '@/api';

const { dark, toggle } = useTheme();
const exporting = ref(false);
const importing = ref(false);

async function handleExport() {
  exporting.value = true;
  try {
    const blob = await exportData();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `lizhang-export-${new Date().toISOString().slice(0, 10)}.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    ElMessage.success('导出成功');
  } finally {
    exporting.value = false;
  }
}

async function handleImport(file: File) {
  importing.value = true;
  try {
    const result = await importData(file);
    ElMessage.success(`导入完成: 人物 ${result.persons || 0}, 关系 ${result.relations || 0}, 事件 ${result.events || 0}, 礼金 ${result.gifts || 0}`);
    if (result.errors?.length) {
      ElMessage.warning(`有 ${result.errors.length} 条错误`);
    }
  } finally {
    importing.value = false;
  }
}

function onFileChange(uploadFile: any) {
  if (uploadFile?.raw) {
    handleImport(uploadFile.raw);
  }
}
</script>

<template>
  <div class="page-container">
    <h1 class="page-title">设置</h1>

    <!-- 主题设置 -->
    <div class="settings-card">
      <h2 class="card-title">主题</h2>
      <div class="setting-row">
        <div class="setting-info">
          <div class="setting-name">深色模式</div>
          <div class="setting-desc">切换浅色/深色主题</div>
        </div>
        <el-switch :model-value="dark" @change="toggle" />
      </div>
    </div>

    <!-- 数据管理 -->
    <div class="settings-card">
      <h2 class="card-title">数据管理</h2>
      <div class="setting-row">
        <div class="setting-info">
          <div class="setting-name">导出数据</div>
          <div class="setting-desc">将所有人物、关系、事件、礼金数据导出为 CSV 压缩包</div>
        </div>
        <el-button type="primary" :loading="exporting" @click="handleExport">导出 CSV</el-button>
      </div>
      <div class="setting-row">
        <div class="setting-info">
          <div class="setting-name">导入数据</div>
          <div class="setting-desc">从 CSV 文件导入数据（支持人物/关系/事件/礼金）</div>
        </div>
        <el-upload
          :show-file-list="false"
          :auto-upload="false"
          accept=".csv,.zip"
          :on-change="onFileChange"
        >
          <el-button :loading="importing">选择文件导入</el-button>
        </el-upload>
      </div>
    </div>

    <!-- 关于 -->
    <div class="settings-card">
      <h2 class="card-title">关于</h2>
      <div class="about-info">
        <div class="about-row"><span class="label">应用名称:</span><span>礼账 Lizhang</span></div>
        <div class="about-row"><span class="label">版本:</span><span>1.0.0</span></div>
        <div class="about-row"><span class="label">描述:</span><span>礼金管理 + 关系图谱</span></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 16px;
  max-width: 700px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 16px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-light);
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  gap: 16px;
}

.setting-info {
  flex: 1;
}

.setting-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
}

.setting-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

.about-info {
  font-size: 14px;
  color: var(--text);
}

.about-row {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.about-row .label {
  color: var(--text-muted);
  min-width: 80px;
}
</style>
