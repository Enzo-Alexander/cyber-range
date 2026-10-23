<template>
  <ChallengeDetailLayout
    :loading="loading"
    :vm="vm"
    :comp="null"
    back-to="/challenges"
    back-label="← 返回题目大厅"
    :status-label="solved ? '已解出' : '等待提交'"
    :status-class="solved ? 'ok' : 'wait'"
    :attachment-url="attachmentUrl"
    v-model:flag="flag"
    :submitting="submitting"
    :solved="solved"
    :msg="msg"
    :msg-ok="msgOk"
    :my-rank="myRank"
    :solvers="solvers"
    :can-favorite="canFavorite"
    :favorited="favorited"
    :favorite-busy="favoriteBusy"
    @submit="submitFlag"
    @toggle-favorite="toggleFavorite"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChallengeDetailLayout from '../components/ChallengeDetailLayout.vue'
import { challengesApi, type Challenge, type Solver } from '../api/challenges'
import { useAuthStore } from '../stores/auth'

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
const favorited = ref(false)
const favoriteBusy = ref(false)
const canFavorite = computed(
  () => auth.isAuthenticated && auth.user?.role !== 'admin',
)

const vm = computed(() => {
  const c = ch.value
  if (!c) return null
  return {
    title: c.title,
    category: c.category,
    difficulty: c.difficulty,
    description: c.description,
    attachment: c.attachment,
    points: c.points as number | null,
    author: c.author as string | null,
    solvedCount: c.solved_count as number | null,
  }
})

const attachmentUrl = computed(() => `/api/challenges/${route.params.id}/attachment`)

async function load() {
  const id = Number(route.params.id)
  loading.value = true
  ch.value = null
  solvers.value = []
  solved.value = false
  favorited.value = false
  myRank.value = 0
  flag.value = ''
  msg.value = ''
  try {
    ch.value = await challengesApi.get(id)
    favorited.value = ch.value.favorited_by_me
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
  } catch {
    // 交给布局组件展示「题目不存在或未上架」
  } finally {
    loading.value = false
  }
}

async function toggleFavorite() {
  if (!auth.isAuthenticated) {
    router.push({ name: 'login' })
    return
  }
  if (!canFavorite.value || favoriteBusy.value) return
  favoriteBusy.value = true
  try {
    const res = await challengesApi.toggleFavorite(Number(route.params.id))
    favorited.value = res.favorited
  } catch (e) {
    msg.value = (e as Error).message
    msgOk.value = false
  } finally {
    favoriteBusy.value = false
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
    const id = Number(route.params.id)
    const res = await challengesApi.submit(id, flag.value.trim())
    msg.value = res.message
    msgOk.value = res.success
    if (res.success) {
      solved.value = true
      const fresh = await challengesApi.get(id)
      ch.value = fresh
      solvers.value = await challengesApi.solvers(id)
    }
  } catch (e) {
    msg.value = (e as Error).message
    msgOk.value = false
  } finally {
    submitting.value = false
  }
}

watch(
  () => route.params.id,
  () => load()
)

onMounted(load)
</script>
