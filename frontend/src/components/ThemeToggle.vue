<template>
  <div ref="root" class="theme-wrap">
    <button
      class="theme-btn"
      type="button"
      :title="`主题：${currentLabel}`"
      :aria-label="`主题：${currentLabel}`"
      @click.stop="open = !open"
    >
      <svg v-if="theme.preference === 'system'" viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
        <rect x="3" y="4" width="18" height="13" rx="2" stroke="currentColor" stroke-width="1.7" />
        <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
      </svg>
      <svg v-else-if="theme.preference === 'light'" viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
        <circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="1.7" />
        <path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
      </svg>
      <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
        <path d="M20.4 15.2A8.5 8.5 0 0 1 8.8 3.6 8.5 8.5 0 1 0 20.4 15.2Z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" />
      </svg>
    </button>

    <div v-if="open" class="theme-menu" @click.stop>
      <div class="theme-head">显示模式</div>
      <button
        v-for="option in options"
        :key="option.value"
        class="theme-option"
        :class="{ active: theme.preference === option.value }"
        type="button"
        @click="choose(option.value)"
      >
        <span class="option-marker"></span>
        <span class="option-copy">
          <b>{{ option.label }}</b>
          <small>{{ option.desc }}</small>
        </span>
        <span v-if="theme.preference === option.value" class="option-check">✓</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useThemeStore, type ThemePreference } from '../stores/theme'

const theme = useThemeStore()
const root = ref<HTMLElement | null>(null)
const open = ref(false)

const options: { value: ThemePreference; label: string; desc: string }[] = [
  { value: 'system', label: '跟随系统', desc: '随设备外观自动切换' },
  { value: 'light', label: '白天模式', desc: '明亮背景与深色文字' },
  { value: 'dark', label: '黑夜模式', desc: '暗色终端界面' },
]

const currentLabel = computed(
  () => options.find((item) => item.value === theme.preference)?.label ?? '跟随系统',
)

function choose(value: ThemePreference) {
  theme.setPreference(value)
  open.value = false
}

function closeOnOutside(event: MouseEvent) {
  if (!open.value) return
  if (root.value && !root.value.contains(event.target as Node)) open.value = false
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') open.value = false
}

onMounted(() => {
  theme.init()
  document.addEventListener('click', closeOnOutside)
  document.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeOnOutside)
  document.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.theme-wrap {
  position: relative;
}
.theme-btn {
  display: grid;
  place-items: center;
  width: 36px;
  height: 34px;
  padding: 0;
  border: 1px solid var(--line2);
  border-radius: 6px;
  background: var(--panel);
  color: var(--muted);
  cursor: pointer;
  transition: 0.15s;
}
.theme-btn:hover {
  border-color: var(--green);
  color: var(--green);
  background: var(--panel-translucent);
}
.theme-menu {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 121;
  width: 232px;
  padding: 6px;
  border: 1px solid var(--line2);
  border-radius: 8px;
  background: var(--panel);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.3);
}
.theme-head {
  padding: 8px 10px 7px;
  color: var(--dim);
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 1px;
}
.theme-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 9px 10px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--text);
  text-align: left;
  cursor: pointer;
}
.theme-option:hover {
  background: rgba(var(--green-rgb), 0.06);
}
.theme-option.active {
  background: rgba(var(--green-rgb), 0.08);
}
.option-marker {
  flex-shrink: 0;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--line2);
}
.theme-option.active .option-marker {
  background: var(--green);
  box-shadow: 0 0 8px rgba(var(--green-rgb), 0.5);
}
.option-copy {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 1px;
}
.option-copy b {
  color: var(--text-strong);
  font-size: 13px;
  font-weight: 700;
}
.option-copy small {
  color: var(--muted);
  font-size: 10px;
}
.option-check {
  color: var(--green);
  font-size: 12px;
}
</style>
