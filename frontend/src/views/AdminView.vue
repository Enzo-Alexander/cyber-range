<template>
  <div class="admin">
    <!-- ADMIN 标 + 标题 -->
    <div class="adminbar">
      <span class="admin-badge">ADMIN</span>
      <span class="dim">· console</span>
    </div>

    <div class="cols">
      <!-- 左侧菜单 -->
      <aside class="side">
        <button
          v-for="m in menus"
          :key="m.id"
          class="m-item"
          :class="{ active: section === m.id }"
          @click="section = m.id"
        >{{ m.label }}</button>
      </aside>

      <!-- 右侧 -->
      <main class="main">
        <!-- 统计卡 -->
        <div class="stats">
          <div class="stat">
            <div class="v">{{ stats?.challenge_total ?? 0 }}</div>
            <div class="k">题目总数</div>
          </div>
          <div class="stat warn">
            <div class="v">{{ stats?.pending ?? 0 }}</div>
            <div class="k">待审核</div>
          </div>
          <div class="stat">
            <div class="v">{{ stats?.today ?? 0 }}</div>
            <div class="k">今日新增</div>
          </div>
          <div class="stat">
            <div class="v">{{ stats?.user_total ?? 0 }}</div>
            <div class="k">用户总数</div>
          </div>
        </div>

        <!-- 题目管理 -->
        <section v-if="section === 'challenges'" class="panel">
          <div class="panel-head">
            <div class="panel-t">题目管理</div>
            <button class="btn primary" @click="openCreate">+ 新建题目</button>
          </div>

          <table class="tbl">
            <thead>
              <tr>
                <th>题目</th>
                <th>分类</th>
                <th>难度</th>
                <th>分值</th>
                <th>作者</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ch in list" :key="ch.id">
                <td class="t">{{ ch.title }}</td>
                <td><span class="ct">{{ ch.category }}</span></td>
                <td class="stars">{{ '★'.repeat(ch.difficulty) }}</td>
                <td class="pts">{{ ch.points }}</td>
                <td class="au">{{ ch.author }}</td>
                <td><span class="st" :class="ch.status">{{ statusText(ch.status) }}</span></td>
                <td class="ops">
                  <button class="op" @click="openEdit(ch)">编辑</button>
                  <button class="op danger" @click="toggle(ch)">{{ ch.status === 'published' ? '下架' : '上架' }}</button>
                </td>
              </tr>
              <tr v-if="!loading && list.length === 0">
                <td colspan="7" class="empty">还没有题目</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section v-else class="panel">
          <div class="panel-t">{{ menus.find((m) => m.id === section)?.label }}</div>
          <p class="ph">该模块将在后续阶段开放。</p>
        </section>
      </main>
    </div>

    <!-- 新建/编辑题目弹窗 -->
    <div v-if="modal" class="overlay" @click.self="modal = false">
      <div class="dialog">
        <div class="d-head">{{ editing ? '编辑题目' : '新建题目' }}</div>
        <div class="form">
          <label>标题
            <input v-model="form.title" placeholder="题目名称" />
          </label>
          <div class="row2">
            <label>分类
              <select v-model="form.category">
                <option v-for="c in cats" :key="c" :value="c">{{ c }}</option>
              </select>
            </label>
            <label>难度
              <select v-model.number="form.difficulty">
                <option :value="1">1 星</option>
                <option :value="2">2 星</option>
                <option :value="3">3 星</option>
                <option :value="4">4 星</option>
                <option :value="5">5 星</option>
              </select>
            </label>
            <label>分值
              <input v-model.number="form.points" type="number" placeholder="100" />
            </label>
          </div>
          <label>Flag
            <input v-model="form.flag" placeholder="flag{...}" />
          </label>
          <label>附件
            <label class="upload-box">
              <input type="file" class="hidden-file" @change="onFile" />
              <template v-if="form.attachment">
                <span class="up-icon">📄</span>
                <span class="up-name">{{ form.attachment }}</span>
                <span class="up-remove" @click.stop="form.attachment = ''">✕ 移除</span>
              </template>
              <template v-else>
                <span class="up-icon">⬆</span>
                <span class="up-text">点击选择附件</span>
                <span class="up-hint">任意格式 · 可留空</span>
              </template>
            </label>
          </label>
          <label>描述
            <textarea v-model="form.description" rows="5" placeholder="题目描述 / 提示" />
          </label>
          <label>状态
            <select v-model="form.status">
              <option value="published">已上架</option>
              <option value="pending">待审核</option>
              <option value="draft">草稿</option>
            </select>
          </label>
        </div>
        <div class="d-ops">
          <button class="btn ghost" @click="modal = false">取消</button>
          <button class="btn primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { CATEGORIES, challengesApi, type AdminStats, type Challenge } from '../api/challenges'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const section = ref('challenges')
