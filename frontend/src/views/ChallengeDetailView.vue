<template>
  <div class="detail">
    <router-link to="/challenges" class="back">← 返回题目大厅</router-link>

    <div v-if="loading" class="loading">加载题目中…</div>

    <div v-else-if="ch" class="cols">
      <!-- 左主区 -->
      <div class="main">
        <div class="tagline">
          <span class="tag">{{ ch.category }}</span>
          <span class="status" :class="solved ? 'ok' : 'wait'">
            {{ solved ? '已解出' : '等待提交' }}
          </span>
        </div>
        <div class="title-row">
          <h1 class="title">{{ ch.title }}</h1>
          <div class="pts">+{{ ch.points }}</div>
        </div>

        <div class="glow">
          <div class="desc" v-html="rendered" />

          <div class="meta">
            <span class="mi">难度：<b>{{ '★'.repeat(ch.difficulty) }}</b></span>
            <span class="mi">作者：<b>{{ ch.author }}</b></span>
            <span class="mi">已解：<b>{{ ch.solved_count }}</b></span>
          </div>

          <a
            v-if="ch.attachment"
            class="btn primary dl"
            :href="`/api/challenges/${ch.id}/attachment`"
            download
          >⬇ 下载附件</a>
        </div>

        <!-- Flag 提交 -->
        <div class="flag-box">
          <div class="flag-head">
            <span>提交 Flag</span>
            <span class="hint">格式 flag{...}</span>
          </div>
          <div class="flag-row">
            <input
              v-model="flag"
              placeholder="flag{...}"
              :disabled="solved"
              @keyup.enter="submitFlag"
            />
            <button class="btn primary" :disabled="solved || submitting" @click="submitFlag">
              {{ submitting ? '提交中…' : '提交Flag' }}
            </button>
          </div>
          <p v-if="msg" class="msg" :class="msgOk ? 'ok' : 'err'">{{ msg }}</p>
        </div>
      </div>

      <!-- 右侧栏 -->
      <aside class="side">
        <div class="s-card stat">
          <div class="s-t">已解人数</div>
          <div class="s-num">{{ ch.solved_count }}</div>
        </div>
        <div class="s-card stat">
          <div class="s-t">当前排名</div>
          <div class="s-num">{{ myRank > 0 ? myRank : '--' }}</div>
        </div>

        <div class="s-card">
          <div class="s-t">最近解题者</div>
          <div class="solvers">
            <span
              v-for="(s, i) in shownSolvers"
              :key="i"
              class="avatar"
              :title="s.username"
            >{{ s.username[0].toUpperCase() }}</span>
            <span v-if="shownSolvers.length === 0" class="dim">暂无</span>
          </div>
        </div>
      </aside>
    </div>

    <div v-else class="loading err">题目不存在或未上架</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { challengesApi, type Challenge, type Solver } from '../api/challenges'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const ch = ref<Challenge | null>(null)
const solvers = ref<Solver[]>([])
const loading = ref(true)

const flag = ref('')
const msg = ref('')
const msgOk = ref(false)
const submitting = ref(false)
const solved = ref(false)
const myRank = ref(0)

const shownSolvers = computed(() => solvers.value.slice(0, 5))
const rendered = computed(() => renderMd(ch.value?.description ?? ''))

function renderMd(text: string): string {
  return text
    .split('\n')
    .map((line) => {
      const t = line
        .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
        .replace(/`(.+?)`/g, '<code>$1</code>')
      if (!t.trim()) return ''
      return `<p>${t}</p>`
    })
    .join('')
}

async function load() {
  const id = Number(route.params.id)
  loading.value = true
  try {
    ch.value = await challengesApi.get(id)
    solvers.value = await challengesApi.solvers(id)
    // 当前用户是否已解
    if (auth.isAuthenticated) {
      const all = await challengesApi.list()
      const mine = all.find((x) => x.id === id)
      if (mine) {
        solved.value = mine.solved_by_me
        const idx = solvers.value.findIndex((s) => s.username === auth.user?.username)
        myRank.value = idx >= 0 ? idx + 1 : 0
      }
    }
  } finally {
    loading.value = false
  }
}

