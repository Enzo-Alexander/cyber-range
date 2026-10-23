<template>
  <div v-if="loading" class="loading">加载中…</div>
  <div v-else-if="article" class="detail">
    <div class="back" @click="$router.back()">← 返回</div>
    <div class="art-card">
      <div class="art-head">
        <span class="art-type" :class="article.type">
          {{ article.type === 'announcement' ? '公告' : '文章' }}
        </span>
        <h1>{{ article.title }}</h1>
        <div class="art-meta">
          <span>作者：{{ article.author }}</span>
          <span class="dim">{{ formatDate(article.created_at) }}</span>
        </div>
      </div>
      <ArticleContent :content="article.content" />
    </div>
  </div>
  <div v-else class="loading">文章不存在</div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import ArticleContent from '../components/ArticleContent.vue'
import { articlesApi, type Article } from '../api/articles'
import { parseServerDate } from '../utils/datetime'

const route = useRoute()
const article = ref<Article | null>(null)
const loading = ref(true)

function formatDate(s: string) {
  const d = parseServerDate(s)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

onMounted(async () => {
  try {
    const id = Number(route.params.id)
    article.value = await articlesApi.get(id)
  } catch {
    article.value = null
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.back {
  font-family: var(--mono);
  font-size: 15px;
  color: var(--cyan);
  cursor: pointer;
  margin-bottom: 16px;
  display: inline-block;
  padding: 6px 16px;
  border: 1px solid var(--line2);
  border-radius: 6px;
  transition: 0.15s;
}
.back:hover { color: var(--green); border-color: var(--green); background: rgba(var(--green-rgb), 0.05); }
.art-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 32px 40px;
}
.art-head { margin-bottom: 24px; padding-bottom: 20px; border-bottom: 1px solid var(--line); }
.art-type {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 4px;
}
.art-type.announcement { color: var(--red); border: 1px solid rgba(var(--red-rgb), 0.5); }
.art-type.article { color: var(--cyan); border: 1px solid rgba(var(--cyan-rgb), 0.5); }
.art-head h1 {
  margin: 12px 0 8px;
  font-size: 26px;
  color: var(--text-strong);
}
.art-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--muted);
}
.art-meta .dim { color: var(--dim); }
.loading { text-align: center; color: var(--dim); padding: 60px; font-family: var(--mono); }
</style>
