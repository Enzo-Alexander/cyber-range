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

        <!-- 题目审核 -->
        <section v-else-if="section === 'review'" class="panel">
          <div class="panel-head">
            <div class="panel-t">题目审核</div>
            <span class="review-count">{{ reviewList.length }} 个待审核</span>
          </div>
          <table class="tbl">
            <thead>
              <tr>
                <th>题目</th>
                <th>分类</th>
                <th>难度</th>
                <th>分值</th>
                <th>提交者</th>
                <th>提交时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ch in reviewList" :key="ch.id">
                <td class="t">{{ ch.title }}</td>
                <td><span class="ct">{{ ch.category }}</span></td>
                <td class="stars">{{ '★'.repeat(ch.difficulty) }}</td>
                <td class="pts">{{ ch.points }}</td>
                <td class="au">{{ ch.author }}</td>
                <td class="au">{{ formatDate(ch.created_at) }}</td>
                <td>
                  <button class="op review-open" @click="openReview(ch)">审核</button>
                </td>
              </tr>
              <tr v-if="!reviewLoading && reviewList.length === 0">
                <td colspan="7" class="empty">暂无待审核题目</td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- 公告管理 -->
        <section v-else-if="section === 'notice'" class="panel">
          <div class="panel-head">
            <div class="panel-t">公告管理</div>
          </div>
          <div class="art-form">
            <label>标题
              <input v-model="noticeForm.title" placeholder="公告标题" />
            </label>
            <label>内容
              <textarea v-model="noticeForm.content" rows="5" placeholder="公告内容" />
            </label>
            <label class="upload-box" style="margin-bottom:0">
              <input type="file" class="hidden-file" accept=".docx,.pdf" @change="onDocUpload($event, noticeForm)" />
              <span class="up-icon">📄</span>
              <span class="up-text">上传 Word / PDF 文档自动提取内容</span>
            </label>
            <div class="art-ops">
              <button class="btn primary" :disabled="artSaving || !noticeForm.title.trim()" @click="publishNotice">
                {{ artSaving ? '发布中…' : '发布公告' }}
              </button>
            </div>
          </div>
          <table class="tbl" style="margin-top: 18px">
            <thead>
              <tr><th>标题</th><th>作者</th><th>发布时间</th><th>操作</th></tr>
            </thead>
            <tbody>
              <tr v-for="a in noticeList" :key="a.id">
                <td class="t">{{ a.title }}</td>
                <td class="au">{{ a.author }}</td>
                <td class="au">{{ formatDate(a.created_at) }}</td>
                <td>
                  <button class="op danger" @click="removeNotice(a)">删除</button>
                </td>
              </tr>
              <tr v-if="!artLoading && noticeList.length === 0">
                <td colspan="4" class="empty">还没有发布过公告</td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- 文章管理 -->
        <section v-else-if="section === 'articles'" class="panel">
          <div class="panel-head">
            <div class="panel-t">文章管理</div>
          </div>
          <div class="art-form">
            <label>标题
              <input v-model="articleForm.title" placeholder="文章标题" />
            </label>
            <label>内容
              <textarea v-model="articleForm.content" rows="5" placeholder="文章内容" />
            </label>
            <label class="upload-box" style="margin-bottom:0">
              <input type="file" class="hidden-file" accept=".docx,.pdf" @change="onDocUpload($event, articleForm)" />
              <span class="up-icon">📄</span>
              <span class="up-text">上传 Word / PDF 文档自动提取内容</span>
            </label>
            <div class="art-ops">
              <button class="btn primary" :disabled="artSaving || !articleForm.title.trim()" @click="publishArticle">
                {{ artSaving ? '发布中…' : '发布文章' }}
              </button>
            </div>
          </div>
          <table class="tbl" style="margin-top: 18px">
            <thead>
              <tr><th>标题</th><th>作者</th><th>发布时间</th></tr>
            </thead>
            <tbody>
              <tr v-for="a in articleList" :key="a.id">
                <td class="t">{{ a.title }}</td>
                <td class="au">{{ a.author }}</td>
                <td class="au">{{ formatDate(a.created_at) }}</td>
              </tr>
              <tr v-if="!artLoading && articleList.length === 0">
                <td colspan="3" class="empty">还没有发布过文章</td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- 比赛管理 -->
        <section v-else-if="section === 'competitions'" class="panel">
          <div class="panel-head">
            <div class="panel-t">比赛管理</div>
          </div>

          <!-- 新建比赛 -->
          <div class="art-form">
            <div class="row2" style="grid-template-columns: 2fr 1fr 1fr">
              <label>比赛名称
                <input v-model="compForm.name" placeholder="如：长城杯" />
              </label>
              <label>图标
                <input v-model="compForm.icon" placeholder="🏆" />
              </label>
              <label>
                <span>&nbsp;</span>
                <button class="btn primary" :disabled="!compForm.name.trim()" @click="createComp">新建比赛</button>
              </label>
            </div>
            <label>描述
              <input v-model="compForm.description" placeholder="比赛简介" />
            </label>
          </div>

          <!-- 比赛列表 -->
          <table class="tbl" style="margin-top: 18px">
            <thead><tr><th>比赛</th><th>届次数</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="c in compList" :key="c.id">
                <td class="t">{{ c.icon }} {{ c.name }}</td>
                <td class="au">{{ editionCount[c.id] || 0 }} 届</td>
                <td class="ops">
                  <button class="op" @click="selectComp(c)">管理届次</button>
                  <button class="op" @click="editComp(c)">编辑简介</button>
                  <button class="op danger" @click="askDeleteComp(c)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- 选中比赛后：届次管理 -->
          <div v-if="selectedComp" style="margin-top: 24px">
            <div class="panel-t" style="margin-bottom:12px">{{ selectedComp.icon }} {{ selectedComp.name }} — 届次管理</div>
            <div class="art-form">
              <div class="row2" style="grid-template-columns: 2fr 1fr 1fr">
                <label>届次名称
                  <input v-model="editionForm.name" placeholder="如：2024 第一届" />
                </label>
                <label>年份
                  <input v-model.number="editionForm.year" type="number" placeholder="2024" />
                </label>
                <label>
                  <span>&nbsp;</span>
                  <button class="btn primary" :disabled="!editionForm.name.trim()" @click="createEdition">新建届次</button>
                </label>
              </div>
            </div>
            <table class="tbl" style="margin-top: 14px">
              <thead><tr><th>届次</th><th>年份</th><th>操作</th></tr></thead>
              <tbody>
                <tr v-for="e in editionList" :key="e.id">
                  <td class="t">{{ e.name }}</td>
                  <td class="au">{{ e.year }}</td>
                  <td class="ops">
                    <button class="op" @click="selectEdition(e)">管理题目</button>
                    <button class="op danger" @click="askDeleteEdition(e)">删除</button>
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- 选中届次后：题目管理 -->
            <div v-if="selectedEdition" style="margin-top: 24px">
              <div class="panel-t" style="margin-bottom:12px">{{ selectedComp.icon }} {{ selectedComp.name }} · {{ selectedEdition.name }} — 题目管理</div>
              <div class="art-form">
                <div class="row2" style="grid-template-columns: 2fr 1fr 1fr 1fr">
                  <label>题目名称
                    <input v-model="chForm.title" placeholder="题目名称" />
                  </label>
                  <label>分类
                    <select v-model="chForm.category">
                      <option>Web</option><option>逆向</option><option>Pwn</option><option>Crypto</option><option>Misc</option>
                    </select>
                  </label>
                  <label>难度
                    <select v-model.number="chForm.difficulty">
                      <option :value="1">1星</option><option :value="2">2星</option><option :value="3">3星</option><option :value="4">4星</option><option :value="5">5星</option>
                    </select>
                  </label>
                  <label>分数
                    <input v-model.number="chForm.points" type="number" min="0" max="100000" placeholder="100" />
                  </label>
                </div>
                <label>题目描述
                  <textarea v-model="chForm.description" rows="3" placeholder="题目描述" />
                </label>
                <label>Flag
                  <input v-model="chForm.flag" placeholder="flag{...}" />
                </label>
                <label>附件
                  <label class="upload-box" style="margin-bottom:0">
                    <input type="file" class="hidden-file" @change="onCompFile" />
                    <template v-if="chForm.attachment">
                      <span class="up-icon">📄</span>
                      <span class="up-name">{{ chForm.attachment }}</span>
                      <span class="up-remove" @click.stop="chForm.attachment = ''">✕ 移除</span>
                    </template>
                    <template v-else>
                      <span class="up-icon">⬆</span>
                      <span class="up-text">点击选择附件</span>
                    </template>
                  </label>
                </label>
                <div class="art-ops">
                  <button class="btn primary" :disabled="!chForm.title.trim()" @click="createCompChallenge">添加题目</button>
                </div>
              </div>
              <table class="tbl" style="margin-top: 14px">
                <thead><tr><th>题目</th><th>分类</th><th>难度</th><th>分数</th><th>已解</th><th>操作</th></tr></thead>
                <tbody>
                  <tr v-for="ch in compChallenges" :key="ch.id">
                    <td class="t">{{ ch.title }}</td>
                    <td class="au">{{ ch.category }}</td>
                    <td class="au">{{ '★'.repeat(ch.difficulty) }}</td>
                    <td class="au">{{ ch.points }}</td>
                    <td class="au">{{ ch.solved_count }}</td>
                    <td class="ops">
                      <button class="op danger" @click="removeChallenge(ch)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
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
              <option value="rejected">已驳回</option>
            </select>
          </label>
        </div>
        <div class="d-ops">
          <button class="btn ghost" @click="modal = false">取消</button>
          <button class="btn primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
        </div>
      </div>
    </div>

    <!-- 编辑比赛弹窗 -->
    <div v-if="editCompModal" class="overlay" @click.self="editCompModal = false">
      <div class="dialog" style="width:480px">
        <div class="d-head">编辑比赛</div>
        <div class="form">
          <label>比赛名称
            <input v-model="editCompForm.name" />
          </label>
          <label>图标
            <input v-model="editCompForm.icon" />
          </label>
          <label>简介
            <textarea v-model="editCompForm.description" rows="3" />
          </label>
        </div>
        <div class="d-ops">
          <button class="btn ghost" @click="editCompModal = false">取消</button>
          <button class="btn primary" :disabled="!editCompForm.name.trim()" @click="saveComp">保存</button>
        </div>
      </div>
    </div>

    <!-- 题目审核弹窗 -->
    <div v-if="reviewTarget" class="overlay" @click.self="reviewTarget = null">
      <div class="dialog review-dialog">
        <div class="d-head">
          题目审核
          <span class="review-state">待审核</span>
        </div>
        <div class="review-content">
          <h3>{{ reviewTarget.title }}</h3>
          <div class="review-meta">
            <span>{{ reviewTarget.category }}</span>
            <span>{{ '★'.repeat(reviewTarget.difficulty) }}</span>
            <span>{{ reviewTarget.points }} 分</span>
            <span>提交者：{{ reviewTarget.author }}</span>
            <span>{{ formatDate(reviewTarget.created_at) }}</span>
          </div>
          <div class="review-block">
            <div class="review-label">题目描述</div>
            <pre>{{ reviewTarget.description || '暂无描述' }}</pre>
          </div>
          <div class="review-grid">
            <div class="review-block">
              <div class="review-label">Flag</div>
              <code>{{ reviewTarget.flag }}</code>
            </div>
            <div class="review-block">
              <div class="review-label">附件</div>
              <a
                v-if="reviewTarget.attachment"
                class="review-file"
                :href="challengesApi.adminAttachmentUrl(reviewTarget.id)"
                download
              >{{ reviewTarget.attachment }}</a>
              <span v-else class="review-empty">无附件</span>
            </div>
          </div>
        </div>
        <div class="d-ops">
          <button class="btn ghost" @click="reviewTarget = null">取消</button>
          <button
            class="btn review-reject"
            :disabled="reviewSaving"
            @click="decideReview('rejected')"
          >驳回</button>
          <button
            class="btn primary"
            :disabled="reviewSaving"
            @click="decideReview('published')"
          >{{ reviewSaving ? '处理中…' : '通过并上架' }}</button>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="deleteModal" class="overlay" @click.self="deleteModal = false">
      <div class="dialog" style="width:440px">
        <div class="d-head" style="color:var(--red)">⚠ 确认删除</div>
        <p style="color:var(--text);font-size:14px;line-height:1.7;margin:12px 0">
          {{ deleteWarning }}
        </p>
        <label v-if="deleteNeedPassword" style="font-size:13px;color:var(--muted);display:flex;flex-direction:column;gap:5px">
          请输入管理员密码确认
          <input v-model="deletePassword" type="password" placeholder="管理员密码" @keyup.enter="confirmDelete" />
        </label>
        <div class="d-ops">
          <button class="btn ghost" @click="deleteModal = false">取消</button>
          <button class="btn" style="background:var(--red);border-color:var(--red);color:#fff" :disabled="deleteNeedPassword && !deletePassword" @click="confirmDelete">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  CATEGORIES,
  challengesApi,
  type AdminChallenge,
  type AdminStats,
  type Challenge,
} from '../api/challenges'
import { articlesApi, type Article } from '../api/articles'
import { competitionsApi, type Competition, type CompetitionEdition, type CompetitionChallenge } from '../api/competitions'
import { useAuthStore } from '../stores/auth'
import { parseServerDate } from '../utils/datetime'