async function submitFlag() {
  if (!auth.isAuthenticated) {
    router.push({ name: 'login' })
    return
  }
  if (!flag.value.trim()) return
  submitting.value = true
  try {
    const res = await challengesApi.submit(Number(route.params.id), flag.value.trim())
    msg.value = res.message
    msgOk.value = res.success
    if (res.success) {
      solved.value = true
      const fresh = await challengesApi.get(Number(route.params.id))
      ch.value = fresh
      solvers.value = await challengesApi.solvers(Number(route.params.id))
    }
  } catch (e) {
    msg.value = (e as Error).message
    msgOk.value = false
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin: 0 -24px;
}
.back {
  color: var(--muted);
  font-size: 13px;
}
.back:hover { color: var(--green); }
.loading {
  text-align: center;
  padding: 60px 0;
  color: var(--muted);
}
.loading.err { color: var(--red); }

.cols {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 20px;
  align-items: start;
}
.main {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 36px 40px;
}
.tagline {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}
.tag {
  font-size: 13px;
  color: var(--cyan);
  border: 1px solid rgba(0, 224, 255, 0.4);
  padding: 3px 12px;
  border-radius: 4px;
}
.status {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 20px;
}
.status.ok { color: var(--green); border: 1px solid var(--green); }
.status.wait { color: var(--amber); border: 1px solid var(--amber); }
.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}
.title { font-size: 30px; font-weight: 800; color: #eaf4ff; }
.pts {
  font-size: 30px;
  font-weight: 800;
  color: var(--green);
  text-shadow: 0 0 12px rgba(0, 255, 159, 0.5);
  white-space: nowrap;
}
.glow {
  border: 1px solid var(--green);
  border-radius: 10px;
  padding: 24px 28px;
  animation: glowPulse 2.2s ease-in-out infinite;
}
@keyframes glowPulse {
  0%, 100% {
    border-color: rgba(0, 255, 159, 0.45);
    box-shadow: 0 0 8px rgba(0, 255, 159, 0.18), inset 0 0 12px rgba(0, 255, 159, 0.04);
  }
  50% {
    border-color: var(--green);
    box-shadow: 0 0 24px rgba(0, 255, 159, 0.55), inset 0 0 18px rgba(0, 255, 159, 0.10);
  }
}
.desc { color: var(--text); font-size: 16.5px; line-height: 2; }
.desc p { margin-bottom: 12px; }
.desc code {
  font-family: var(--mono);
  background: rgba(0, 224, 255, 0.1);
  color: var(--cyan);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 15px;
}
.meta {
  display: flex;
  gap: 24px;
  margin: 18px 0;
  font-size: 14px;
  color: var(--muted);
}
.meta b { color: var(--amber); letter-spacing: 2px; }
.meta .mi b:not(:nth-of-type(1)) { color: var(--text); }
.dl {
  display: inline-block;
  margin-bottom: 22px;
}

.flag-box {
  border-top: 1px dashed var(--line2);
  padding-top: 20px;
}
.flag-head {
  display: flex;
  justify-content: space-between;
  font-size: 15px;
  color: #eaf4ff;
  margin-bottom: 10px;
}
.flag-head .hint { font-size: 12px; color: var(--dim); }
.flag-row {
  display: flex;
  gap: 10px;
}
.flag-row input {
  flex: 1;
  font-family: var(--mono);
  font-size: 15px;
  padding: 12px 16px;
  background: rgba(9, 22, 30, 0.9);
  border: 1px solid var(--line2);
  border-radius: 6px;
  color: var(--text);
  outline: none;
}
.flag-row input:focus { border-color: var(--green); }
.flag-row input:disabled { opacity: 0.5; }
.msg { margin-top: 10px; font-size: 13px; }
.msg.ok { color: var(--green); }
.msg.err { color: var(--red); }

.side {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.s-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
}
.s-t {
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 10px;
  letter-spacing: 1px;
}
.s-num {
  font-family: var(--mono);
  font-size: 30px;
  font-weight: 700;
  color: var(--green);
  text-shadow: 0 0 10px rgba(0, 255, 159, 0.3);
}
.solvers {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #06261a;
  background: var(--green);
  font-size: 14px;
  box-shadow: 0 0 10px rgba(0, 255, 159, 0.3);
}
.dim { color: var(--dim); font-size: 12px; }
.rel {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px dashed var(--line);
  color: var(--text);
  font-size: 13px;
}
.rel:hover { color: var(--green); }
.rel .rt { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rel .rp { font-family: var(--mono); color: var(--green); }
</style>
