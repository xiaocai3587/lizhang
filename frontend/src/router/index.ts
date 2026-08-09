// 路由配置
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import MainLayout from '@/layouts/MainLayout.vue';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
      { path: 'persons', name: 'Persons', component: () => import('@/views/Persons.vue') },
      { path: 'persons/new', name: 'PersonNew', component: () => import('@/views/PersonForm.vue') },
      {
        path: 'persons/:id',
        name: 'PersonDetail',
        component: () => import('@/views/PersonDetail.vue'),
        props: true,
      },
      {
        path: 'persons/:id/edit',
        name: 'PersonEdit',
        component: () => import('@/views/PersonForm.vue'),
        props: true,
      },
      { path: 'events', name: 'Events', component: () => import('@/views/Events.vue') },
      { path: 'events/new', name: 'EventNew', component: () => import('@/views/EventDetail.vue') },
      {
        path: 'events/:id',
        name: 'EventDetail',
        component: () => import('@/views/EventDetail.vue'),
        props: true,
      },
      { path: 'gifts', name: 'Gifts', component: () => import('@/views/Gifts.vue') },
      { path: 'graph', name: 'Graph', component: () => import('@/views/Graph.vue') },
      { path: 'settings', name: 'Settings', component: () => import('@/views/Settings.vue') },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
