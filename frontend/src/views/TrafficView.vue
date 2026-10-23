<template>
  <div class="traffic-page">
    <!-- 工具条 -->
    <div class="traffic-toolbar">
      <div class="tb-left">
        <span class="title">◈ 流量分析器</span>
        <span class="source-badge" :class="source.kind">
          {{ source.kind === 'upload' ? `上传文件：${source.name}` : '示例通信' }}
        </span>
        <span v-if="source.kind === 'upload' && source.size" class="dim">
          {{ formatSize(source.size) }}
        </span>
      </div>
      <div class="tb-right">
        <label class="display-filter">
          <input
            v-model="filter"
            placeholder="显示过滤器：http / tcp / dns / 10.0.0.5"
            spellcheck="false"
          />
          <button v-if="filter" class="clear" title="清除过滤器" @click="filter = ''">✕</button>
        </label>
        <label class="upload-btn">
          <input type="file" hidden @change="onUpload" />
          <span>上传文件捕获流量</span>
        </label>
        <button class="btn ghost" :disabled="loading" title="加载示例通信" @click="load">
          {{ loading ? '捕获中…' : '示例通信' }}
        </button>
      </div>
    </div>

    <p v-if="errorMsg" class="err">{{ errorMsg }}</p>

    <div ref="stackRef" class="pane-stack">
    <!-- 报文列表 -->
    <section class="pane packet-list" :style="{ height: `${listH}px` }">
      <header class="pane-head">
        <span class="pane-title">报文列表</span>
        <span class="dim">{{ filteredPackets.length }} / {{ packets.length }} 个报文</span>
      </header>
      <div class="pane-body">
        <table>
          <thead>
            <tr>
              <th class="c-no">No.</th>
              <th class="c-time">Time</th>
              <th class="c-src">Source</th>
              <th class="c-dst">Destination</th>
              <th class="c-proto">Protocol</th>
              <th class="c-len">Length</th>
              <th class="c-info">Info</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="p in filteredPackets"
              :key="p.no"
              :class="['row', protoClass(p.protocol), { selected: selected?.no === p.no }]"
              @click="selectPacket(p)"
            >
              <td class="c-no">{{ p.no }}</td>
              <td class="c-time">{{ p.time.toFixed(6) }}</td>
              <td class="c-src">
                {{ p.src_ip }}<span v-if="p.src_port" class="port">:{{ p.src_port }}</span>
              </td>
              <td class="c-dst">
                {{ p.dst_ip }}<span v-if="p.dst_port" class="port">:{{ p.dst_port }}</span>
              </td>
              <td class="c-proto">{{ p.protocol }}</td>
              <td class="c-len">{{ p.length }}</td>
              <td class="c-info">{{ p.info }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="!filteredPackets.length" class="empty-hint">没有匹配的报文</div>
      </div>
    </section>

    <div
      class="splitter"
      role="separator"
      aria-orientation="horizontal"
      aria-label="调整报文列表与报文详情的高度"
      tabindex="0"
      title="上下拖动调整显示框大小，双击复位"
      @pointerdown="startDrag('list', $event)"
      @pointermove="onDrag"
      @pointerup="endDrag"
      @pointercancel="endDrag"
      @keydown="onSplitterKey('list', $event)"
      @dblclick="resetLayout"
    >
      <span class="grip"></span>
    </div>

    <!-- 报文详情（协议字段树） -->
    <section class="pane packet-detail" :style="{ height: `${detailH}px` }">
      <header class="pane-head">
        <span class="pane-title">报文详情</span>
        <span class="dim">
          {{ selected ? `Frame ${selected.no} · ${selected.length} bytes` : '未选择报文' }}
        </span>
        <span class="spacer"></span>
        <button class="mini" :disabled="!selected" title="展开全部字段" @click="expandAll">展开</button>
        <button class="mini" :disabled="!selected" title="折叠全部字段" @click="collapseAll">折叠</button>
      </header>
      <div class="pane-body tree">
        <div v-if="!selected" class="empty-hint">点击上方报文查看协议字段</div>
        <template v-else>
          <div
            v-for="row in rows"
            :key="row.id"
            class="field-row"
            :class="{ focused: focusedField === row.node }"
            :style="{ paddingLeft: 8 + row.depth * 16 + 'px' }"
            @click="onFieldClick(row)"
          >
            <span class="arrow">{{ row.hasChildren ? (row.expanded ? '▾' : '▸') : '' }}</span>
            <span class="fname" :class="{ layer: row.depth === 0 }">{{ row.node.name }}</span>
            <span v-if="row.node.value" class="fvalue">{{ row.node.value }}</span>
          </div>
        </template>
      </div>
    </section>

    <div
      class="splitter"
      role="separator"
      aria-orientation="horizontal"
      aria-label="调整报文详情与报文字节的高度"
      tabindex="0"
      title="上下拖动调整显示框大小，双击复位"
      @pointerdown="startDrag('detail', $event)"
      @pointermove="onDrag"
      @pointerup="endDrag"
      @pointercancel="endDrag"
      @keydown="onSplitterKey('detail', $event)"
      @dblclick="resetLayout"
    >
      <span class="grip"></span>
    </div>

    <!-- 报文字节（Hex） -->
    <section class="pane packet-bytes">
      <header class="pane-head">
        <span class="pane-title">报文字节</span>
        <span class="dim">{{ focusedLabel }}</span>
      </header>
      <div class="pane-body hex">
        <div v-if="!selected" class="empty-hint">Hex 数据</div>
        <div v-else class="hex-grid">
          <div v-for="(line, li) in selected.hex_lines" :key="line.offset" class="hex-line">
            <span class="hex-offset">{{ line.offset }}</span>
            <span class="hex-track">
              <span
                v-for="(hx, bi) in line.hex_bytes"
                :key="bi"
                class="cell"
                :class="{ hl: isHighlighted(li * 16 + bi) }"
              >{{ hx }}</span>
            </span>
            <span class="hex-track ascii">
              <span
                v-for="(ch, bi) in line.ascii.split('')"
                :key="bi"
                class="cell"
                :class="{ hl: isHighlighted(li * 16 + bi) }"
              >{{ ch }}</span>
            </span>
          </div>
        </div>
      </div>
    </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { http } from '../api/client'

interface FieldNode {
  name: string
  value: string
  start: number | null
  length: number | null
  children: FieldNode[]
}

interface HexLine {
  offset: string
  hex_bytes: string[]
  ascii: string
}

interface Packet {
  no: number
  time: number
  src_ip: string
  dst_ip: string
  src_port: number | null
  dst_port: number | null
  protocol: string
  length: number
  info: string
  fields: FieldNode[]
  hex_lines: HexLine[]
}

interface TreeRow {
  id: string
  depth: number
  node: FieldNode
  hasChildren: boolean
  expanded: boolean
}

const packets = ref<Packet[]>([])
const selected = ref<Packet | null>(null)
const loading = ref(false)
const filter = ref('')
const errorMsg = ref('')
const source = ref<{ kind: 'sample' | 'upload'; name?: string; size?: number }>({ kind: 'sample' })

const expanded = ref<Set<string>>(new Set())
const focusedField = ref<FieldNode | null>(null)

// ---- 三个显示框的高度：列表与详情用像素高度，报文字节区自适剩余空间 ----
const SPLITTER = 10
const MIN_PANE = 76
const stackRef = ref<HTMLElement | null>(null)
const listH = ref(220)
const detailH = ref(280)
let dragState: { which: 'list' | 'detail'; startY: number; list: number; detail: number } | null = null
let observer: ResizeObserver | null = null
let initialized = false

function availableHeight() {
  const stack = stackRef.value
  return stack ? stack.clientHeight - SPLITTER * 2 : 0
}

/** 保证三个框都不小于最小高度，且总和不超出可用高度。 */
function sanitize() {
  const available = availableHeight()
  if (available <= MIN_PANE * 3) return
  const maxPair = available - MIN_PANE
  let list = Math.max(MIN_PANE, listH.value)
  let detail = Math.max(MIN_PANE, detailH.value)
  if (list + detail > maxPair) {
    detail -= Math.min(list + detail - maxPair, detail - MIN_PANE)
    list = Math.min(list, maxPair - detail)
  }
  listH.value = Math.max(MIN_PANE, Math.min(list, maxPair - MIN_PANE))
  detailH.value = Math.max(MIN_PANE, Math.min(detail, maxPair - listH.value))
}

function computeDefaults() {
  const available = availableHeight()
  if (available <= MIN_PANE * 3) return
  listH.value = Math.round(available * 0.31)
  detailH.value = Math.round(available * 0.39)
  sanitize()
}

function resetLayout() {
  computeDefaults()
}

function startDrag(which: 'list' | 'detail', event: PointerEvent) {
  const target = event.currentTarget as HTMLElement
  target.setPointerCapture(event.pointerId)
  dragState = { which, startY: event.clientY, list: listH.value, detail: detailH.value }
  event.preventDefault()
}

function applyDelta(which: 'list' | 'detail', delta: number, base: { list: number; detail: number }) {
  if (which === 'list') {
    // 拖动列表/详情之间的分隔条：两者高度此消彼长
    const total = base.list + base.detail
    const next = Math.min(Math.max(base.list + delta, MIN_PANE), total - MIN_PANE)
    listH.value = next
    detailH.value = total - next
  } else {
    // 拖动详情/字节之间的分隔条：详情变高，字节区自动收缩
    const maxDetail = availableHeight() - listH.value - MIN_PANE
    detailH.value = Math.min(Math.max(base.detail + delta, MIN_PANE), Math.max(MIN_PANE, maxDetail))
  }
  sanitize()
}

function onDrag(event: PointerEvent) {
  if (!dragState) return
  applyDelta(dragState.which, event.clientY - dragState.startY, dragState)
}

function endDrag(event: PointerEvent) {
  const target = event.currentTarget as HTMLElement
  if (target.hasPointerCapture(event.pointerId)) target.releasePointerCapture(event.pointerId)
  dragState = null
}

function onSplitterKey(which: 'list' | 'detail', event: KeyboardEvent) {
  if (event.key !== 'ArrowUp' && event.key !== 'ArrowDown') return
  const step = event.shiftKey ? 48 : 16
  applyDelta(which, event.key === 'ArrowDown' ? step : -step, {
    list: listH.value,
    detail: detailH.value,
  })
  event.preventDefault()
}

const filteredPackets = computed(() => {
  const query = filter.value.trim().toLowerCase()
  if (!query) return packets.value
  return packets.value.filter(
    (p) =>
      p.protocol.toLowerCase().includes(query) ||
      p.info.toLowerCase().includes(query) ||
      p.src_ip.includes(query) ||
      p.dst_ip.includes(query) ||
      String(p.src_port ?? '').includes(query) ||
      String(p.dst_port ?? '').includes(query)
  )
})

const rows = computed<TreeRow[]>(() => {
  const out: TreeRow[] = []
  const walk = (nodes: FieldNode[], depth: number, prefix: string) => {
    nodes.forEach((node, i) => {
      const id = prefix ? `${prefix}.${i}` : String(i)
      const hasChildren = node.children.length > 0
      const isOpen = expanded.value.has(id)
      out.push({ id, depth, node, hasChildren, expanded: isOpen })
      if (hasChildren && isOpen) walk(node.children, depth + 1, id)
    })
  }
  walk(selected.value?.fields ?? [], 0, '')
  return out
})

const focusRange = computed<[number, number] | null>(() => {
  const field = focusedField.value
  if (!field || field.start == null || !field.length) return null
  return [field.start, field.start + field.length]
})

const focusedLabel = computed(() => {
  const field = focusedField.value
  if (!field) return '选中字段后高亮对应字节'
  const text = field.value ? `${field.name}: ${field.value}` : field.name
  return text.length > 90 ? `${text.slice(0, 90)}…` : text
})

function isHighlighted(index: number) {
  const range = focusRange.value
  return !!range && index >= range[0] && index < range[1]
}

function protoClass(proto: string) {
  return { TCP: 'tcp', UDP: 'udp', DNS: 'dns', HTTP: 'http' }[proto] || 'other'
}

function formatSize(size?: number) {
  if (!size) return ''
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function selectPacket(packet: Packet) {
  selected.value = packet
  focusedField.value = null
  expanded.value = new Set(packet.fields.map((_, i) => String(i)))
}

function onFieldClick(row: TreeRow) {
  if (row.hasChildren) {
    const next = new Set(expanded.value)
    if (next.has(row.id)) next.delete(row.id)
    else next.add(row.id)
    expanded.value = next
  }
  focusedField.value = row.node
}

function expandAll() {
  const all = new Set<string>()
  const walk = (nodes: FieldNode[], prefix: string) => {
    nodes.forEach((node, i) => {
      const id = prefix ? `${prefix}.${i}` : String(i)
      if (node.children.length) {
        all.add(id)
        walk(node.children, id)
      }
    })
  }
  walk(selected.value?.fields ?? [], '')
  expanded.value = all
}

function collapseAll() {
  expanded.value = new Set()
}

async function load() {
  loading.value = true
  errorMsg.value = ''
  try {
    packets.value = await http.get<Packet[]>('/traffic/capture')
    source.value = { kind: 'sample' }
    filter.value = ''
    if (packets.value.length) selectPacket(packets.value[0])
  } catch (e) {
    errorMsg.value = `加载失败: ${(e as Error).message}`
  } finally {
    loading.value = false
  }
}

async function onUpload(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  loading.value = true
  errorMsg.value = ''
  try {
    const form = new FormData()
    form.append('file', file)
    const captured = await http.postForm<Packet[]>('/traffic/upload-capture', form)
    packets.value = captured
    source.value = { kind: 'upload', name: file.name, size: file.size }
    filter.value = ''
    if (captured.length) selectPacket(captured[0])
  } catch (e) {
    errorMsg.value = `上传捕获失败: ${(e as Error).message}`
  } finally {
    loading.value = false
    input.value = ''
  }
}

onMounted(() => {
  load()
  const stack = stackRef.value
  if (!stack) return
  observer = new ResizeObserver(() => {
    if (!initialized) {
      if (stack.clientHeight > 0) {
        computeDefaults()
        initialized = true
      }
      return
    }
    sanitize()
  })
  observer.observe(stack)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
  dragState = null
})
</script>

<style scoped>
.traffic-page {
  display: flex;
  flex-direction: column;
  gap: 10px;
  /* 顶部导航(60) + 容器上下内边距(28×2) + 底部状态栏(37) ≈ 152 */
  height: calc(100vh - 154px);
  min-height: 460px;
}

/* ---------- 工具条 ---------- */
.traffic-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.tb-left,
.tb-right {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.tb-left .title {
  font-family: var(--mono);
  font-size: 14px;
  color: var(--green);
}
.source-badge {
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-family: var(--mono);
  border: 1px solid var(--line2);
  color: var(--muted);
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.source-badge.upload {
  color: var(--cyan);
  border-color: rgba(var(--cyan-rgb), 0.5);
  background: rgba(var(--cyan-rgb), 0.08);
}
.dim {
  color: var(--dim);
  font-size: 12px;
  font-family: var(--mono);
}
.display-filter {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px 4px 10px;
  background: var(--bg2);
  border: 1px solid var(--line2);
  border-radius: 6px;
}
.display-filter:focus-within {
  border-color: var(--green);
}
.display-filter input {
  width: 260px;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text);
  font-family: var(--mono);
  font-size: 12px;
}
.display-filter .clear {
  background: none;
  border: none;
  color: var(--dim);
  cursor: pointer;
  font-size: 12px;
  padding: 0 2px;
}
.display-filter .clear:hover {
  color: var(--red);
}
.upload-btn {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  background: rgba(var(--green-rgb), 0.1);
  border: 1px solid var(--green);
  border-radius: 6px;
  color: var(--green);
  font-size: 13px;
  cursor: pointer;
  transition: 0.15s;
}
.upload-btn:hover {
  background: rgba(var(--green-rgb), 0.2);
  box-shadow: 0 0 12px rgba(var(--green-rgb), 0.2);
}
.err {
  margin: 0;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--red);
  background: rgba(var(--red-rgb), 0.12);
  border: 1px solid rgba(var(--red-rgb), 0.5);
  border-radius: 6px;
}

/* ---------- 分栏 ---------- */
.pane-stack {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.pane {
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
}
.packet-list,
.packet-detail {
  flex: 0 0 auto; /* 高度由拖动分隔条决定 */
}
.packet-bytes {
  flex: 1 1 auto;
  min-height: 0;
}

/* ---------- 可拖动分隔条 ---------- */
.splitter {
  position: relative;
  flex: 0 0 auto;
  height: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: row-resize;
  touch-action: none;
  user-select: none;
  background: transparent;
}
.splitter::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 1px;
  background: var(--line);
}
.splitter .grip {
  position: relative;
  width: 52px;
  height: 4px;
  border-radius: 3px;
  background: var(--line2);
  transition: background 0.15s, box-shadow 0.15s;
}
.splitter:hover .grip,
.splitter:focus-visible .grip {
  background: var(--green);
  box-shadow: 0 0 10px rgba(var(--green-rgb), 0.45);
}
.splitter:focus-visible {
  outline: none;
}
.pane-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  background: var(--panel2);
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}
.pane-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
}
.pane-head .spacer { margin-left: auto; }
.mini {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid var(--line2);
  background: transparent;
  color: var(--muted);
  cursor: pointer;
}
.mini:hover:not(:disabled) {
  color: var(--green);
  border-color: var(--green);
}
.mini:disabled {
  opacity: 0.4;
  cursor: default;
}
.pane-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

