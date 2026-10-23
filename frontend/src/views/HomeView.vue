<template>
  <div>
    <div class="page-title">总览</div>
    <div class="page-sub">网络安全实战靶场与流量分析学习平台</div>

    <div class="grid g3" style="margin-bottom: 24px">
      <div class="card">
        <div class="t"><span style="color: var(--green)">◈</span>题目总数</div>
        <div class="stat-num">{{ totalCount }}</div>
        <p>多题型可练习</p>
      </div>
      <div class="card solved-card">
        <div class="t"><span style="color: var(--cyan)">◈</span>已解出</div>
        <div class="solved-split">
          <div>
            <div class="stat-num">{{ auth.isAuthenticated ? solvedCount : '--' }}</div>
            <p>题库已解出</p>
          </div>
          <div>
            <div class="stat-num competition">{{ auth.isAuthenticated ? competitionSolved : '--' }}</div>
            <p>比赛已解出</p>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="t"><span style="color: var(--amber)">◈</span>我的排名</div>
        <div class="stat-num">{{ auth.isAuthenticated ? '#' + myRank : '--' }}</div>
        <p>总榜</p>
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

    <div class="card year-activity">
      <div class="year-head">
        <div class="t"><span style="color: var(--green)">◈</span>全年做题活跃</div>
        <div class="year-nav">
          <button class="year-btn" title="上一年" @click="changeYear(-1)">‹</button>
          <span class="year-label">{{ activityYear }} 年</span>
          <button
            class="year-btn"
            title="下一年"
            :disabled="!canGoNextYear"
            @click="changeYear(1)"
          >›</button>
        </div>
      </div>

      <div v-if="auth.isAuthenticated" class="year-grid" :class="{ loading: activityLoading }">
        <div v-for="month in monthBlocks" :key="month.month" class="month-block">
          <div class="month-name">{{ month.month }} 月</div>
          <div class="month-grid">
            <div
              v-for="(cell, index) in month.cells"
              :key="index"
              class="day-cell"
              :class="[`level-${cell.level}`, { blank: !cell.day }]"
              :title="cell.day ? `${activityYear}-${String(month.month).padStart(2, '0')}-${String(cell.day).padStart(2, '0')}：${cell.count} 题` : ''"
            ></div>
          </div>
        </div>
      </div>
      <div v-else class="year-login">登录后查看年度做题记录</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { challengesApi, type YearlyActivity } from '../api/challenges'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

const totalCount = ref(0)
const solvedCount = ref(0)
const competitionSolved = ref(0)
const myRank = ref<number | string>('-')
const today = new Date()
const activityYear = ref(today.getFullYear())
const activity = ref<YearlyActivity | null>(null)
const activityLoading = ref(false)

const monthBlocks = computed(() => {
  const year = activityYear.value
  return Array.from({ length: 12 }, (_, index) => {
    const month = index + 1
    const source = activity.value?.months.find((item) => item.month === month)
    const totalDays = source?.days ?? new Date(year, month, 0).getDate()
    const counts = new Map(
      (source?.daily ?? []).map((item) => [item.day, item.count]),
    )
    const firstWeekday = (new Date(year, month - 1, 1).getDay() + 6) % 7
    const cells: { day: number | null; count: number; level: number }[] = []

    for (let leading = 0; leading < firstWeekday; leading++) {
      cells.push({ day: null, count: 0, level: 0 })
    }
    for (let day = 1; day <= totalDays; day++) {
      const count = counts.get(day) ?? 0
      const level = count === 0 ? 0 : count === 1 ? 1 : count === 2 ? 2 : count <= 4 ? 3 : 4
      cells.push({ day, count, level })
    }
    return { month, cells }
  })
})

const canGoNextYear = computed(() => activityYear.value < today.getFullYear())

const categories = [
  { name: '逆向工程', icon: '↩', desc: '分析二进制，还原程序逻辑' },
  { name: '二进制漏洞', icon: '⚠', desc: '栈溢出 / 堆利用 / ROP' },
  { name: '密码学', icon: '🔑', desc: '古典 / 现代密码，数学攻防' },
  { name: 'Web安全', icon: '🌐', desc: 'SQL注入 / XSS / 逻辑漏洞' },
  { name: '流量分析', icon: '⇄', desc: '报文拆解，学习网络协议' },
  { name: '数字取证', icon: '◆', desc: 'Misc / 隐写 / 取证' },
]

async function loadYearActivity() {
  if (!auth.isAuthenticated) {
    activity.value = null
    return
  }
  activityLoading.value = true
  try {
    activity.value = await challengesApi.yearlyActivity(activityYear.value)
  } catch {
    activity.value = null
  } finally {
    activityLoading.value = false
  }
}

function changeYear(delta: number) {
  activityYear.value += delta
  loadYearActivity()
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
      competitionSolved.value = p.competition_solved
      myRank.value = p.rank
    } catch {
      solvedCount.value = 0
      competitionSolved.value = 0
    }
    await loadYearActivity()
  }
})
</script>

<style scoped>
.solved-card {
  display: flex;
  flex-direction: column;
}
.solved-split {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
.solved-split .stat-num {
  line-height: 1.15;
}
.solved-split .stat-num.competition {
  color: var(--amber);
  text-shadow: 0 0 12px rgba(var(--amber-rgb), 0.28);
}
.year-activity {
  margin-top: 16px;
  padding: 22px 24px;
}
.year-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}
.year-head .t {
  margin-bottom: 0;
  white-space: nowrap;
}
.year-nav {
  display: flex;
  align-items: center;
  gap: 5px;
}
.year-btn {
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  padding: 0;
  border: 1px solid var(--line2);
  border-radius: 4px;
  background: transparent;
  color: var(--muted);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
}
.year-btn:hover:not(:disabled) {
  border-color: var(--green);
  color: var(--green);
}
.year-btn:disabled {
  opacity: 0.35;
  cursor: default;
}
.year-label {
  min-width: 52px;
  color: var(--muted);
  font-family: var(--mono);
  font-size: 12px;
  text-align: center;
  white-space: nowrap;
}
.year-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  column-gap: 12px;
  row-gap: 12px;
  transition: opacity 0.15s ease;
}
.year-grid.loading {
  opacity: 0.55;
}
.month-block {
  min-width: 0;
}
.month-name {
  margin-bottom: 6px;
  color: var(--muted);
  font-family: var(--mono);
  font-size: 10px;
  text-align: center;
  white-space: nowrap;
}
.month-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 2px;
}
.day-cell {
  aspect-ratio: 1;
  border-radius: 2px;
  background: var(--heat-0);
  transition: transform 0.12s ease;
}
.day-cell.blank {
  background: transparent;
}
.day-cell.level-1 { background: var(--heat-1); }
.day-cell.level-2 { background: var(--heat-2); }
.day-cell.level-3 { background: var(--heat-3); }
.day-cell.level-4 { background: var(--heat-4); }
.day-cell:not(.blank):hover {
  position: relative;
  z-index: 1;
  outline: 1px solid var(--text-strong);
  outline-offset: 1px;
  transform: scale(1.2);
}
.year-login {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 108px;
  color: var(--dim);
  font-size: 12px;
}
@media (max-width: 1100px) {
  .year-grid {
    grid-template-columns: repeat(6, minmax(0, 1fr));
    column-gap: 12px;
    row-gap: 16px;
  }
}
@media (max-width: 680px) {
  .year-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    column-gap: 14px;
    row-gap: 18px;
  }
  .year-head {
    align-items: flex-start;
  }
}
@media (max-width: 460px) {
  .year-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
