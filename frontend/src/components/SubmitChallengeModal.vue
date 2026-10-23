<template>
  <div class="overlay" @click.self="emit('close')">
    <div class="dialog">
      <div class="d-head">
        提交题目
        <span class="d-sub">通过审核后才会公开</span>
      </div>

      <div v-if="done" class="done">
        <div class="done-mark">✓</div>
        <h3>题目已提交</h3>
        <p>管理员审核后会通过站内通知反馈结果。</p>
        <button class="btn primary" @click="emit('close')">关闭</button>
      </div>

      <template v-else>
        <div class="form">
          <label>题目名称
            <input v-model="form.title" placeholder="输入题目名称" maxlength="200" />
          </label>

          <div class="row3">
            <label>分类
              <select v-model="form.category">
                <option v-for="category in categories" :key="category" :value="category">
                  {{ category }}
                </option>
              </select>
            </label>
            <label>难度
              <select v-model.number="form.difficulty">
                <option v-for="n in 5" :key="n" :value="n">{{ n }} 星</option>
              </select>
            </label>
            <label>分值
              <input v-model.number="form.points" type="number" min="0" max="100000" />
            </label>
          </div>

          <label>题目描述
            <textarea
              v-model="form.description"
              rows="5"
              placeholder="题目背景、提示、解题要求等"
            />
          </label>

          <label>Flag
            <input v-model="form.flag" placeholder="flag{...}" maxlength="255" />
          </label>

          <label class="attachment">附件
            <span class="upload-box">
              <input type="file" class="hidden-file" @change="onFile" />
              <template v-if="file">
                <span class="file-name">{{ file.name }}</span>
                <span class="file-remove" @click.prevent="clearFile">移除</span>
              </template>
              <span v-else class="upload-text">选择题目附件（可选）</span>
            </span>
          </label>
        </div>

        <p v-if="error" class="error">{{ error }}</p>

        <div class="d-ops">
          <button class="btn ghost" @click="emit('close')">取消</button>
          <button class="btn primary" :disabled="!canSubmit" @click="submit">
            {{ saving ? '提交中…' : '提交审核' }}
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { CATEGORIES, challengesApi } from '../api/challenges'

const emit = defineEmits<{ close: [] }>()

const categories = CATEGORIES.filter((item) => item !== '全部')
const form = reactive({
  title: '',
  category: 'Web安全',
  difficulty: 2,
  points: 100,
  description: '',
  flag: '',
})

const file = ref<File | null>(null)
const saving = ref(false)
const done = ref(false)
const error = ref('')

const canSubmit = computed(
  () => !!form.title.trim() && !!form.flag.trim() && !saving.value,
)

function onFile(event: Event) {
  const input = event.target as HTMLInputElement
  file.value = input.files?.[0] ?? null
}

function clearFile() {
  file.value = null
}

async function submit() {
  if (!canSubmit.value) return
  saving.value = true
  error.value = ''
  try {
    let attachment: string | null = null
    if (file.value) {
      const uploaded = await challengesApi.uploadSubmissionAttachment(file.value)
      attachment = uploaded.filename
    }
    await challengesApi.submitChallenge({
      title: form.title.trim(),
      category: form.category,
      difficulty: form.difficulty,
      points: form.points,
      description: form.description,
      attachment,
      flag: form.flag.trim(),
    })
    done.value = true
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: var(--overlay-bg);
}
.dialog {
  width: 620px;
  max-width: 100%;
  max-height: min(88vh, 760px);
  overflow-y: auto;
  padding: 24px;
  border: 1px solid var(--line2);
  border-radius: 8px;
  background: var(--panel);
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.42);
}
.d-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 18px;
  color: var(--text-strong);
  font-size: 18px;
  font-weight: 800;
}
.d-sub {
  color: var(--dim);
  font-size: 12px;
  font-weight: 500;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--muted);
  font-size: 13px;
}
.form input,
.form select,
.form textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--line2);
  border-radius: 6px;
  outline: none;
  background: var(--bg2);
  color: var(--text);
  font-family: var(--sans);
  font-size: 14px;
}
.form textarea {
  resize: vertical;
  min-height: 100px;
}
.form input:focus,
.form select:focus,
.form textarea:focus {
  border-color: var(--green);
}
.row3 {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr;
  gap: 12px;
}
.attachment {
  gap: 0 !important;
}
.upload-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px dashed var(--line2);
  border-radius: 6px;
  background: var(--field-soft);
  cursor: pointer;
}
.upload-box:hover {
  border-color: var(--green);
}
.hidden-file {
  display: none;
}
.upload-text {
  color: var(--dim);
}
.file-name {
  overflow: hidden;
  color: var(--cyan);
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-remove {
  flex-shrink: 0;
  color: var(--red);
  font-size: 12px;
}
.error {
  margin-top: 12px;
  color: var(--red);
  font-size: 13px;
}
.d-ops {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}
.done {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 26px 12px 14px;
  text-align: center;
}
.done-mark {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  margin-bottom: 14px;
  border: 1px solid var(--green);
  border-radius: 50%;
  color: var(--green);
  font-size: 22px;
  font-weight: 800;
  box-shadow: 0 0 18px rgba(var(--green-rgb), 0.18);
}
.done h3 {
  margin-bottom: 8px;
  color: var(--text-strong);
  font-size: 19px;
}
.done p {
  margin-bottom: 22px;
  color: var(--muted);
  font-size: 13px;
}
@media (max-width: 620px) {
  .row3 {
    grid-template-columns: 1fr;
  }
  .dialog {
    padding: 18px;
  }
  .d-head {
    flex-direction: column;
    gap: 4px;
  }
}
</style>
