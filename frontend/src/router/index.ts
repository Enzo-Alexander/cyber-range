import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        { path: '', name: 'home', component: () => import('../views/HomeView.vue') },
        { path: 'challenges', name: 'challenges', component: () => import('../views/ChallengesView.vue') },
        { path: 'traffic', name: 'traffic', component: () => import('../views/TrafficView.vue') },
        { path: 'leaderboard', name: 'leaderboard', component: () => import('../views/LeaderboardView.vue') },
        { path: 'announcements', name: 'announcements', component: () => import('../views/AnnouncementView.vue') },
        { path: 'profile', name: 'profile', component: () => import('../views/ProfileView.vue'), meta: { requiresAuth: true } },
        { path: 'admin', name: 'admin', component: () => import('../views/AdminView.vue'), meta: { requiresAuth: true } },
      ],
    },
    { path: '/login', name: 'login', component: () => import('../views/AuthView.vue'), props: { mode: 'login' } },
    { path: '/register', name: 'register', component: () => import('../views/AuthView.vue'), props: { mode: 'register' } },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (auth.isAuthenticated && !auth.user) {
    await auth.fetchMe()
  }
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login' }
  }
})

export default router
