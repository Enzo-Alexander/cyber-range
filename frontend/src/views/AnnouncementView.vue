<template>
  <div class="announcements">
    <div class="page-head">
      <div>
        <div class="page-title">公告</div>
        <div class="page-sub">平台通知与重要更新</div>
      </div>
      <div class="notice-count">
        <span class="signal"></span>
        <span>{{ loading ? '--' : announcements.length }}</span> 条公告
      </div>
    </div>

    <div v-if="loading" class="state">正在读取公告<span class="ellipsis">...</span></div>

    <div v-else-if="announcements.length === 0" class="empty-state">
      <div class="empty-mark">[ ]</div>
      <p>暂无公告</p>
      <span>管理员发布的通知会显示在这里</span>
    </div>

    <div v-else class="notice-panel">
      <div class="panel-head">
        <span class="ok">◈ 系统公告</span>
        <span class="dim">按发布时间倒序</span>
      </div>
      <div class="notice-list">
        <router-link
          v-for="item in announcements"
          :key="item.id"
          :to="`/article/${item.id}`"
          class="notice-item"
        >
          <div class="notice-main">
            <h2 class="notice-title">{{ item.title }}</h2>
            <time class="notice-time" :datetime="item.created_at">{{ formatDate(item.created_at) }}</time>
          </div>
          <span class="notice-arrow">→</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { articlesApi, type Article } from '../api/articles'
import { parseServerDate } from '../utils/datetime'

const announcements = ref<Article[]>([])
const loading = ref(true)

function formatDate(s: string) {
  const d = parseServerDate(s)
  const date = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  const time = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  return `${date} ${time}`
}

onMounted(async () => {
  try {
    announcements.value = await articlesApi.list('announcement')
  } catch {
    announcements.value = []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.announcements {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.page-head .page-sub {
  margin-bottom: 0;
}
.notice-count {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-shrink: 0;
  padding: 6px 11px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel-translucent);
  font-family: var(--mono);
  font-size: 12px;
  color: var(--muted);
}
.signal {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--red);
  box-shadow: 0 0 8px rgba(var(--red-rgb), 0.75);
}
.notice-panel {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel-translucent);
  overflow: hidden;
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
  font-family: var(--mono);
  font-size: 13px;
}
.panel-head .ok {
  color: var(--green);
}
.panel-head .dim {
  color: var(--dim);
}
.notice-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 24px;
  align-items: center;
  gap: 20px;
  padding: 20px 22px;
  border-bottom: 1px dashed var(--line);
  color: inherit;
  text-decoration: none;
  transition: background 0.15s;
}
.notice-item:last-child {
  border-bottom: none;
}
.notice-item:hover {
  background: rgba(var(--red-rgb), 0.035);
}
.notice-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  min-width: 0;
}
.notice-title {
  color: var(--text-strong);
  font-size: 19px;
  font-weight: 800;
  line-height: 1.45;
  overflow-wrap: anywhere;
}
.notice-time {
  flex-shrink: 0;
  color: var(--amber);
  font-family: var(--mono);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0;
  white-space: nowrap;
  text-shadow: 0 0 10px rgba(var(--amber-rgb), 0.28);
}
.notice-arrow {
  color: var(--dim);
  font-size: 18px;
  transition: color 0.15s, transform 0.15s;
}
.notice-item:hover .notice-arrow {
  color: var(--red);
  transform: translateX(3px);
}
.state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel-soft);
  color: var(--muted);
  font-size: 14px;
}
.state {
  font-family: var(--mono);
}
.ellipsis {
  color: var(--green);
}
.empty-mark {
  margin-bottom: 12px;
  color: var(--dim);
  font-family: var(--mono);
  font-size: 24px;
  letter-spacing: 4px;
}
.empty-state p {
  margin-bottom: 5px;
  color: var(--text);
}
.empty-state span {
  color: var(--dim);
  font-size: 12px;
}
@media (max-width: 820px) {
  .notice-item {
    grid-template-columns: minmax(0, 1fr) 20px;
    gap: 10px;
    padding: 16px;
  }
  .notice-main {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
@media (max-width: 620px) {
  .page-head {
    flex-direction: column;
    gap: 10px;
  }
  .notice-count {
    align-self: flex-start;
  }
  .panel-head .dim {
    display: none;
  }
}
</style>
