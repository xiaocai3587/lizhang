<script setup lang="ts">
// 关系图谱
import { ref, computed, onMounted } from 'vue';
import FamilyTree from '@/components/graph/FamilyTree.vue';
import FriendGraph from '@/components/graph/FriendGraph.vue';
import { getPersons } from '@/api';
import type { Person, PersonGroup } from '@/types';
import { groupLabel } from '@/utils/format';

const activeTab = ref<PersonGroup | 'friends'>('my_family');
const persons = ref<Person[]>([]);
const anchorId = ref<string | null>(null);

// 当前族谱的分组
const currentGroup = computed<PersonGroup>(() => {
  if (activeTab.value === 'my_family') return 'my_family';
  if (activeTab.value === 'wife_family') return 'wife_family';
  return 'friends';
});

// 当前分组的人物(用于锚点选择)
const groupPersons = computed(() => {
  return persons.value.filter((p) => p.group === currentGroup.value);
});

const isFamily = computed(() => activeTab.value !== 'friends');

// 默认锚点: 当前分组中 is_self 的人物, 否则第一个
function setDefaultAnchor() {
  if (activeTab.value === 'friends') return;
  const list = groupPersons.value;
  const self = list.find((p) => p.is_self);
  anchorId.value = self?.id ?? list[0]?.id ?? null;
}

function onTabChange() {
  if (activeTab.value !== 'friends') {
    setDefaultAnchor();
  }
}

function onSetAnchor(id: string) {
  anchorId.value = id;
}

async function loadPersons() {
  persons.value = await getPersons();
  setDefaultAnchor();
}

onMounted(loadPersons);
</script>

<template>
  <div class="page-container">
    <h1 class="page-title">关系图谱</h1>

    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <el-tab-pane label="我的家族族谱" name="my_family" />
      <el-tab-pane label="老婆家族族谱" name="wife_family" />
      <el-tab-pane label="朋友关系网" name="friends" />
    </el-tabs>

    <!-- 族谱 -->
    <template v-if="isFamily">
      <div class="anchor-bar">
        <span class="anchor-label">锚点人物:</span>
        <el-select v-model="anchorId" placeholder="选择锚点" filterable style="width: 240px">
          <el-option
            v-for="p in groupPersons"
            :key="p.id"
            :label="p.name + (p.is_self ? ' (我)' : '')"
            :value="p.id"
          />
        </el-select>
        <span class="anchor-hint">{{ groupLabel(currentGroup) }} · 以选中人物为中心展示上下代关系</span>
      </div>
      <FamilyTree :anchor-id="anchorId" :group="currentGroup" @set-anchor="onSetAnchor" />
    </template>

    <!-- 朋友关系网 -->
    <template v-else>
      <FriendGraph />
    </template>
  </div>
</template>

<style scoped>
.anchor-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.anchor-label {
  font-size: 14px;
  color: var(--text);
  font-weight: 500;
}

.anchor-hint {
  font-size: 12px;
  color: var(--text-muted);
}
</style>
