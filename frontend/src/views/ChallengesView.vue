<template>
  <div>
    <div class="page-title">题库 · 题目大厅</div>
    <div class="page-sub">按分类筛选，开始你的攻防挑战（Phase 1 将接入真实题目数据）</div>

    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px">
      <button
        v-for="c in cats"
        :key="c"
        class="btn"
        :style="active === c ? 'border-color:var(--green);color:var(--green)' : ''"
        @click="active = c"
      >{{ c }}</button>
    </div>

    <div class="card" style="padding: 40px; text-align: center; color: var(--muted)">
      <div class="code" style="font-family: var(--mono); color: var(--dim)">mode: challenge lobby · {{
        active }}</div>
      <p>题目列表将在 Phase 1 上线。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const cats = ['全部', '逆向工程', '二进制漏洞', '密码学', 'Web 安全', '流量分析', '数字取证']
const active = ref('全部')
</script>