const auth = useAuthStore()
const route = useRoute()
const section = ref('challenges')
const menus = [
  { id: 'challenges', label: '题目管理' },
  { id: 'competitions', label: '比赛管理' },
  { id: 'review', label: '题目审核' },
  { id: 'users', label: '用户管理' },
  { id: 'notice', label: '公告管理' },
  { id: 'articles', label: '文章管理' },
  { id: 'site', label: '站点配置' },
  { id: 'logs', label: '日志审计' },
]
const cats = CATEGORIES.filter((c) => c !== '全部')

const stats = ref<AdminStats | null>(null)
const list = ref<Challenge[]>([])
const loading = ref(true)
const reviewList = ref<AdminChallenge[]>([])
const reviewLoading = ref(false)
const reviewTarget = ref<AdminChallenge | null>(null)
const reviewSaving = ref(false)

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

async function onCompFile(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    const res = await challengesApi.uploadAttachment(file)
    chForm.attachment = res.filename
  } catch (e) {
    alert((e as Error).message)
  }
}

function statusText(s: string) {
  return {
    published: '已上架',
    pending: '待审核',
    draft: '已下架',
    rejected: '已驳回',
  }[s] ?? s
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

// ---------- 题目审核 ----------
async function loadReview() {
  reviewLoading.value = true
  try {
    reviewList.value = await challengesApi.adminList('pending')
  } catch (e) {
    reviewList.value = []
    alert((e as Error).message)
  } finally {
    reviewLoading.value = false
  }
}

function openReview(ch: AdminChallenge) {
  reviewTarget.value = ch
}

async function decideReview(status: 'published' | 'rejected') {
  if (!reviewTarget.value) return
  reviewSaving.value = true
  try {
    await challengesApi.adminUpdate(reviewTarget.value.id, { status })
    reviewTarget.value = null
    await Promise.all([loadReview(), load()])
  } catch (e) {
    alert((e as Error).message)
  } finally {
    reviewSaving.value = false
  }
}

// ---------- 比赛管理 ----------
const compList = ref<Competition[]>([])
const selectedComp = ref<Competition | null>(null)
const editionList = ref<CompetitionEdition[]>([])
const selectedEdition = ref<CompetitionEdition | null>(null)
const compChallenges = ref<CompetitionChallenge[]>([])
const editionCount = ref<Record<number, number>>({})

const compForm = reactive({ name: '', description: '', icon: '🏆' })
const editionForm = reactive({ name: '', year: 2024 })
const chForm = reactive({ title: '', category: 'Web', difficulty: 1, points: 100, description: '', flag: '', attachment: '' })

// 编辑比赛
const editCompModal = ref(false)
const editCompId = ref(0)
const editCompForm = reactive({ name: '', description: '', icon: '🏆' })

function editComp(c: Competition) {
  editCompId.value = c.id
  editCompForm.name = c.name
  editCompForm.description = c.description
  editCompForm.icon = c.icon
  editCompModal.value = true
}

async function saveComp() {
  await competitionsApi.updateCompetition(editCompId.value, { ...editCompForm })
  editCompModal.value = false
  await loadComps()
}

// 删除确认
const deleteModal = ref(false)
const deletePassword = ref('')
const deleteWarning = ref('')
const deleteNeedPassword = ref(true)
let deleteAction: (() => Promise<void>) | null = null

function askDeleteComp(c: Competition) {
  deleteWarning.value = `删除比赛「${c.name}」将同时删除其下所有届次及所有题目，此操作不可恢复！`
  deletePassword.value = ''
  deleteNeedPassword.value = true
  deleteAction = async () => {
    await competitionsApi.deleteCompetition(c.id, deletePassword.value)
    selectedComp.value = null
    selectedEdition.value = null
    await loadComps()
  }
  deleteModal.value = true
}

function askDeleteEdition(e: CompetitionEdition) {
  deleteWarning.value = `删除届次「${e.name}」将同时删除其下所有题目，此操作不可恢复！`
  deletePassword.value = ''
  deleteNeedPassword.value = true
  deleteAction = async () => {
    await competitionsApi.deleteEdition(e.id, deletePassword.value)
    selectedEdition.value = null
    compChallenges.value = []
    if (selectedComp.value) {
      editionList.value = await competitionsApi.editions(selectedComp.value.id)
    }
    await loadComps()
  }
  deleteModal.value = true
}

async function confirmDelete() {
  if (!deleteAction) return
  try {
    await deleteAction()
    deleteModal.value = false
  } catch (e) {
    alert((e as Error).message)
  }
}

async function removeChallenge(ch: CompetitionChallenge) {
  if (!selectedEdition.value) return
  deleteWarning.value = `确定删除题目「${ch.title}」吗？`
  deletePassword.value = ''
  deleteNeedPassword.value = false
  deleteAction = async () => {
    await competitionsApi.deleteChallenge(ch.id)
    compChallenges.value = await competitionsApi.editionChallenges(selectedEdition.value!.id)
  }
  deleteModal.value = true
}

async function loadComps() {
  compList.value = await competitionsApi.list()
  const counts: Record<number, number> = {}
  for (const c of compList.value) {
    const eds = await competitionsApi.editions(c.id)
    counts[c.id] = eds.length
  }
  editionCount.value = counts
}

async function createComp() {
  await competitionsApi.createCompetition({ ...compForm })
  compForm.name = ''; compForm.description = ''; compForm.icon = '🏆'
  await loadComps()
}

async function selectComp(c: Competition) {
  selectedComp.value = c
  selectedEdition.value = null
  compChallenges.value = []
  editionList.value = await competitionsApi.editions(c.id)
}

async function createEdition() {
  if (!selectedComp.value) return
  await competitionsApi.createEdition({
    competition_id: selectedComp.value.id,
    name: editionForm.name,
    year: editionForm.year,
  })
  editionForm.name = ''
  editionList.value = await competitionsApi.editions(selectedComp.value.id)
  await loadComps()
}

async function selectEdition(e: CompetitionEdition) {
  selectedEdition.value = e
  compChallenges.value = await competitionsApi.editionChallenges(e.id)
}

async function createCompChallenge() {
  if (!selectedEdition.value) return
  try {
    await competitionsApi.createChallenge({
      edition_id: selectedEdition.value.id,
      title: chForm.title,
      category: chForm.category,
      difficulty: chForm.difficulty,
      points: Number(chForm.points) || 0,
      description: chForm.description,
      flag: chForm.flag,
      attachment: chForm.attachment || null,
    })
    chForm.title = ''; chForm.description = ''; chForm.flag = ''; chForm.attachment = ''
    chForm.points = 100
    compChallenges.value = await competitionsApi.editionChallenges(selectedEdition.value.id)
  } catch (e) {
    alert('创建失败: ' + (e as Error).message)
  }
}

onMounted(() => {
  if (route.query.section === 'review') section.value = 'review'
  load()
  loadArticles()
  loadComps()
})

watch(section, (value) => {
  if (value === 'review') loadReview()
})

// ---------- 公告 / 文章 ----------
const artList = ref<Article[]>([])
const artLoading = ref(true)
const artSaving = ref(false)
const noticeForm = reactive({ title: '', content: '' })
const articleForm = reactive({ title: '', content: '' })

const noticeList = ref<Article[]>([])
const articleList = ref<Article[]>([])

function formatDate(s: string) {
  const d = parseServerDate(s)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

async function loadArticles() {
  artLoading.value = true
  try {
    artList.value = await articlesApi.list()
    noticeList.value = artList.value.filter((a) => a.type === 'announcement')
    articleList.value = artList.value.filter((a) => a.type === 'article')
  } catch {
    artList.value = []
    noticeList.value = []
    articleList.value = []
  } finally {
    artLoading.value = false
  }
}

async function publishNotice() {
  artSaving.value = true
  try {
    await articlesApi.create({ title: noticeForm.title.trim(), content: noticeForm.content, type: 'announcement' })
    noticeForm.title = ''
    noticeForm.content = ''
    await loadArticles()
  } catch (e) {
    alert((e as Error).message)
  } finally {
    artSaving.value = false
  }
}

function removeNotice(item: Article) {
  deleteWarning.value = `确定删除公告「${item.title}」吗？此操作不可恢复。`
  deletePassword.value = ''
  deleteNeedPassword.value = false
  deleteAction = async () => {
    await articlesApi.remove(item.id)
    await loadArticles()
  }
  deleteModal.value = true
}

async function onDocUpload(ev: Event, form: { title: string; content: string }) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  artSaving.value = true
  try {
    const res = await articlesApi.parseDoc(file)
    form.title = res.suggested_title
    form.content = res.content
  } catch (e) {
    alert('文档解析失败: ' + (e as Error).message)
  } finally {
    artSaving.value = false
    input.value = ''
  }
}

async function publishArticle() {
  artSaving.value = true
  try {
    await articlesApi.create({ title: articleForm.title.trim(), content: articleForm.content, type: 'article' })
    articleForm.title = ''
    articleForm.content = ''
    await loadArticles()
  } catch (e) {
    alert((e as Error).message)
  } finally {
    artSaving.value = false
  }
}
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
  box-shadow: 0 0 12px rgba(var(--red-rgb), 0.5);
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
.m-item.active { color: var(--green); background: rgba(var(--green-rgb), 0.08); }

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
.panel-t { font-size: 16px; font-weight: 700; color: var(--text-strong); }
.review-count {
  color: var(--amber);
  font-family: var(--mono);
  font-size: 12px;
}

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
.tbl tr:hover td { background: rgba(var(--green-rgb), 0.03); }
.t { font-weight: 600; }
.ct {
  font-size: 12px;
  color: var(--cyan);
  border: 1px solid rgba(var(--cyan-rgb), 0.35);
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
.st.rejected { color: var(--red); border: 1px solid rgba(var(--red-rgb), 0.65); background: rgba(var(--red-rgb), 0.06); }
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
.review-open { color: var(--amber); border-color: rgba(var(--amber-rgb), 0.45); }
.review-open:hover { color: var(--amber); border-color: var(--amber); }
.op.danger { color: var(--muted); }
.op.danger:hover { border-color: var(--red); color: var(--red); }
.empty { text-align: center; color: var(--muted); padding: 30px; }
.ph { color: var(--muted); font-size: 14px; }

/* 题目审核 */
.review-dialog { width: 640px; }
.review-state {
  padding: 2px 9px;
  border: 1px solid rgba(var(--amber-rgb), 0.55);
  border-radius: 4px;
  color: var(--amber);
  font-size: 11px;
  font-weight: 700;
}
.review-content h3 {
  margin-bottom: 10px;
  color: var(--text-strong);
  font-size: 21px;
  line-height: 1.4;
}
.review-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin-bottom: 18px;
  color: var(--muted);
  font-size: 12px;
}
.review-block {
  min-width: 0;
  margin-bottom: 14px;
}
.review-label {
  margin-bottom: 7px;
  color: var(--dim);
  font-family: var(--mono);
  font-size: 11px;
}
.review-block pre {
  max-height: 240px;
  overflow-y: auto;
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--bg2);
  color: var(--text);
  font-family: var(--sans);
  font-size: 13px;
  line-height: 1.75;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.review-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.review-grid code {
  display: block;
  overflow: hidden;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--bg2);
  color: var(--green);
  font-family: var(--mono);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.review-file {
  display: block;
  overflow: hidden;
  padding: 10px 12px;
  border: 1px dashed var(--line2);
  border-radius: 6px;
  color: var(--cyan);
  font-size: 12px;
  text-decoration: none;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.review-file:hover { border-color: var(--cyan); }
.review-empty {
  display: block;
  padding: 10px 12px;
  color: var(--dim);
  font-size: 12px;
}
.review-reject {
  border-color: rgba(var(--red-rgb), 0.6);
  color: var(--red);
}
.review-reject:hover { border-color: var(--red); color: var(--red); }
@media (max-width: 820px) {
  .review-grid { grid-template-columns: 1fr; }
}

/* 弹窗 */
.overlay {
  position: fixed;
  inset: 0;
  background: var(--overlay-bg);
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
  box-shadow: 0 0 40px rgba(var(--green-rgb), 0.15);
  border-radius: 10px;
  padding: 22px;
}
.d-head { font-size: 17px; font-weight: 800; color: var(--text-strong); margin-bottom: 16px; }
.form { display: flex; flex-direction: column; gap: 12px; }
.form label { font-size: 13px; color: var(--muted); display: flex; flex-direction: column; gap: 5px; }
.form input, .form select, .form textarea {
  font-family: var(--mono);
  font-size: 14px;
  padding: 9px 12px;
  background: var(--field-bg);
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
  background: rgba(var(--green-rgb), 0.04);
  box-shadow: 0 0 12px rgba(var(--green-rgb), 0.08);
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
  border: 1px solid rgba(var(--red-rgb), 0.5);
  border-radius: 4px;
  padding: 2px 8px;
}
.up-remove:hover { background: rgba(var(--red-rgb), 0.1); }
.row2 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
.d-ops { display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; }
.btn.ghost { background: transparent; border: 1px solid var(--line2); color: var(--muted); }

.art-form { display: flex; flex-direction: column; gap: 12px; }
.art-form label { font-size: 13px; color: var(--muted); display: flex; flex-direction: column; gap: 5px; }
.art-form input, .art-form textarea {
  font-family: var(--mono);
  font-size: 14px;
  padding: 9px 12px;
  background: var(--field-bg);
  border: 1px solid var(--line2);
  border-radius: 6px;
  color: var(--text);
  outline: none;
}
.art-form input:focus, .art-form textarea:focus { border-color: var(--green); }
.art-form textarea { resize: vertical; font-family: inherit; }
.art-ops { display: flex; justify-content: flex-end; }
.art-form select {
  font-family: var(--mono);
  font-size: 14px;
  padding: 9px 12px;
  background: var(--field-bg);
  border: 1px solid var(--line2);
  border-radius: 6px;
  color: var(--text);
  outline: none;
  cursor: pointer;
}
.art-form select:focus { border-color: var(--green); }
.art-form select option { background: var(--panel); color: var(--text); }
</style>
