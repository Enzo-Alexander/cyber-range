<template>
  <div>
    <div class="page-title">管理后台</div>
    <div class="page-sub">题目管理 / 用户管理 / 公告 / 配置（Phase 1 起逐步实现）</div>

    <div class="placeholder">
      <div class="code">[ admin · console ]</div>
      <p>当前管理员：{{ auth.user?.username }}（{{ auth.user?.role }}）</p>
      <p>题目管理与审核功能将在 Phase 1 上线。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
</script>