/* ---------- 报文列表 ---------- */
.packet-list table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--mono);
  font-size: 12px;
}
.packet-list thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: var(--panel2);
  color: var(--muted);
  text-align: left;
  padding: 7px 10px;
  border-bottom: 1px solid var(--line);
  font-weight: 600;
}
.packet-list td {
  padding: 5px 10px;
  color: var(--text);
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
  white-space: nowrap;
}
.row { cursor: pointer; border-left: 3px solid transparent; }
.row.tcp { background: rgba(136, 116, 216, 0.1); }
.row.udp { background: rgba(90, 160, 255, 0.09); }
.row.dns { background: rgba(90, 160, 255, 0.14); }
.row.http { background: rgba(var(--green-rgb), 0.07); }
.row:hover { background: rgba(var(--cyan-rgb), 0.12); }
.row.selected {
  background: rgba(var(--cyan-rgb), 0.2);
  border-left-color: var(--cyan);
}
.c-no { width: 56px; color: var(--dim); }
.c-time { width: 92px; color: var(--muted); }
.c-src, .c-dst { width: 150px; }
.c-proto { width: 78px; font-weight: 700; }
.row.tcp .c-proto { color: var(--green); }
.row.udp .c-proto { color: var(--amber); }
.row.dns .c-proto { color: var(--cyan); }
.row.http .c-proto { color: var(--green); }
.c-len { width: 68px; color: var(--muted); }
.c-info { color: var(--text); }
.port { color: var(--dim); }

