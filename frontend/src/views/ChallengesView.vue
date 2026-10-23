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
      <div class="head-actions">
        <button v-if="canSubmitChallenge" class="submit-trigger" @click="showSubmit = true">
          <span class="plus">+</span> 提交题目
        </button>
        <div class="search">
          <span class="s-ico">⌕</span>
          <input v-model="search" placeholder="搜索题目…" @input="onSearch" />
        </div>
      </div>
    </div>

    <!-- 分类标签 -->
    <div class="tabs">
      <button
        v-for="c in CATEGORIES"
        :key="c"
        class="tab"
        :class="{ active: viewMode === 'lobby' && active === c }"
        @click="pick(c)"
      >{{ c }}</button>
      <button
        class="tab comp-tab"
        :class="{ active: viewMode === 'competitions' }"
        @click="viewMode = 'competitions'"
      >🏆 比赛真题</button>
    </div>

    <!-- 比赛真题视图 -->
    <div v-if="viewMode === 'competitions'" class="comp-view">
      <!-- 比赛列表 -->
      <div v-if="!selectedComp && !selectedEdition" class="ch-grid">
        <div v-for="c in compList" :key="c.id" class="card comp-card" @click="selectedComp = c">
          <div class="c-head" style="justify-content:center"><span class="c-icon">{{ c.icon }}</span></div>
          <div class="c-title" style="text-align:center">{{ c.name }}</div>
          <p class="c-desc" style="text-align:center">{{ c.description || '暂无描述' }}</p>
        </div>
      </div>

      <!-- 届次列表 -->
      <div v-else-if="!selectedEdition" class="edition-view">
        <div class="back" @click="selectedComp = null">← 返回比赛列表</div>
        <h2 class="edition-title">{{ selectedComp?.icon }} {{ selectedComp?.name }}</h2>
        <div class="ch-grid">
          <div v-for="e in editionList" :key="e.id" class="card comp-card" @click="selectedEdition = e">
            <div class="c-head" style="justify-content:center"><span class="c-icon">📅</span></div>
            <div class="c-title" style="text-align:center">{{ e.name }}</div>
            <p class="c-desc" style="text-align:center">{{ e.year }} 年</p>
            <p class="comp-earned" :class="{ scored: e.my_points > 0 }">
              <span class="ce-label">已得分数：</span>
              <b>{{ e.my_points }}</b>
            </p>
          </div>
        </div>
      </div>

      <!-- 届次题目列表 -->
      <div v-else class="edition-view">
        <div class="back" @click="selectedEdition = null">← 返回届次列表</div>
        <h2 class="edition-title">{{ selectedComp?.icon }} {{ selectedComp?.name }} · {{ selectedEdition?.name }}</h2>
        <div class="ch-grid">
          <router-link
            v-for="ch in compChallenges"
            :key="ch.id"
            :to="`/comp-challenge/${ch.id}`"
            class="card comp-card"
            :class="{ 'comp-solved': ch.solved_by_me }"
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
        </div>
      </div>
    </div>

    <!-- 题目卡片网格 -->
    <div v-if="viewMode === 'lobby'" class="ch-grid">
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
    <div class="pager" v-if="viewMode === 'lobby' && !loading && list.length > 0">
      <button class="pg" :disabled="page === 1" @click="page--">← 上一页</button>
      <span class="pg-info">第 {{ page }} / {{ totalPages }} 页 · 共 {{ total }} 题</span>
      <button class="pg" :disabled="page === totalPages" @click="page++">下一页 →</button>
    </div>

    <SubmitChallengeModal v-if="showSubmit" @close="showSubmit = false" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { CATEGORIES, challengesApi, type ChallengeCard } from '../api/challenges'
import { competitionsApi, type Competition, type CompetitionEdition, type CompetitionChallenge } from '../api/competitions'
import SubmitChallengeModal from '../components/SubmitChallengeModal.vue'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const auth = useAuthStore()
const list = ref<ChallengeCard[]>([])
const total = ref(0)
const queryCat = typeof route.query.category === 'string' ? route.query.category : ''
const active = ref(CATEGORIES.includes(queryCat) ? queryCat : '全部')
const search = ref('')
const loading = ref(true)
const showSubmit = ref(false)
const canSubmitChallenge = computed(
  () => auth.isAuthenticated && auth.user?.role !== 'admin',
)

