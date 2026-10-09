<template>
  <div>
    <div class="page-title">总览</div>
    <div class="page-sub">网络安全实战靶场与流量分析学习平台</div>

    <div class="grid g4" style="margin-bottom: 24px">
      <div class="card">
        <div class="t"><span style="color: var(--green)">◈</span>题目总数</div>
        <div class="stat-num">128</div>
        <p>多题型可练习</p>
      </div>
      <div class="card">
        <div class="t"><span style="color: var(--cyan)">◈</span>已解出</div>
        <div class="stat-num">76</div>
        <p>个人进度</p>
      </div>
      <div class="card">
        <div class="t"><span style="color: var(--amber)">◈</span>我的排名</div>
        <div class="stat-num">12</div>
        <p>总榜</p>
      </div>
      <div class="card">
        <div class="t"><span style="color: var(--red)">◈</span>活跃用户</div>
        <div class="stat-num">342</div>
        <p>本周在线</p>
      </div>
    </div>

    <div class="grid g3">
      <router-link v-for="c in categories" :key="c.name" :to="'/challenges'">
        <div class="card">
          <div class="t"><span>{{ c.icon }}</span>{{ c.name }}</div>
          <p>{{ c.desc }}</p>
        </div>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
const categories = [
  { name: '逆向工程', icon: '↩', desc: '分析二进制，还原程序逻辑' },
  { name: '二进制漏洞', icon: '⚠', desc: '栈溢出 / 堆利用 / ROP' },
  { name: '密码学', icon: '🔑', desc: '古典 / 现代密码，数学攻防' },
  { name: 'Web 安全', icon: '🌐', desc: 'SQL注入 / XSS / 逻辑漏洞' },
  { name: '流量分析', icon: '⇄', desc: '报文拆解，学习网络协议' },
  { name: '数字取证', icon: '◆', desc: 'Misc / 隐写 / 取证' },
]
</script>
