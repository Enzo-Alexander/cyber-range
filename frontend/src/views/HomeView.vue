<template>
  <div>
    <div class="page-title">总览</div>
    <div class="page-sub">网络安全实战靶场与流量分析学习平台</div>

    <div class="grid g4" style="margin-bottom: 24px">
      <div class="card">
        <div class="t"><span style="color: var(--green)">◈</span>题目总数</div>
        <div class="stat-num">{{ totalCount }}</div>
        <p>多题型可练习</p>
      </div>
      <div class="card">
        <div class="t"><span style="color: var(--cyan)">◈</span>已解出</div>
        <div class="stat-num">{{ auth.isAuthenticated ? solvedCount : '--' }}</div>
        <p>个人进度</p>
      </div>
      <div class="card">
        <div class="t"><span style="color: var(--amber)">◈</span>我的排名</div>
        <div class="stat-num">{{ auth.isAuthenticated ? '#' + myRank : '--' }}</div>
        <p>总榜</p>
      </div>
      <div class="card">
        <div class="t"><span style="color: var(--red)">◈</span>签到</div>
        <div class="stat-num">--</div>
        <p>即将上线</p>
      </div>
    </div>

    <div class="grid g3">
      <router-link
        v-for="c in categories"
        :key="c.name"
        :to="`/challenges?category=${encodeURIComponent(c.name)}`"
      >
        <div class="card">
          <div class="t"><span>{{ c.icon }}</span>{{ c.name }}</div>
          <p>{{ c.desc }}</p>
        </div>
      </router-link>
    </div>

    <div class="articles-panel">
      <div class="panel-head">
        <span class="ok">◈ 公告与文章</span>
        <span class="dim">{{ articles.length }} 篇</span>
      </div>
      <div class="articles-list">
        <div v-if="!loadingArticles && articles.length === 0" class="empty-art">
          暂无文章，等待管理员发布
        </div>
        <div v-for="a in articles" :key="a.id" class="art-item">
          <router-link :to="`/article/${a.id}`" class="art-row">
            <span class="art-type" :class="a.type">{{ a.type === 'announcement' ? '公告' : '文章' }}</span>
            <span class="art-title">{{ a.title }}</span>
            <span class="art-meta">
              <span>{{ a.author }}</span>
              <span class="dim">{{ formatDate(a.created_at) }}</span>
              <span class="arrow">›</span>
            </span>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { challengesApi } from '../api/challenges'
import { articlesApi, type Article } from '../api/articles'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

const totalCount = ref(0)
const solvedCount = ref(0)
const myRank = ref<number | string>('-')
const articles = ref<Article[]>([])
const loadingArticles = ref(true)

const categories = [
  { name: '逆向工程', icon: '↩', desc: '分析二进制，还原程序逻辑' },
  { name: '二进制漏洞', icon: '⚠', desc: '栈溢出 / 堆利用 / ROP' },
  { name: '密码学', icon: '🔑', desc: '古典 / 现代密码，数学攻防' },
  { name: 'Web安全', icon: '🌐', desc: 'SQL注入 / XSS / 逻辑漏洞' },
  { name: '流量分析', icon: '⇄', desc: '报文拆解，学习网络协议' },
  { name: '数字取证', icon: '◆', desc: 'Misc / 隐写 / 取证' },
]

function formatDate(s: string) {
  const d = new Date(s)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(async () => {
  try {
    const all = await challengesApi.list()
    totalCount.value = all.length
  } catch {
    totalCount.value = 0
  }

  if (auth.isAuthenticated) {
    try {
      const p = await challengesApi.profile()
      solvedCount.value = p.total_solved
      myRank.value = p.rank
    } catch {
      solvedCount.value = 0
    }
  }

  try {
    articles.value = await articlesApi.list()
  } catch {
    articles.value = []
  } finally {
    loadingArticles.value = false
  }
})
</script>

<style scoped>
.articles-panel {
  margin-top: 24px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(16, 24, 35, 0.5);
  overflow: hidden;
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
  font-family: var(--mono);
  font-size: 13px;
}
.panel-head .ok { color: var(--green); }
.panel-head .dim { color: var(--dim); }
.articles-list {
  max-height: 320px;
  overflow-y: auto;
}
.art-item {
  border-bottom: 1px dashed var(--line);
}
.art-item:last-child { border-bottom: none; }
.art-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: inherit;
  text-decoration: none;
  transition: 0.15s;
}
.art-row:hover { background: rgba(0, 255, 159, 0.04); }
.art-type {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}
.art-type.announcement { color: var(--red); border: 1px solid rgba(255, 59, 48, 0.5); }
.art-type.article { color: var(--cyan); border: 1px solid rgba(0, 224, 255, 0.5); }
.art-title {
  flex: 1;
  font-weight: 600;
  color: #eaf4ff;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.art-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--muted);
  flex-shrink: 0;
}
.art-meta .dim { color: var(--dim); }
.arrow { color: var(--dim); }
.empty-art {
  padding: 40px;
  text-align: center;
  color: var(--dim);
  font-size: 14px;
}
</style>
