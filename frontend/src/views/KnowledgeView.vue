<template>
  <div class="knowledge">
    <aside class="catalog">
      <div class="catalog-head">
        <div>
          <div class="kicker">KNOWLEDGE</div>
          <h1>知识库</h1>
        </div>
        <span class="count">{{ loading ? '--' : articles.length }} 篇</span>
      </div>

      <div class="catalog-scroll">
        <div v-if="loading" class="state">正在读取文章…</div>
        <div v-else-if="articles.length === 0" class="state">暂无文章</div>
        <button
          v-for="item in articles"
          :key="item.id"
          class="article-item"
          :class="{ active: selected?.id === item.id }"
          type="button"
          @click="selectArticle(item)"
        >
          <span class="item-title">{{ item.title }}</span>
          <span class="item-meta">
            <span>{{ formatDate(item.created_at) }}</span>
            <span>{{ item.author }}</span>
          </span>
        </button>
      </div>
    </aside>

    <section class="reader">
      <div v-if="selected" class="reader-shell">
        <div class="reader-head">
          <div class="reader-kicker">
            <span class="tag">文章</span>
            <time>{{ formatDate(selected.created_at) }}</time>
            <span>作者：{{ selected.author }}</span>
          </div>
          <h1>{{ selected.title }}</h1>
        </div>
        <div ref="readerScroll" class="reader-scroll">
          <ArticleContent
            v-if="selected.content.trim()"
            :content="selected.content"
          />
          <div v-else class="state">这篇文章暂无内容</div>
        </div>
      </div>

      <div v-else class="reader-empty">
        <div class="empty-mark">[ 知识 ]</div>
        <h2>选择一篇文章开始阅读</h2>
        <p>管理员发布的知识文章会显示在左侧目录。</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { articlesApi, type Article } from '../api/articles'
import ArticleContent from '../components/ArticleContent.vue'
import { parseServerDate } from '../utils/datetime'

const articles = ref<Article[]>([])
const selected = ref<Article | null>(null)
const loading = ref(true)
const readerScroll = ref<HTMLElement | null>(null)

function formatDate(value: string) {
  const date = parseServerDate(value)
  const day = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  const time = `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  return `${day} ${time}`
}

async function selectArticle(item: Article) {
  selected.value = item
  await nextTick()
  if (readerScroll.value) readerScroll.value.scrollTop = 0
}

onMounted(async () => {
  try {
    articles.value = await articlesApi.list('article')
  } catch {
    articles.value = []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.knowledge {
  display: grid;
  grid-template-columns: minmax(260px, 320px) minmax(0, 1fr);
  gap: 16px;
  height: calc(100dvh - 148px);
  min-height: 520px;
}
.catalog,
.reader {
  min-height: 0;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel-translucent);
}
.catalog {
  display: flex;
  flex-direction: column;
}
.catalog-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
  padding: 16px;
  border-bottom: 1px solid var(--line);
}
.kicker {
  margin-bottom: 4px;
  color: var(--dim);
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 1px;
}
.catalog-head h1 {
  color: var(--text-strong);
  font-size: 22px;
  line-height: 1.2;
}
.count {
  flex-shrink: 0;
  color: var(--amber);
  font-family: var(--mono);
  font-size: 11px;
}
.catalog-scroll,
.reader-scroll {
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-width: thin;
  scrollbar-color: var(--line2) transparent;
}
.catalog-scroll {
  flex: 1;
}
.catalog-scroll::-webkit-scrollbar,
.reader-scroll::-webkit-scrollbar {
  width: 7px;
}
.catalog-scroll::-webkit-scrollbar-thumb,
.reader-scroll::-webkit-scrollbar-thumb {
  border-radius: 4px;
  background: var(--line2);
}
.catalog-scroll::-webkit-scrollbar-thumb:hover,
.reader-scroll::-webkit-scrollbar-thumb:hover {
  background: var(--green);
}
.article-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  padding: 14px 16px;
  border: 0;
  border-bottom: 1px dashed var(--line);
  border-left: 2px solid transparent;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.article-item:hover {
  background: rgba(var(--green-rgb), 0.04);
}
.article-item.active {
  border-left-color: var(--green);
  background: rgba(var(--green-rgb), 0.07);
}
.item-title {
  color: var(--text-strong);
  font-size: 14px;
  font-weight: 700;
  line-height: 1.45;
  overflow-wrap: anywhere;
}
.article-item.active .item-title {
  color: var(--green);
}
.item-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--dim);
  font-family: var(--mono);
  font-size: 10px;
}
.reader {
  display: flex;
  flex-direction: column;
}
.reader-shell {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
}
.reader-head {
  flex-shrink: 0;
  padding: 22px 28px 20px;
  border-bottom: 1px solid var(--line);
}
.reader-kicker {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
  color: var(--dim);
  font-family: var(--mono);
  font-size: 11px;
}
.reader-kicker .tag {
  padding: 1px 8px;
  border: 1px solid rgba(var(--cyan-rgb), 0.4);
  border-radius: 4px;
  color: var(--cyan);
  font-family: var(--sans);
  font-weight: 700;
}
.reader-head h1 {
  color: var(--text-strong);
  font-size: 28px;
  line-height: 1.4;
  overflow-wrap: anywhere;
}
.reader-scroll {
  flex: 1;
  padding: 24px 28px 38px;
}
.reader-empty {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  text-align: center;
}
.empty-mark {
  margin-bottom: 14px;
  color: var(--green);
  font-family: var(--mono);
  font-size: 13px;
  letter-spacing: 2px;
  opacity: 0.72;
}
.reader-empty h2 {
  margin-bottom: 7px;
  color: var(--text-strong);
  font-size: 19px;
}
.reader-empty p {
  color: var(--dim);
  font-size: 12px;
}
.state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 160px;
  padding: 24px;
  color: var(--dim);
  font-size: 13px;
}
@media (max-width: 820px) {
  .knowledge {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(210px, 36%) minmax(0, 1fr);
    height: calc(100dvh - 150px);
    min-height: 620px;
  }
  .catalog-head {
    padding: 13px 16px;
  }
  .reader-head {
    padding: 18px 18px 16px;
  }
  .reader-head h1 {
    font-size: 22px;
  }
  .reader-scroll {
    padding: 20px 18px 30px;
  }
}
</style>
