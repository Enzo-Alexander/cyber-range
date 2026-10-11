<template>
  <div class="profile">
    <!-- 左侧用户信息卡 -->
    <aside class="p-left">
      <div class="u-card">
        <div class="avatar">{{ (p?.user.username || '?')[0].toUpperCase() }}</div>
        <div class="name">{{ p?.user.username }}</div>
        <div class="lv">LV{{ level }}</div>
        <div class="mail">{{ p?.user.email }}</div>
        <div class="role" :class="p?.user.role">{{ p?.user.role === 'admin' ? '管理员' : '选手' }}</div>

        <div class="stat-row">
          <div class="st">
            <div class="v">{{ p?.total_points ?? 0 }}</div>
            <div class="k">总分</div>
          </div>
          <div class="st">
            <div class="v">{{ p?.total_solved ?? 0 }}</div>
            <div class="k">已解</div>
          </div>
          <div class="st">
            <div class="v">{{ p?.rank ?? '--' }}</div>
            <div class="k">排名</div>
          </div>
        </div>
      </div>

      <div class="menu">
        <button
          v-for="m in menu"
          :key="m.id"
          class="m-item"
          :class="{ active: view === m.id }"
          @click="view = m.id"
        >{{ m.label }}</button>
      </div>
    </aside>

    <!-- 右侧主区 -->
    <main class="p-main">
      <!-- 掌握度 -->
      <section v-if="view === 'progress'" class="panel">
        <div class="panel-t">掌握度进度</div>
        <div v-for="pr in p?.progress" :key="pr.category" class="bar-row">
          <span class="bk">{{ pr.category }}</span>
          <div class="bar">
            <div class="fill" :style="{ width: pr.percent + '%' }" />
          </div>
          <span class="bp">{{ pr.percent }}%</span>
        </div>
      </section>

      <!-- 解题记录 -->
      <section v-else-if="view === 'solves'" class="panel">
        <div class="panel-t">解题记录</div>
        <table class="tbl">
          <thead>
            <tr>
              <th>题目</th>
              <th>分类</th>
              <th>积分</th>
              <th>解题时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in p?.solves" :key="s.challenge_id + s.solved_at">
              <td>
                <router-link :to="`/challenge/${s.challenge_id}`" class="lt">{{ s.title }}</router-link>
              </td>
              <td><span class="ct">{{ s.category }}</span></td>
              <td class="pts">+{{ s.points }}</td>
              <td class="time">{{ fmt(s.solved_at) }}</td>
            </tr>
            <tr v-if="!p?.solves?.length">
              <td colspan="4" class="empty">还没有解题记录，去题目大厅试试吧</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section v-else class="panel">
        <div class="panel-t">{{ currentMenu?.label }}</div>
        <p class="ph">该模块将在后续阶段开放。</p>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { challengesApi, type Profile } from '../api/challenges'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const p = ref<Profile | null>(null)
const view = ref<string>('progress')

const menu = [
  { id: 'progress', label: '我的进度' },
  { id: 'solves', label: '解题记录' },
  { id: 'fav', label: '我的收藏' },
  { id: 'account', label: '账号设置' },
]
const currentMenu = computed(() => menu.find((m) => m.id === view.value))
const level = computed(() => Math.floor((p.value?.total_points ?? 0) / 1000) + 1)

function fmt(iso: string) {
  const d = new Date(iso)
  const p2 = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p2(d.getMonth() + 1)}-${p2(d.getDate())} ${p2(d.getHours())}:${p2(d.getMinutes())}`
}

onMounted(async () => {
  try {
    p.value = await challengesApi.profile()
  } catch {
    // 未登录由路由守卫拦截
  }
})
</script>

<style scoped>
.profile {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 20px;
  align-items: start;
}
.p-left { display: flex; flex-direction: column; gap: 14px; }
.u-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 22px 18px;
  text-align: center;
}
.avatar {
  width: 64px;
  height: 64px;
  margin: 0 auto 10px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 800;
  color: #06261a;
  background: linear-gradient(135deg, var(--green), var(--cyan));
  box-shadow: 0 0 20px rgba(0, 255, 159, 0.3);
}
.name { font-size: 20px; font-weight: 800; color: #eaf4ff; }
.lv {
  font-family: var(--mono);
  color: var(--amber);
  font-weight: 700;
  margin-top: 2px;
}
.mail { font-size: 12px; color: var(--muted); margin-top: 2px; }
.role {
  display: inline-block;
  margin-top: 8px;
  font-size: 12px;
  padding: 2px 12px;
  border-radius: 20px;
}
.role.admin { color: var(--red); border: 1px solid var(--red); }
.role.user { color: var(--cyan); border: 1px solid var(--cyan); }

.stat-row {
  display: flex;
  justify-content: space-around;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px dashed var(--line2);
}
.st .v {
  font-family: var(--mono);
  font-size: 20px;
  font-weight: 700;
  color: var(--green);
}
.st .k { font-size: 11px; color: var(--muted); }

.menu {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.m-item {
  text-align: left;
  padding: 10px 14px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--muted);
  font-size: 14px;
  cursor: pointer;
}
.m-item:hover { color: var(--text); }
.m-item.active { color: var(--green); background: rgba(0, 255, 159, 0.08); }

.p-main { display: flex; flex-direction: column; gap: 16px; }
.panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 22px 24px;
}
.panel-t { font-size: 16px; font-weight: 700; color: #eaf4ff; margin-bottom: 16px; }

.bar-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 12px;
}
.bk { width: 84px; font-size: 13px; color: var(--text); }
.bar {
  flex: 1;
  height: 10px;
  background: var(--panel2);
  border: 1px solid var(--line2);
  border-radius: 20px;
  overflow: hidden;
}
.fill {
  height: 100%;
  background: linear-gradient(90deg, var(--green), var(--cyan));
  border-radius: 20px;
  box-shadow: 0 0 10px rgba(0, 255, 159, 0.4);
  transition: width 0.5s ease;
}
.bp { width: 42px; text-align: right; font-family: var(--mono); color: var(--green); font-size: 13px; }

.tbl { width: 100%; border-collapse: collapse; }
.tbl th {
  text-align: left;
  font-size: 12px;
  color: var(--muted);
  padding: 10px 14px;
  border-bottom: 1px solid var(--line);
  background: var(--panel2);
}
.tbl td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--line);
  font-size: 14px;
  color: var(--text);
}
.tbl tr:last-child td { border-bottom: none; }
.lt { color: var(--cyan); }
.lt:hover { color: var(--green); }
.ct {
  font-size: 12px;
  color: var(--cyan);
  border: 1px solid rgba(0, 224, 255, 0.35);
  padding: 1px 8px;
  border-radius: 4px;
}
.pts { font-family: var(--mono); color: var(--green); font-weight: 700; }
.time { font-family: var(--mono); font-size: 12px; color: var(--muted); }
.empty { text-align: center; color: var(--muted); padding: 30px; }
.ph { color: var(--muted); font-size: 14px; }
</style>
