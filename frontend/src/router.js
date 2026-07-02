import { createRouter, createWebHistory } from 'vue-router'
import { checkAuth, isGuest } from '@/composables/useAuth'

const routes = [
  {
    path: '/marketing/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/marketing/signup',
    name: 'Signup',
    component: () => import('@/views/SignupView.vue'),
    meta: { public: true },
  },
  {
    path: '/marketing',
    component: () => import('@/layouts/AppLayout.vue'),
    children: [
      { path: '', name: 'Calendar', component: () => import('@/views/CalendarView.vue') },
      { path: 'posts', name: 'Posts', component: () => import('@/views/PostsView.vue') },
      { path: 'posts/:postId', name: 'PostDetail', component: () => import('@/views/PostsView.vue'), props: true },
      { path: 'projects', name: 'Projects', component: () => import('@/views/ProjectsView.vue') },
      { path: 'todo', redirect: to => ({ name: 'Projects', query: { view: 'todo', ...to.query } }) },
      { path: 'assets', name: 'Assets', component: () => import('@/views/AssetsView.vue') },
      { path: 'analytics', name: 'Analytics', component: () => import('@/views/AnalyticsView.vue') },
      { path: 'settings', name: 'Settings', component: () => import('@/views/SettingsView.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/marketing' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

let authChecked = false

router.beforeEach(async (to) => {
  if (to.meta?.public) return true

  if (!authChecked) {
    await checkAuth()
    authChecked = true
  }

  if (isGuest.value) {
    return { name: 'Login', query: { next: to.fullPath } }
  }

  return true
})

export default router
