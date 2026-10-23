<template>
  <div class="board">
    <div class="modebar">
      <span class="ok">mode: leaderboard</span>
      <span class="dim">· global ranking</span>
    </div>

    <div class="head">
      <h1 class="page-title">排行榜</h1>
      <div class="toolbar">
        <div class="search">
          <span class="s-ico">⌕</span>
          <input v-model="keyword" placeholder="搜索选手…" />
        </div>
      </div>
    </div>

    <div class="table-wrap">
      <table class="tbl">
        <thead>
          <tr>
            <th>排名</th>
            <th>选手</th>
            <th>总分</th>
            <th>已解题目数</th>
            <th>最后解题时间</th>
            <th>近期动态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in shown" :key="row.username">
            <td class="rank">
              <span v-if="row.rank === 1" class="medal">🥇</span>
              <span v-else-if="row.rank === 2" class="medal">🥈</span>
              <span v-else-if="row.rank === 3" class="medal">🥉</span>
              <span v-else class="no">{{ row.rank }}</span>
            </td>
            <td class="player">
              <span class="avatar">{{ row.username[0].toUpperCase() }}</span>
              <span class="name">{{ row.username }}</span>
            </td>
            <td class="pts">{{ row.total_points }}</td>
            <td>{{ row.solved_count }}</td>
            <td class="time">{{ fmt(row.last_solved_at) }}</td>
            <td>
              <span class="chip">{{ row.solved_count > 0 ? '近期有解题' : '暂无动态' }}</span>
            </td>
          </tr>
          <tr v-if="!loading && shown.length === 0">
            <td colspan="6" class="empty">暂无排名数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { challengesApi, type LeaderboardEntry } from '../api/challenges'
import { parseServerDate } from '../utils/datetime'

const rows = ref<LeaderboardEntry[]>([])
const loading = ref(true)
const keyword = ref('')

const shown = computed(() => {
  let list = rows.value
  if (keyword.value.trim()) {
    const k = keyword.value.trim().toLowerCase()
    list = list.filter((r) => r.username.toLowerCase().includes(k))
  }
  return list
})

function fmt(iso: string | null): string {
  if (!iso) return '--'
  const d = parseServerDate(iso)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

onMounted(async () => {
  try {
    rows.value = await challengesApi.leaderboard()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.board { display: flex; flex-direction: column; gap: 16px; }
.modebar {
  font-family: var(--mono);
  font-size: 13px;
  color: var(--muted);
  padding: 8px 14px;
  background: var(--panel-translucent);
  border: 1px solid var(--line);
  border-radius: 6px;
}
.modebar .ok { color: var(--green); }
.modebar .dim { color: var(--dim); }
.head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.page-title { font-size: 26px; font-weight: 800; color: var(--text-strong); }
.toolbar { display: flex; align-items: center; gap: 12px; }
.search {
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--line2);
  background: var(--panel);
  border-radius: 6px;
  padding: 6px 12px;
}
.s-ico { color: var(--dim); }
.search input { border: none; outline: none; background: transparent; color: var(--text); width: 140px; font-size: 14px; }

.table-wrap {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
}
.tbl { width: 100%; border-collapse: collapse; }
.tbl th {
  text-align: left;
  font-size: 12px;
  color: var(--muted);
  padding: 12px 18px;
  border-bottom: 1px solid var(--line);
  letter-spacing: 1px;
  background: var(--panel2);
}
.tbl td {
  padding: 14px 18px;
  border-bottom: 1px solid var(--line);
  font-size: 14px;
  color: var(--text);
}
.tbl tr:last-child td { border-bottom: none; }
.tbl tr:hover td { background: rgba(var(--green-rgb), 0.03); }
.rank { width: 60px; font-family: var(--mono); }
.medal { font-size: 20px; }
.no { color: var(--muted); font-weight: 700; }
.player { display: flex; align-items: center; gap: 10px; }
.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: var(--on-accent);
  background: var(--cyan);
  font-size: 13px;
}
.name { font-weight: 600; }
.pts { font-family: var(--mono); font-weight: 700; color: var(--green); }
.time { font-family: var(--mono); font-size: 12px; color: var(--muted); }
.chip {
  font-size: 12px;
  color: var(--cyan);
  border: 1px solid rgba(var(--cyan-rgb), 0.35);
  padding: 2px 10px;
  border-radius: 20px;
}
.empty { text-align: center; color: var(--muted); padding: 40px; }
</style>
