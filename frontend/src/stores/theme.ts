// 主题状态管理 - 深色模式
import { ref, watch } from 'vue';

const STORAGE_KEY = 'lizhang-theme';

// 读取本地存储的初始值
function getInitialDark(): boolean {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored !== null) return stored === 'dark';
  // 默认浅色
  return false;
}

const dark = ref<boolean>(getInitialDark());

// 应用主题到 html 元素
function applyTheme(isDark: boolean) {
  const html = document.documentElement;
  if (isDark) {
    html.classList.add('dark');
  } else {
    html.classList.remove('dark');
  }
}

// 初始化时立即应用一次
applyTheme(dark.value);

// 监听变化，持久化并应用
watch(dark, (val) => {
  localStorage.setItem(STORAGE_KEY, val ? 'dark' : 'light');
  applyTheme(val);
});

export function useTheme() {
  function toggle() {
    dark.value = !dark.value;
  }

  function setDark(val: boolean) {
    dark.value = val;
  }

  return { dark, toggle, setDark };
}
