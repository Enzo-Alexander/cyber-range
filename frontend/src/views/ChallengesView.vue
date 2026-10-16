<template>
  <div class="lobby">
    <!-- 模式指示条 -->
    <div class="modebar">
      <span class="ok">mode: challenge lobby</span>
      <span class="dim">· {{ total }} tasks online</span>
      <span class="sep">|</span>
      <span class="dim">submit flag → earn points</span>
    </div>

    <!-- 标题 + 搜索 -->
    <div class="head">
      <h1 class="page-title">题目大厅</h1>
      <div class="search">
        <span class="s-ico">⌕</span>
        <input v-model="search" placeholder="搜索题目…" @input="onSearch" />
      </div>
    </div>

    <!-- 分类标签 -->
    <div class="tabs">
      <button
        v-for="c in CATEGORIES"
        :key="c"
        class="tab"
        :class="{ active: active === c }"
        @click="pick(c)"
      >{{ c }}</button>
    </div>

    <!-- 题目卡片网格 -->
    <div class="ch-grid">
      <router-link
        v-for="ch in pagedList"
        :key="ch.id"
        :to="`/challenge/${ch.id}`"
        class="card"
        :class="{ solved: ch.solved_by_me }"
      >
        <div class="c-head">
          <span class="c-state" :class="{ done: ch.solved_by_me }">
            {{ ch.solved_by_me ? '✓' : '' }}
          </span>
          <span class="c-pts">+{{ ch.points }}</span>
        </div>
        <div class="c-title-row">
          <span v-if="ch.solved_by_me" class="solved-badge">✓ 已解</span>
          <span class="c-title">{{ ch.title }}</span>
        </div>
        <span class="c-tag">{{ ch.category }}</span>
        <div class="c-stars" :title="'难度 ' + ch.difficulty + ' 星'">
          <i v-for="n in 5" :key="n" :class="['st', { on: n <= ch.difficulty }]">★</i>
        </div>
        <div class="c-foot">
          <span class="c-cnt">{{ ch.solved_count }} 已解</span>
          <span class="go">→</span>
        </div>
      </router-link>

      <div v-if="!loading && list.length === 0" class="empty">
        <p>暂无符合条件的题目</p>
        <p class="dim">换个分类或关键词试试</p>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pager" v-if="!loading && list.length > 0">
      <button class="pg" :disabled="page === 1" @click="page--">← 上一页</button>
      <span class="pg-info">第 {{ page }} / {{ totalPages }} 页 · 共 {{ total }} 题</span>
      <button class="pg" :disabled="page === totalPages" @click="page++">下一页 →</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { CATEGORIES, challengesApi, type ChallengeCard } from '../api/challenges'

const route = useRoute()
const list = ref<ChallengeCard[]>([])
const total = ref(0)
const queryCat = typeof route.query.category === 'string' ? route.query.category : ''
const active = ref(CATEGORIES.includes(queryCat) ? queryCat : '全部')
const search = ref('')
const loading = ref(true)

const PAGE_SIZE = 16
const page = ref(1)
const totalPages = computed(() => Math.max(1, Math.ceil(list.value.length / PAGE_SIZE)))
const pagedList = computed(() => list.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE))

async function load() {
  loading.value = true
  page.value = 1
  try {
    list.value = await challengesApi.list(active.value, search.value)
    total.value = list.value.length
  } finally {
    loading.value = false
  }
}

function pick(c: string) {
  active.value = c
  load()
}

let searchTimer: ReturnType<typeof setTimeout> | undefined
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 250)
}

onMounted(load)
</script>

<style scoped>
.lobby {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.modebar {
  font-family: var(--mono);
  font-size: 13px;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: rgba(16, 24, 35, 0.5);
  border: 1px solid var(--line);
  border-radius: 6px;
}
.modebar .ok { color: var(--green); }
.modebar .dim { color: var(--dim); }
.modebar .sep { color: var(--dim); opacity: 0.5; }

.head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}
.page-title {
  font-size: 26px;
  font-weight: 800;
  color: #eaf4ff;
}
.search {
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--line2);
  background: var(--panel);
  border-radius: 6px;
  padding: 6px 12px;
}
.s-ico { color: var(--dim); font-size: 16px; }
.search input {
  border: none;
  outline: none;
  background: transparent;
  color: var(--text);
  font-size: 14px;
  width: 180px;
}

.tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.tab {
  font-size: 14px;
  padding: 6px 16px;
  border: 1px solid var(--line2);
  background: var(--panel);
  color: var(--muted);
  border-radius: 20px;
  cursor: pointer;
  transition: 0.15s;
}
.tab:hover { color: var(--text); border-color: var(--green); }
.tab.active {
  color: #06261a;
  background: var(--green);
  border-color: var(--green);
  font-weight: 700;
}

.ch-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.card {
  aspect-ratio: 1 / 0.82;
  display: flex;
  flex-direction: column;
  gap: 9px;
  padding: 16px 18px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  color: var(--text);
  transition: 0.18s;
}
.card:hover {
  border-color: var(--green);
  box-shadow: 0 0 18px rgba(0, 255, 159, 0.16);
  transform: translateY(-3px);
}
.card.solved {
  border-color: rgba(0, 255, 159, 0.55);
  background: linear-gradient(180deg, rgba(0, 255, 159, 0.07), var(--panel));
  box-shadow: 0 0 14px rgba(0, 255, 159, 0.12);
}
.c-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}
.solved-badge {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 800;
  color: #06261a;
  background: var(--green);
  border-radius: 4px;
  padding: 2px 7px;
  box-shadow: 0 0 10px rgba(0, 255, 159, 0.8);
  letter-spacing: 0.5px;
}
.c-state {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid var(--dim);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 800;
  color: transparent;
  transition: 0.2s;
}
.c-state.done {
  border-color: var(--green);
  background: var(--green);
  color: #06261a;
  box-shadow: 0 0 10px rgba(0, 255, 159, 0.8), 0 0 4px rgba(0, 255, 159, 0.6);
}
.c-pts {
  font-family: var(--mono);
  font-size: 20px;
  font-weight: 700;
  color: var(--green);
  text-shadow: 0 0 10px rgba(0, 255, 159, 0.35);
}
.c-title {
  font-size: 17px;
  font-weight: 700;
  color: #eaf4ff;
  line-height: 1.45;
  flex: 1;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.c-tag {
  align-self: flex-start;
  font-size: 12px;
  color: var(--cyan);
  border: 1px solid rgba(0, 224, 255, 0.4);
  padding: 1px 8px;
  border-radius: 4px;
}
.c-stars { color: var(--dim); font-size: 12px; letter-spacing: 1px; }
.c-stars .st.on { color: var(--amber); text-shadow: 0 0 6px rgba(245, 166, 35, 0.5); }
.c-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px dashed var(--line);
  padding-top: 8px;
}
.c-cnt { font-size: 12px; color: var(--muted); }
.go { color: var(--dim); font-size: 16px; }
.card:hover .go { color: var(--green); }

.empty {
  text-align: center;
  padding: 60px 0;
  color: var(--muted);
  font-size: 14px;
}
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  padding: 16px 0 4px;
}
.pg {
  font-size: 13px;
  padding: 7px 18px;
  border: 1px solid var(--line2);
  background: var(--panel);
  color: var(--muted);
  border-radius: 6px;
  cursor: pointer;
  transition: 0.15s;
}
.pg:hover:not(:disabled) { border-color: var(--green); color: var(--green); }
.pg:disabled { opacity: 0.4; cursor: not-allowed; }
.pg-info {
  font-family: var(--mono);
  font-size: 13px;
  color: var(--muted);
}
</style>
