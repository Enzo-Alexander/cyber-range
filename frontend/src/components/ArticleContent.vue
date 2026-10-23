<template>
  <div class="article-content" v-html="rendered"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ content: string }>()

const rendered = computed(() => {
  let html = escapeHtml(props.content)
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" />')
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/\n/g, '<br>')
  return html
})

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}
</script>

<style scoped>
.article-content {
  color: var(--text);
  font-size: 15px;
  line-height: 1.9;
  overflow-wrap: anywhere;
}
.article-content :deep(img) {
  max-width: 100%;
  margin: 16px 0;
  border: 1px solid var(--line);
  border-radius: 8px;
}
.article-content :deep(h2) {
  margin: 20px 0 10px;
  padding-left: 10px;
  border-left: 3px solid var(--green);
  color: var(--text-strong);
  font-size: 18px;
}
.article-content :deep(h3) {
  margin: 16px 0 8px;
  color: var(--cyan);
  font-size: 16px;
}
</style>
