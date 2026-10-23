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

        <div class="level-box">
          <div class="level-line">
            <span>等级进度</span>
            <span>{{ p?.level_progress ?? 0 }} / {{ p?.level_required ?? 5 }}</span>
          </div>
          <div class="level-track">
            <div class="level-fill" :style="{ width: levelPercent + '%' }" />
          </div>
          <div class="level-next">距 LV{{ level + 1 }} 还差 {{ levelRemaining }} 题</div>
        </div>

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

      <!-- 我的收藏 -->
      <section v-else-if="view === 'fav'" class="panel">
        <div class="panel-t">我的收藏 <span class="fav-count">{{ favorites.length }}</span></div>
        <table class="tbl">
          <thead>
            <tr>
              <th>题目</th>
              <th>分类</th>
              <th>难度</th>
              <th>积分</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in favorites" :key="item.id">
              <td>
                <router-link :to="`/challenge/${item.id}`" class="lt">{{ item.title }}</router-link>
              </td>
              <td><span class="ct">{{ item.category }}</span></td>
              <td class="stars">{{ '★'.repeat(item.difficulty) }}</td>
              <td class="pts">+{{ item.points }}</td>
              <td>
                <span class="fav-state" :class="{ done: item.solved_by_me }">
                  {{ item.solved_by_me ? '已解' : '未解' }}
                </span>
              </td>
              <td>
                <button
                  class="unfav"
                  :disabled="favBusyId === item.id"
                  @click="removeFavorite(item.id)"
                >{{ favBusyId === item.id ? '处理中…' : '取消收藏' }}</button>
              </td>
            </tr>
            <tr v-if="!favLoading && favorites.length === 0">
              <td colspan="6" class="empty">还没有收藏题目，去题目大厅看看吧</td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- 账号设置 -->
      <section v-else-if="view === 'account'" class="panel">
        <div class="panel-t">账号设置</div>
        <div class="account-grid">
          <form class="account-form" @submit.prevent="saveEmail">
            <h3>基础信息</h3>
            <label>用户名
              <input :value="p?.user.username" disabled />
            </label>
            <label>邮箱
              <input v-model.trim="accountEmail" type="email" autocomplete="email" />
            </label>
            <p class="form-hint">用户名暂不可修改</p>
            <p v-if="accountMsg" class="form-msg" :class="accountMsgOk ? 'ok' : 'err'">
              {{ accountMsg }}
            </p>
            <button
              class="btn primary save-btn"
              type="submit"
              :disabled="accountSaving || !accountEmail || accountEmail === p?.user.email"
            >{{ accountSaving ? '保存中…' : '保存邮箱' }}</button>
          </form>

          <form class="account-form" @submit.prevent="savePassword">
            <h3>修改密码</h3>
            <label>当前密码
              <input
                v-model="currentPassword"
                type="password"
                autocomplete="current-password"
              />
            </label>
            <label>新密码
              <input
                v-model="newPassword"
                type="password"
                autocomplete="new-password"
                placeholder="至少 6 位"
              />
            </label>
            <label>确认新密码
              <input
                v-model="confirmPassword"
                type="password"
                autocomplete="new-password"
              />
            </label>
            <p v-if="passwordMsg" class="form-msg" :class="passwordMsgOk ? 'ok' : 'err'">
              {{ passwordMsg }}
            </p>
            <button
              class="btn primary save-btn"
              type="submit"
              :disabled="passwordSaving || !currentPassword || !newPassword || !confirmPassword"
            >{{ passwordSaving ? '更新中…' : '更新密码' }}</button>
          </form>
        </div>
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
import { challengesApi, type FavoriteChallenge, type Profile } from '../api/challenges'
import { usersApi } from '../api/users'
import { useAuthStore } from '../stores/auth'
import { parseServerDate } from '../utils/datetime'

const auth = useAuthStore()
const p = ref<Profile | null>(null)
const view = ref<string>('progress')
const favorites = ref<FavoriteChallenge[]>([])
const favLoading = ref(true)
const favBusyId = ref<number | null>(null)
const accountEmail = ref('')
const accountSaving = ref(false)
const accountMsg = ref('')
const accountMsgOk = ref(false)
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordSaving = ref(false)
const passwordMsg = ref('')
const passwordMsgOk = ref(false)

const menu = [
  { id: 'progress', label: '我的进度' },
  { id: 'solves', label: '解题记录' },
  { id: 'fav', label: '我的收藏' },
  { id: 'account', label: '账号设置' },
]
const currentMenu = computed(() => menu.find((m) => m.id === view.value))
const level = computed(() => p.value?.level ?? 1)
const levelPercent = computed(() => {
  const required = p.value?.level_required ?? 5
  const progress = p.value?.level_progress ?? 0
  return required > 0 ? Math.round((progress / required) * 100) : 0
})
const levelRemaining = computed(() => {
  const required = p.value?.level_required ?? 5
  const progress = p.value?.level_progress ?? 0
  return Math.max(0, required - progress)
})

