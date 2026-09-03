import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/views/AppLayout.vue'
import Dashboard from '@/views/Dashboard.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
    },
    {
      path: '/',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'dashboard',
          component: Dashboard,
        },
        {
          path: 'analysis',
          name: 'analysis',
          component: () => import('@/views/Analysis.vue'),
        },
        {
          path: 'patients',
          name: 'patients',
          component: () => import('@/views/Patients.vue'),
        },
        {
          path: 'reports',
          name: 'reports',
          component: () => import('@/views/Reports.vue'),
        },
        {
          path: 'history',
          name: 'history',
          component: () => import('@/views/History.vue'),
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/Settings.vue'),
        },
        {
          path: 'help',
          name: 'help',
          component: () => import('@/views/Help.vue'),
        },
      ],
    },
  ],
})

export default router