const menus = [
  { id: 'challenges', label: '题目管理' },
  { id: 'review', label: '题目审核' },
  { id: 'users', label: '用户管理' },
  { id: 'notice', label: '公告管理' },
  { id: 'site', label: '站点配置' },
  { id: 'logs', label: '日志审计' },
]
const cats = CATEGORIES.filter((c) => c !== '全部')

const stats = ref<AdminStats | null>(null)
const list = ref<Challenge[]>([])
const loading = ref(true)

const modal = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive({
  title: '',
  category: 'Web安全',
  difficulty: 1,
  points: 100,
  flag: '',
  attachment: '',
  description: '',
  status: 'published',
})

async function onFile(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    const res = await challengesApi.uploadAttachment(file)
    form.attachment = res.filename
  } catch (e) {
    alert((e as Error).message)
  }
}

function statusText(s: string) {
  return { published: '已上架', pending: '待审核', draft: '已下架' }[s] ?? s
}

function openCreate() {
  editing.value = false
  editingId.value = null
  Object.assign(form, { title: '', category: 'Web安全', difficulty: 1, points: 100, flag: '', attachment: '', description: '', status: 'published' })
  modal.value = true
}

function openEdit(ch: Challenge) {
  editing.value = true
  editingId.value = ch.id
  Object.assign(form, {
    title: ch.title,
    category: ch.category,
    difficulty: ch.difficulty,
    points: ch.points,
    flag: '',
    attachment: ch.attachment ?? '',
    description: ch.description,
    status: ch.status,
  })
  modal.value = true
}

async function load() {
  loading.value = true
  try {
    const [s, l] = await Promise.all([challengesApi.adminStats(), challengesApi.adminList()])
    stats.value = s
    list.value = l
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    if (editing.value && editingId.value) {
      const b = { ...form } as Partial<typeof form>
      if (!form.flag) delete b.flag
      await challengesApi.adminUpdate(editingId.value, b as any)
    } else {
      await challengesApi.adminCreate({ ...form })
    }
    modal.value = false
    await load()
  } catch (e) {
    alert((e as Error).message)
  } finally {
    saving.value = false
  }
}

async function toggle(ch: Challenge) {
  const next = ch.status === 'published' ? 'draft' : 'published'
  await challengesApi.adminUpdate(ch.id, { status: next })
  await load()
}

onMounted(load)
</script>

