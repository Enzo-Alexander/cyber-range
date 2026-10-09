<template>
  <div class="app">
    <header class="topbar">
      <div class="in">
        <router-link to="/" class="brand">
          <span class="sh"></span>CYBERRANGE
        </router-link>
        <nav class="nav">
          <router-link to="/challenges">题库</router-link>
          <router-link to="/traffic">流量分析</router-link>
          <router-link to="/leaderboard">排行榜</router-link>
          <router-link to="/announcements">公告</router-link>
        </nav>
        <div class="top-actions">
          <template v-if="auth.isAuthenticated && auth.user">
            <router-link :to="auth.user.role === 'admin' ? '/admin' : '/profile'">
              <button class="btn" :class="{ alert: auth.user.role === 'admin' }">
                {{ auth.user.role === 'admin' ? 'ADMIN' : auth.user.username }}
              </button>
            </router-link>
            <button class="btn" @click="onLogout">退出</button>
          </template>
          <template v-else>
            <router-link to="/login"><button class="btn alert">登录 / 注册</button></router-link>
          </template>
        </div>
      </div>
    </header>

    <main class="container">
      <router-view />
    </main>

    <footer class="status-bar">
      <span>mode: <span class="ok">online</span></span>
      <span>CYBERRANGE · phase 0 scaffold</span>
      <span class="warn">⚠ design preview</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

function onLogout() {
  auth.logout()
  router.push('/')
}
</script>
