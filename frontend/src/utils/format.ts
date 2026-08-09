// 通用格式化工具
import type { PersonGroup, Gender, EventRole, RelationType } from '@/types';

// 格式化金额
export function formatMoney(amount: number): string {
  if (amount === null || amount === undefined || isNaN(amount)) return '0';
  return amount.toLocaleString('zh-CN', { maximumFractionDigits: 2 });
}

// 带符号金额
export function formatSignedMoney(amount: number): string {
  const formatted = formatMoney(Math.abs(amount));
  if (amount > 0) return `+${formatted}`;
  if (amount < 0) return `-${formatted}`;
  return formatted;
}

// 分组标签
export function groupLabel(group: PersonGroup): string {
  const map: Record<PersonGroup, string> = {
    my_family: '我的家族',
    wife_family: '老婆家族',
    friends: '朋友',
  };
  return map[group] || group;
}

export function groupTagType(group: PersonGroup): 'primary' | 'success' | 'warning' {
  const map: Record<PersonGroup, 'primary' | 'success' | 'warning'> = {
    my_family: 'primary',
    wife_family: 'success',
    friends: 'warning',
  };
  return map[group] || 'primary';
}

// 性别标签
export function genderLabel(gender: Gender): string {
  const g = (gender || '').toLowerCase();
  if (g === 'male' || g === '男') return '男';
  if (g === 'female' || g === '女') return '女';
  return '未知';
}

// 角色标签
export function roleLabel(role: EventRole): string {
  return role === 'received' ? '收礼' : '出礼';
}

export function roleTagType(role: EventRole): 'success' | 'warning' {
  return role === 'received' ? 'success' : 'warning';
}

// 关系类型标签
export function relationLabel(type: RelationType): string {
  const map: Record<RelationType, string> = {
    parent_child: '亲子',
    spouse: '配偶',
    sibling: '兄弟姐妹',
  };
  return map[type] || type;
}

// 格式化日期 (YYYY-MM-DD)
export function formatDate(date: string | null | undefined): string {
  if (!date) return '-';
  try {
    const d = new Date(date);
    if (isNaN(d.getTime())) return date;
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  } catch {
    return date;
  }
}

// 计算年龄
export function calcAge(birthYear: string | null | undefined): string {
  if (!birthYear) return '-';
  const year = Number(birthYear);
  if (isNaN(year)) return '-';
  const age = new Date().getFullYear() - year;
  return `${age}岁`;
}

// 获取姓名首字符作为头像
export function getInitial(name: string): string {
  if (!name) return '?';
  return name.charAt(0).toUpperCase();
}

// 根据姓名生成颜色
export function getColorFromName(name: string): string {
  if (!name) return '#c44536';
  const colors = ['#c44536', '#d4a843', '#4a90d9', '#e8788a', '#52c41a', '#722ed1'];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}
