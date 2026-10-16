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
      <div class="art-content" v-html="renderedContent"></div>
    </div>
  </div>
  <div v-else class="loading">文章不存在</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { articlesApi, type Article } from '../api/articles'

const route = useRoute()
const article = ref<Article | null>(null)
const loading = ref(true)

const renderedContent = computed(() => {
  if (!article.value) return ''
  let html = escapeHtml(article.value.content)
  // 转换 markdown 图片 ![alt](url)
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" />')
  // 转换标题
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>')
  // 换行转 <br>
  html = html.replace(/\n/g, '<br>')
  return html
})

function escapeHtml(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function formatDate(s: string) {
  const d = new Date(s)
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
.back:hover { color: var(--green); border-color: var(--green); background: rgba(0, 255, 159, 0.05); }
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
.art-type.announcement { color: var(--red); border: 1px solid rgba(255, 59, 48, 0.5); }
.art-type.article { color: var(--cyan); border: 1px solid rgba(0, 224, 255, 0.5); }
.art-head h1 {
  margin: 12px 0 8px;
  font-size: 26px;
  color: #eaf4ff;
}
.art-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--muted);
}
.art-meta .dim { color: var(--dim); }
.art-content {
  font-size: 15px;
  line-height: 1.9;
  color: var(--text);
}
.art-content :deep(img) {
  max-width: 100%;
  border-radius: 8px;
  margin: 16px 0;
  border: 1px solid var(--line);
}
.art-content :deep(h2) {
  font-size: 18px;
  color: #eaf4ff;
  margin: 20px 0 10px;
  padding-left: 10px;
  border-left: 3px solid var(--green);
}
.art-content :deep(h3) {
  font-size: 16px;
  color: var(--cyan);
  margin: 16px 0 8px;
}
.loading { text-align: center; color: var(--dim); padding: 60px; font-family: var(--mono); }
</style>