// 比赛真题视图
const viewMode = ref<'lobby' | 'competitions'>('lobby')
const compList = ref<Competition[]>([])
const selectedComp = ref<Competition | null>(null)
const editionList = ref<CompetitionEdition[]>([])
const selectedEdition = ref<CompetitionEdition | null>(null)
const compChallenges = ref<CompetitionChallenge[]>([])

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
  viewMode.value = 'lobby'
  load()
}

let searchTimer: ReturnType<typeof setTimeout> | undefined
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 250)
}

async function loadCompetitions() {
  compList.value = await competitionsApi.list()
}

watch(selectedComp, async (c) => {
  if (c) {
    editionList.value = await competitionsApi.editions(c.id)
  } else {
    editionList.value = []
    selectedEdition.value = null
  }
})

watch(selectedEdition, async (e) => {
  if (e) {
    compChallenges.value = await competitionsApi.editionChallenges(e.id)
  } else {
    compChallenges.value = []
  }
})

/** 从比赛题目详情页返回时，按 URL 参数恢复到原来的比赛 / 届次 */
async function restoreCompFromQuery() {
  if (route.query.tab !== 'competitions') return
  viewMode.value = 'competitions'
  if (!compList.value.length) await loadCompetitions()
  const target = compList.value.find((c) => c.id === Number(route.query.comp))
  if (!target) return
  selectedComp.value = target
  const editions = await competitionsApi.editions(target.id)
  editionList.value = editions
  const edition = editions.find((e) => e.id === Number(route.query.edition))
  if (edition) {
    selectedEdition.value = edition
    compChallenges.value = await competitionsApi.editionChallenges(edition.id)
  }
}

onMounted(async () => {
  load()
  await loadCompetitions()
  await restoreCompFromQuery()
})
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
  background: var(--panel-translucent);
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
.head-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.submit-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border: 1px solid rgba(var(--green-rgb), 0.45);
  border-radius: 6px;
  background: rgba(var(--green-rgb), 0.06);
  color: var(--green);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: 0.15s;
}
.submit-trigger:hover {
  border-color: var(--green);
  background: rgba(var(--green-rgb), 0.12);
  box-shadow: 0 0 12px rgba(var(--green-rgb), 0.12);
}
.submit-trigger .plus {
  font-family: var(--mono);
  font-size: 16px;
  line-height: 1;
}
.page-title {
  font-size: 26px;
  font-weight: 800;
  color: var(--text-strong);
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
  color: var(--on-accent);
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
  border-color: var(--card-hover-border);
  background: var(--card-hover-bg);
  box-shadow: var(--card-hover-shadow);
  transform: var(--card-hover-transform);
}
.card.solved {
  border-color: rgba(var(--green-rgb), 0.55);
  background: linear-gradient(180deg, rgba(var(--green-rgb), 0.07), var(--panel));
  box-shadow: 0 0 14px rgba(var(--green-rgb), 0.12);
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
  color: var(--on-accent);
  background: var(--green);
  border-radius: 4px;
  padding: 2px 7px;
  box-shadow: 0 0 10px rgba(var(--green-rgb), 0.8);
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
  color: var(--on-accent);
  box-shadow: 0 0 10px rgba(var(--green-rgb), 0.8), 0 0 4px rgba(var(--green-rgb), 0.6);
}
.c-pts {
  font-family: var(--mono);
  font-size: 20px;
  font-weight: 700;
  color: var(--green);
  text-shadow: 0 0 10px rgba(var(--green-rgb), 0.35);
}
.c-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-strong);
  line-height: 1.3;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.c-tag {
  align-self: flex-start;
  font-size: 12px;
  color: var(--cyan);
  border: 1px solid rgba(var(--cyan-rgb), 0.4);
  padding: 1px 8px;
  border-radius: 4px;
}
.c-stars { color: var(--dim); font-size: 12px; letter-spacing: 1px; }
.c-stars .st.on { color: var(--amber); text-shadow: 0 0 6px rgba(var(--amber-rgb), 0.5); }
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