<style scoped>
.admin { display: flex; flex-direction: column; gap: 16px; }
.adminbar {
  font-family: var(--mono);
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.admin-badge {
  background: var(--red);
  color: #fff;
  font-weight: 800;
  padding: 3px 12px;
  border-radius: 4px;
  letter-spacing: 1px;
  box-shadow: 0 0 12px rgba(255, 59, 48, 0.5);
}
.dim { color: var(--dim); }

.cols {
  display: grid;
  grid-template-columns: 170px 1fr;
  gap: 18px;
  align-items: start;
}
.side {
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

.main { display: flex; flex-direction: column; gap: 16px; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.stat {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 18px;
}
.stat .v { font-family: var(--mono); font-size: 30px; font-weight: 700; color: var(--green); }
.stat.warn .v { color: var(--amber); }
.stat .k { font-size: 12px; color: var(--muted); margin-top: 4px; }

.panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 20px 22px;
}
.panel-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.panel-t { font-size: 16px; font-weight: 700; color: #eaf4ff; }

.tbl { width: 100%; border-collapse: collapse; }
.tbl th {
  text-align: left;
  font-size: 12px;
  color: var(--muted);
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
  background: var(--panel2);
}
.tbl td { padding: 12px; border-bottom: 1px solid var(--line); font-size: 14px; color: var(--text); }
.tbl tr:last-child td { border-bottom: none; }
.tbl tr:hover td { background: rgba(0, 255, 159, 0.03); }
.t { font-weight: 600; }
.ct {
  font-size: 12px;
  color: var(--cyan);
  border: 1px solid rgba(0, 224, 255, 0.35);
  padding: 1px 8px;
  border-radius: 4px;
}
.stars { color: var(--amber); font-size: 13px; letter-spacing: 1px; }
.pts { font-family: var(--mono); color: var(--green); font-weight: 700; }
.au { color: var(--muted); font-size: 13px; }
.st { font-size: 12px; padding: 2px 10px; border-radius: 20px; }
.st.published { color: var(--green); border: 1px solid var(--green); }
.st.pending { color: var(--red); border: 1px solid var(--red); }
.st.draft { color: var(--dim); border: 1px solid var(--line2); }
.ops { display: flex; gap: 6px; }
.op {
  font-size: 12px;
  padding: 3px 10px;
  border: 1px solid var(--line2);
  background: transparent;
  color: var(--cyan);
  border-radius: 4px;
  cursor: pointer;
}
.op:hover { border-color: var(--green); color: var(--green); }
.op.danger { color: var(--muted); }
.op.danger:hover { border-color: var(--red); color: var(--red); }
.empty { text-align: center; color: var(--muted); padding: 30px; }
.ph { color: var(--muted); font-size: 14px; }

/* 弹窗 */
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(4, 10, 15, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.dialog {
  width: 520px;
  max-height: 86vh;
  overflow: auto;
  background: var(--panel);
  border: 1px solid var(--green);
  box-shadow: 0 0 40px rgba(0, 255, 159, 0.15);
  border-radius: 10px;
  padding: 22px;
}
.d-head { font-size: 17px; font-weight: 800; color: #eaf4ff; margin-bottom: 16px; }
.form { display: flex; flex-direction: column; gap: 12px; }
.form label { font-size: 13px; color: var(--muted); display: flex; flex-direction: column; gap: 5px; }
.form input, .form select, .form textarea {
  font-family: var(--mono);
  font-size: 14px;
  padding: 9px 12px;
  background: rgba(9, 22, 30, 0.9);
  border: 1px solid var(--line2);
  border-radius: 6px;
  color: var(--text);
  outline: none;
}
.form input:focus, .form select:focus, .form textarea:focus { border-color: var(--green); }
.form textarea { resize: vertical; font-family: inherit; }
.attach-row { display: flex; align-items: center; gap: 10px; }
.attach-row input[type='file'] {
  font-family: var(--mono);
  font-size: 13px;
  color: var(--muted);
}
.att-name { font-family: var(--mono); font-size: 12px; color: var(--green); }
.att-hint { font-size: 12px; color: var(--dim); }
.upload-box {
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px dashed var(--line2);
  border-radius: 8px;
  padding: 14px 16px;
  cursor: pointer;
  transition: 0.15s;
}
.upload-box:hover {
  border-color: var(--green);
  background: rgba(0, 255, 159, 0.04);
  box-shadow: 0 0 12px rgba(0, 255, 159, 0.08);
}
.upload-box .hidden-file { display: none; }
.up-icon { font-size: 20px; line-height: 1; }
.up-text { font-size: 14px; color: var(--muted); }
.up-hint { font-size: 12px; color: var(--dim); margin-left: auto; white-space: nowrap; }
.up-name { font-size: 13px; color: var(--green); font-family: var(--mono); word-break: break-all; }
.up-remove {
  margin-left: auto;
  font-size: 12px;
  color: var(--red);
  cursor: pointer;
  white-space: nowrap;
  border: 1px solid rgba(255, 59, 48, 0.5);
  border-radius: 4px;
  padding: 2px 8px;
}
.up-remove:hover { background: rgba(255, 59, 48, 0.1); }
.row2 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
.d-ops { display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; }
.btn.ghost { background: transparent; border: 1px solid var(--line2); color: var(--muted); }
</style>