/* ---------- 字段树 ---------- */
.tree { padding: 6px 0; }
.field-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 3px 10px;
  font-family: var(--mono);
  font-size: 12px;
  cursor: pointer;
  border-radius: 3px;
}
.field-row:hover { background: rgba(var(--green-rgb), 0.06); }
.field-row.focused { background: rgba(var(--cyan-rgb), 0.16); }
.field-row .arrow {
  width: 12px;
  flex-shrink: 0;
  color: var(--cyan);
}
.fname { color: var(--muted); flex-shrink: 0; }
.fname.layer { color: var(--green); font-weight: 700; }
.fvalue { color: var(--text); word-break: break-all; }

/* ---------- Hex ---------- */
.hex { padding: 8px 12px; }
.hex-grid {
  font-family: var(--mono);
  font-size: 12px;
  line-height: 1.7;
  display: inline-block;
  min-width: 100%;
}
.hex-line { display: flex; gap: 14px; white-space: nowrap; }
.hex-offset { color: var(--dim); flex-shrink: 0; }
.hex-track {
  display: grid;
  grid-template-columns: repeat(16, 2ch);
  column-gap: 5px;
}
.hex-track.ascii { color: var(--muted); }
.hex-track .cell { text-align: center; border-radius: 2px; }
.hex-track.ascii .cell { text-align: left; }
.hex-track .cell.hl {
  background: rgba(var(--cyan-rgb), 0.32);
  color: var(--text-strong);
}

.empty-hint {
  padding: 26px;
  text-align: center;
  color: var(--dim);
  font-size: 13px;
  font-family: var(--mono);
}

@media (max-width: 900px) {
  .traffic-toolbar { flex-direction: column; align-items: stretch; }
  .display-filter input { width: 100%; }
  .display-filter { flex: 1; }
}
</style>
