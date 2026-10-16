<template>
  <ChallengeDetailLayout
    :loading="loading"
    :vm="vm"
    :comp="compInfo"
    :back-to="backTo"
    back-label="← 返回比赛真题"
    :status-label="solved ? '已解出' : '比赛真题'"
    :status-class="solved ? 'comp-ok' : 'comp'"
    :attachment-url="attachmentUrl"
    v-model:flag="flag"
    :submitting="submitting"
    :solved="solved"
    :msg="msg"
    :msg-ok="msgOk"
    :my-rank="0"
    :solvers="[]"
    @submit="submitFlag"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChallengeDetailLayout from '../components/ChallengeDetailLayout.vue'
import { competitionsApi, type CompetitionChallengeDetail } from '../api/competitions'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const ch = ref<CompetitionChallengeDetail | null>(null)
const loading = ref(true)

const flag = ref('')
const msg = ref('')
const msgOk = ref(false)
const submitting = ref(false)
const solved = ref(false)

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
    // 比赛真题没有作者，右栏改为展示比赛信息
    author: null as string | null,
    solvedCount: c.solved_count as number | null,
  }
})

const compInfo = computed(() => {
  const c = ch.value
  if (!c) return null
  return {
    competition_name: c.competition_name,
    competition_icon: c.competition_icon,
    edition_name: c.edition_name,
    edition_year: c.edition_year,
  }
})

/** 返回时带上比赛/届次，直接回到原来那一层 */
const backTo = computed(() => {
  const params = new URLSearchParams({ tab: 'competitions' })
  if (ch.value?.competition_id) params.set('comp', String(ch.value.competition_id))
  if (ch.value?.edition_id) params.set('edition', String(ch.value.edition_id))
  return `/challenges?${params.toString()}`
})

const attachmentUrl = computed(() => `/api/competitions/challenges/${route.params.id}/attachment`)

async function load() {
  const id = Number(route.params.id)
  loading.value = true
  ch.value = null
  flag.value = ''
  msg.value = ''
  solved.value = false
  try {
    ch.value = await competitionsApi.challenge(id)
    // 解题记录已持久化，进入页面即回显是否已解出
    solved.value = ch.value.solved_by_me
  } catch {
    // 交给布局组件展示「题目不存在或未上架」
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
    // flag 由后端校验，前端拿不到答案
    const res = await competitionsApi.submitChallenge(Number(route.params.id), flag.value.trim())
    msg.value = res.message
    msgOk.value = res.success
    if (res.success) {
      solved.value = true
      ch.value = await competitionsApi.challenge(Number(route.params.id))
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
