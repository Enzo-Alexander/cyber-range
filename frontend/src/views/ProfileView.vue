<template>
  <div>
    <div class="page-title">个人中心</div>
    <div class="page-sub">学习进度与解题记录</div>

    <div class="grid g2">
      <div class="card">
        <div class="t"><span style="color: var(--green)">◉</span>账号信息</div>
        <p v-if="auth.user">
          用户名：{{ auth.user.username }}<br />
          邮箱：{{ auth.user.email }}<br />
          角色：{{ auth.user.role }}<br />
          注册时间：{{ fmt(auth.user.created_at) }}
        </p>
        <p v-else>未登录</p>
      </div>
      <div class="card">
        <div class="t"><span style="color: var(--cyan)">◉</span>Phase 0 待完善</div>
        <p>分类掌握度、解题记录、收藏、账号设置等将在后续阶段实现。</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

function fmt(iso: string) {
  return new Date(iso).toLocaleString()
}
</script>
