<script setup lang="ts">
// 主布局: 顶部导航栏 + 内容区
import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';

const route = useRoute();
const mobileMenuOpen = ref(false);

const menuItems = [
  { path: '/', label: '首页', icon: 'home' },
  { path: '/persons', label: '人物', icon: 'users' },
  { path: '/events', label: '事件', icon: 'calendar' },
  { path: '/gifts', label: '礼金', icon: 'gift' },
  { path: '/graph', label: '关系图', icon: 'graph' },
  { path: '/settings', label: '设置', icon: 'settings' },
];

const activeIndex = computed(() => {
  const path = route.path;
  // 精确匹配 / 和 /persons 等,子路由也算激活
  if (path === '/') return '/';
  // /persons/new, /persons/1 都算 persons 激活
  const top = '/' + path.split('/')[1];
  return top;
});

function closeMobile() {
  mobileMenuOpen.value = false;
}
</script>

<template>
  <div class="layout">
    <!-- 顶部导航栏 -->
    <header class="navbar">
      <div class="navbar-inner">
        <!-- Logo -->
        <router-link to="/" class="logo" @click="closeMobile">
          <span class="logo-icon">礼</span>
          <span class="logo-text">礼账</span>
        </router-link>

        <!-- 桌面菜单 -->
        <nav class="menu hide-mobile">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="menu-item"
            :class="{ active: activeIndex === item.path }"
          >
            {{ item.label }}
          </router-link>
        </nav>

        <div class="navbar-right">
          <ThemeToggle />
          <!-- 移动端汉堡按钮 -->
          <button class="hamburger hide-desktop" @click="mobileMenuOpen = !mobileMenuOpen">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <line x1="3" y1="6" x2="21" y2="6" v-if="!mobileMenuOpen" />
              <line x1="3" y1="12" x2="21" y2="12" v-if="!mobileMenuOpen" />
              <line x1="3" y1="18" x2="21" y2="18" v-if="!mobileMenuOpen" />
              <line x1="6" y1="6" x2="18" y2="18" v-if="mobileMenuOpen" />
              <line x1="18" y1="6" x2="6" y2="18" v-if="mobileMenuOpen" />
            </svg>
          </button>
        </div>
      </div>

      <!-- 移动端下拉菜单 -->
      <transition name="slide">
        <nav v-show="mobileMenuOpen" class="mobile-menu hide-desktop">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="mobile-menu-item"
            :class="{ active: activeIndex === item.path }"
            @click="mobileMenuOpen = false"
          >
            {{ item.label }}
          </router-link>
        </nav>
      </transition>
    </header>

    <!-- 内容区 -->
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: var(--shadow-sm);
}

.navbar-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.logo-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--accent);
  color: var(--gold);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  font-family: serif;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
}

.menu {
  display: flex;
  gap: 4px;
  flex: 1;
  margin-left: 32px;
}

.menu-item {
  padding: 8px 16px;
  border-radius: var(--radius);
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.menu-item:hover {
  background: var(--bg-hover);
  color: var(--accent);
}

.menu-item.active {
  background: var(--accent-light);
  color: var(--accent);
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.hamburger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--text);
  cursor: pointer;
}

.mobile-menu {
  display: flex;
  flex-direction: column;
  padding: 8px 16px;
  border-top: 1px solid var(--border);
}

.mobile-menu-item {
  padding: 12px 16px;
  color: var(--text);
  border-radius: var(--radius);
  font-size: 15px;
}

.mobile-menu-item.active {
  background: var(--accent-light);
  color: var(--accent);
}

.content {
  flex: 1;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 768px) {
  .navbar-inner {
    padding: 0 12px;
  }
}
</style>