function fmt(iso: string) {
  const d = parseServerDate(iso)
  const p2 = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p2(d.getMonth() + 1)}-${p2(d.getDate())} ${p2(d.getHours())}:${p2(d.getMinutes())}`
}

async function removeFavorite(id: number) {
  if (favBusyId.value !== null) return
  favBusyId.value = id
  try {
    const res = await challengesApi.toggleFavorite(id)
    if (!res.favorited) {
      favorites.value = favorites.value.filter((item) => item.id !== id)
    }
  } catch (e) {
    alert((e as Error).message)
  } finally {
    favBusyId.value = null
  }
}

async function loadProfile() {
  try {
    p.value = await challengesApi.profile()
    accountEmail.value = p.value.user.email
  } catch {
    // 未登录由路由守卫拦截
  }
}

async function saveEmail() {
  if (!p.value || !accountEmail.value || accountEmail.value === p.value.user.email) return
  accountSaving.value = true
  accountMsg.value = ''
  try {
    const updated = await usersApi.updateAccount(accountEmail.value)
    p.value.user.email = updated.email
    accountEmail.value = updated.email
    await auth.fetchMe()
    accountMsgOk.value = true
    accountMsg.value = '邮箱已更新'
  } catch (e) {
    accountMsgOk.value = false
    accountMsg.value = (e as Error).message
  } finally {
    accountSaving.value = false
  }
}

async function savePassword() {
  passwordMsg.value = ''
  if (newPassword.value.length < 6) {
    passwordMsgOk.value = false
    passwordMsg.value = '新密码至少需要 6 位'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    passwordMsgOk.value = false
    passwordMsg.value = '两次输入的新密码不一致'
    return
  }
  passwordSaving.value = true
  try {
    await usersApi.changePassword(currentPassword.value, newPassword.value)
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    passwordMsgOk.value = true
    passwordMsg.value = '密码已更新'
  } catch (e) {
    passwordMsgOk.value = false
    passwordMsg.value = (e as Error).message
  } finally {
    passwordSaving.value = false
  }
}

onMounted(async () => {
  await loadProfile()
  try {
    favorites.value = await challengesApi.favorites()
  } catch {
    favorites.value = []
  } finally {
    favLoading.value = false
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
  color: var(--on-accent);
  background: linear-gradient(135deg, var(--green), var(--cyan));
  box-shadow: 0 0 20px rgba(var(--green-rgb), 0.3);
}
.name { font-size: 20px; font-weight: 800; color: var(--text-strong); }
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

.level-box {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed var(--line2);
  text-align: left;
}
.level-line {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--muted);
  font-size: 10px;
}
.level-line span:last-child {
  color: var(--amber);
  font-family: var(--mono);
}
.level-track {
  height: 7px;
  margin-top: 6px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel2);
}
.level-fill {
  height: 100%;
  border-radius: 8px;
  background: linear-gradient(90deg, var(--green), var(--cyan));
  transition: width 0.4s ease;
}
.level-next {
  margin-top: 6px;
  color: var(--dim);
  font-size: 10px;
}

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
.m-item.active { color: var(--green); background: rgba(var(--green-rgb), 0.08); }

.p-main { display: flex; flex-direction: column; gap: 16px; }
.panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 22px 24px;
}
.panel-t { font-size: 16px; font-weight: 700; color: var(--text-strong); margin-bottom: 16px; }
.fav-count {
  margin-left: 7px;
  color: var(--amber);
  font-family: var(--mono);
  font-size: 12px;
}

.account-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 28px;
}
.account-form {
  display: flex;
  flex-direction: column;
  gap: 13px;
}
.account-form h3 {
  color: var(--text-strong);
  font-size: 14px;
  font-weight: 700;
}
.account-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--muted);
  font-size: 12px;
}
.account-form input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--line2);
  border-radius: 6px;
  outline: none;
  background: var(--field-bg);
  color: var(--text);
  font-size: 14px;
}
.account-form input:focus {
  border-color: var(--green);
}
.account-form input:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}
.form-hint {
  color: var(--dim);
  font-size: 11px;
}
.form-msg {
  font-size: 12px;
}
.form-msg.ok { color: var(--green); }
.form-msg.err { color: var(--red); }
.save-btn {
  align-self: flex-start;
  margin-top: 2px;
}
.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

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
  box-shadow: 0 0 10px rgba(var(--green-rgb), 0.4);
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
  border: 1px solid rgba(var(--cyan-rgb), 0.35);
  padding: 1px 8px;
  border-radius: 4px;
}
.pts { font-family: var(--mono); color: var(--green); font-weight: 700; }
.time { font-family: var(--mono); font-size: 12px; color: var(--muted); }
.stars { color: var(--amber); font-size: 12px; letter-spacing: 1px; }
.fav-state {
  color: var(--muted);
  font-size: 12px;
}
.fav-state.done {
  color: var(--green);
}
.unfav {
  padding: 3px 9px;
  border: 1px solid var(--line2);
  border-radius: 4px;
  background: transparent;
  color: var(--muted);
  font-size: 12px;
  cursor: pointer;
}
.unfav:hover:not(:disabled) {
  border-color: var(--amber);
  color: var(--amber);
}
.unfav:disabled {
  opacity: 0.5;
  cursor: wait;
}
.empty { text-align: center; color: var(--muted); padding: 30px; }
.ph { color: var(--muted); font-size: 14px; }
@media (max-width: 900px) {
  .account-grid {
    grid-template-columns: 1fr;
    gap: 22px;
  }
}
</style>