/* 比赛真题视图 */
.comp-tab { border-color: rgba(255, 193, 7, 0.4); color: var(--amber); }
.comp-tab.active { background: rgba(255, 193, 7, 0.15); border-color: var(--amber); color: var(--amber); }
.comp-card { cursor: pointer; padding: 16px 16px 14px; min-height: 120px; }
.comp-card:hover { border-color: var(--amber); box-shadow: 0 0 16px rgba(255, 193, 7, 0.1); }
/* 比赛题目解出后用琥珀色标记（与比赛板块的黄色边框一致，而不是题库的绿色） */
.comp-card.comp-solved {
  border-color: rgba(var(--amber-rgb), 0.65);
  background: linear-gradient(180deg, rgba(var(--amber-rgb), 0.09), var(--panel));
  box-shadow: 0 0 14px rgba(var(--amber-rgb), 0.14);
}
.comp-card.comp-solved:hover {
  border-color: var(--amber);
  box-shadow: 0 0 18px rgba(var(--amber-rgb), 0.22);
}
.comp-card .c-state.done {
  border-color: var(--amber);
  background: var(--amber);
  color: var(--on-amber);
  box-shadow: 0 0 10px rgba(var(--amber-rgb), 0.8), 0 0 4px rgba(var(--amber-rgb), 0.6);
}
.comp-card .solved-badge {
  color: var(--on-amber);
  background: var(--amber);
  box-shadow: 0 0 10px rgba(var(--amber-rgb), 0.8);
}
.comp-card:hover .go { color: var(--amber); }
/* 届次卡片：该届已得分数 */
.comp-earned {
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px dashed var(--line);
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 6px;
}
.comp-earned .ce-label {
  font-size: 12px;
  color: var(--dim);
  letter-spacing: 1px;
}
.comp-earned b {
  font-family: var(--mono);
  font-size: 30px;
  font-weight: 800;
  line-height: 1;
  color: var(--muted);
  transition: color 0.2s;
}
/* 有得分时才点亮：琥珀色 + 呼吸光晕，和比赛板块的黄色调一致 */
.comp-earned.scored b {
  color: var(--amber);
  animation: scorePulse 2.4s ease-in-out infinite;
}
@keyframes scorePulse {
  0%,
  100% {
    text-shadow: 0 0 8px rgba(var(--amber-rgb), 0.35), 0 0 18px rgba(var(--amber-rgb), 0.15);
  }
  50% {
    text-shadow: 0 0 16px rgba(var(--amber-rgb), 0.8), 0 0 34px rgba(var(--amber-rgb), 0.4);
  }
}
.c-icon { font-size: 28px; }
.c-desc {
  font-size: 13px;
  color: var(--muted);
  /* 与上方比赛名称拉开距离（.card 的 gap 之外再加一段间距） */
  margin-top: 16px;
  line-height: 1.4;
  /* 卡片尺寸固定不变：简介占据剩余空间，过长时在卡片内滚动，内容仍可完整查看 */
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  /* 长串（无空格的英文/链接）也不会撑破卡片 */
  overflow-wrap: anywhere;
  word-break: break-word;
  scrollbar-width: thin;
  scrollbar-color: var(--line2) transparent;
}
.c-desc::-webkit-scrollbar { width: 6px; }
.c-desc::-webkit-scrollbar-thumb { background: var(--line2); border-radius: 3px; }
.c-desc::-webkit-scrollbar-thumb:hover { background: var(--green); }
.edition-view { display: flex; flex-direction: column; gap: 16px; }
.back {
  font-family: var(--mono);
  font-size: 14px;
  color: var(--cyan);
  cursor: pointer;
  width: fit-content;
}
.back:hover { color: var(--green); }
.edition-title {
  font-size: 22px;
  color: var(--text-strong);
  margin: 0;
}
@media (max-width: 820px) {
  .head {
    align-items: flex-start;
    flex-direction: column;
  }
  .head-actions {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
