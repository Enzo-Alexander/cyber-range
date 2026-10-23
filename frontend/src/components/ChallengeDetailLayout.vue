<!--
  题目详情页布局（题目大厅 / 比赛真题共用）。
  两个入口的数据来源不同，但这里保证渲染出来的结构与样式完全一致。
-->
<template>
  <div class="detail">
    <router-link :to="backTo" class="back">{{ backLabel }}</router-link>

    <div v-if="loading" class="loading">加载题目中…</div>

    <div v-else-if="vm" class="cols">
      <!-- 左主区 -->
      <div class="main">
        <div class="tagline">
          <span class="tag">{{ vm.category }}</span>
          <span class="status" :class="statusClass">{{ statusLabel }}</span>
        </div>
        <div class="title-row">
          <h1 class="title">{{ vm.title }}</h1>
          <div class="title-actions">
            <button
              v-if="canFavorite"
              class="fav-btn"
              :class="{ on: favorited }"
              :disabled="favoriteBusy"
              @click="emit('toggle-favorite')"
            >
              <span class="fav-star">{{ favorited ? '★' : '☆' }}</span>
              {{ favoriteBusy ? '处理中…' : favorited ? '已收藏' : '收藏' }}
            </button>
            <div v-if="vm.points !== null" class="pts">+{{ vm.points }}</div>
          </div>
        </div>

        <div class="glow">
          <div class="desc" v-html="rendered" />

          <div class="meta">
            <span class="mi">难度：<b>{{ '★'.repeat(vm.difficulty) }}</b></span>
            <template v-if="comp">
              <span class="mi">比赛：<b>{{ comp.competition_name }}</b></span>
              <span class="mi">届次：<b>{{ comp.edition_name }}</b></span>
            </template>
            <template v-else>
              <span class="mi">作者：<b>{{ vm.author }}</b></span>
              <span class="mi">已解：<b>{{ vm.solvedCount }}</b></span>
            </template>
          </div>

          <a v-if="vm.attachment" class="btn primary dl" :href="attachmentUrl" download>⬇ 下载附件</a>
        </div>

        <!-- Flag 提交 -->
        <div class="flag-box">
          <div class="flag-head">
            <span>提交 Flag</span>
            <span class="hint">格式 flag{...}</span>
          </div>
          <div class="flag-row">
            <input
              :value="flag"
              placeholder="flag{...}"
              :disabled="solved"
              @input="emit('update:flag', ($event.target as HTMLInputElement).value)"
              @keyup.enter="emit('submit')"
            />
            <button class="btn primary" :disabled="solved || submitting" @click="emit('submit')">
              {{ submitting ? '提交中…' : '提交Flag' }}
            </button>
          </div>
          <p v-if="msg" class="msg" :class="msgOk ? 'ok' : 'err'">{{ msg }}</p>
        </div>
      </div>

      <!-- 右侧栏 -->
      <aside class="side">
        <template v-if="comp">
          <div class="s-card">
            <div class="s-t">所属比赛</div>
            <div class="s-name">{{ comp.competition_icon }} {{ comp.competition_name }}</div>
          </div>
          <div class="s-card">
            <div class="s-t">届次</div>
            <div class="s-name">{{ comp.edition_name }}</div>
            <div class="s-sub">{{ comp.edition_year }} 年</div>
          </div>
          <div class="s-card stat">
            <div class="s-t">难度</div>
            <div class="s-stars">{{ '★'.repeat(vm.difficulty) }}</div>
          </div>
        </template>

        <template v-else>
          <div class="s-card stat">
            <div class="s-t">已解人数</div>
            <div class="s-num">{{ vm.solvedCount }}</div>
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
        </template>
      </aside>
    </div>

    <div v-else class="loading err">题目不存在或未上架</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface DetailVM {
  title: string
  category: string
  difficulty: number
  description: string
  attachment: string | null
  points: number | null
  author: string | null
  solvedCount: number | null
}

export interface CompInfo {
  competition_name: string
  competition_icon: string
  edition_name: string
  edition_year: number
}

const props = defineProps<{
  loading: boolean
  vm: DetailVM | null
  /** 传值时右栏显示比赛信息，否则显示解题统计 */
  comp?: CompInfo | null
  backTo: string
  backLabel: string
  statusLabel: string
  statusClass: string
  attachmentUrl: string
  flag: string
  submitting: boolean
  solved: boolean
  msg: string
  msgOk: boolean
  myRank: number
  solvers: { username: string }[]
  canFavorite?: boolean
  favorited?: boolean
  favoriteBusy?: boolean
}>()

const emit = defineEmits<{
  submit: []
  'update:flag': [string]
  'toggle-favorite': []
}>()

const shownSolvers = computed(() => props.solvers.slice(0, 5))

const rendered = computed(() => renderMd(props.vm?.description ?? ''))

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
  border: 1px solid rgba(var(--cyan-rgb), 0.4);
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
.status.comp { color: var(--cyan); border: 1px solid rgba(var(--cyan-rgb), 0.5); }
.status.comp-ok { color: var(--amber); border: 1px solid var(--amber); }
.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}
.title { font-size: 30px; font-weight: 800; color: var(--text-strong); }
.title-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}
.fav-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--line2);
  border-radius: 6px;
  background: transparent;
  color: var(--muted);
  font-size: 12px;
  cursor: pointer;
  transition: 0.15s;
}
.fav-btn:hover {
  border-color: var(--amber);
  color: var(--amber);
}
.fav-btn.on {
  border-color: rgba(var(--amber-rgb), 0.65);
  background: rgba(var(--amber-rgb), 0.08);
  color: var(--amber);
}
.fav-btn:disabled {
  opacity: 0.55;
  cursor: wait;
}
.fav-star {
  font-size: 16px;
  line-height: 1;
}
.pts {
  font-size: 30px;
  font-weight: 800;
  color: var(--green);
  text-shadow: 0 0 12px rgba(var(--green-rgb), 0.5);
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
    border-color: rgba(var(--green-rgb), 0.45);
    box-shadow: 0 0 8px rgba(var(--green-rgb), 0.18), inset 0 0 12px rgba(var(--green-rgb), 0.04);
  }
  50% {
    border-color: var(--green);
    box-shadow: 0 0 24px rgba(var(--green-rgb), 0.55), inset 0 0 18px rgba(var(--green-rgb), 0.10);
  }
}
.desc { color: var(--text); font-size: 16.5px; line-height: 2; }
.desc p { margin-bottom: 12px; }
.desc code {
  font-family: var(--mono);
  background: rgba(var(--cyan-rgb), 0.1);
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
  color: var(--text-strong);
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
  background: var(--field-bg);
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
  text-shadow: 0 0 10px rgba(var(--green-rgb), 0.3);
}
.s-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-strong);
  line-height: 1.4;
}
.s-sub {
  font-size: 12px;
  color: var(--dim);
  margin-top: 4px;
}
.s-stars {
  font-size: 18px;
  color: var(--amber);
  letter-spacing: 3px;
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
  color: var(--on-accent);
  background: var(--green);
  font-size: 14px;
  box-shadow: 0 0 10px rgba(var(--green-rgb), 0.3);
}
.dim { color: var(--dim); font-size: 12px; }
</style>
