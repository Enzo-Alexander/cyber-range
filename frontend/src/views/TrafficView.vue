<template>
  <div class="traffic-page">
    <div class="traffic-toolbar">
      <div class="tb-left">
        <span class="ok">◈ 流量分析器</span>
        <span class="dim" style="margin-left:12px">模拟用户 ↔ 服务器通信</span>
      </div>
      <div class="tb-right">
        <button v-if="modalPackets.length > 0 && !modalVisible" class="btn ghost" @click="restoreModal">
          📋 查看上次捕获
        </button>
        <label class="upload-btn" style="margin-left:8px">
          <input type="file" @change="onUpload" hidden />
          <span>📤 上传文件捕获流量</span>
        </label>
        <button class="btn ghost" style="margin-left:8px" :disabled="loading" @click="load">
          {{ loading ? '捕获中…' : '示例通信' }}
        </button>
        <span class="dim" style="margin-left:12px">{{ packets.length }} 个报文</span>
      </div>
    </div>

    <!-- 报文列表（上） -->
    <div class="packet-list">
      <table>
        <thead>
          <tr>
            <th class="c-no">No.</th>
            <th class="c-time">Time</th>
            <th class="c-src">Source</th>
            <th class="c-dst">Destination</th>
            <th class="c-proto">Proto</th>
            <th class="c-len">Length</th>
            <th>Info</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="p in packets"
            :key="p.no"
            :class="{ selected: selected?.no === p.no }"
            @click="selected = p"
          >
            <td class="c-no">{{ p.no }}</td>
            <td class="c-time">{{ p.time.toFixed(6) }}</td>
            <td class="c-src">{{ p.src_ip }}<span v-if="p.src_port" class="port">:{{ p.src_port }}</span></td>
            <td class="c-dst">{{ p.dst_ip }}<span v-if="p.dst_port" class="port">:{{ p.dst_port }}</span></td>
            <td class="c-proto" :class="protoClass(p.protocol)">{{ p.protocol }}</td>
            <td class="c-len">{{ p.length }}</td>
            <td class="info">{{ p.info }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 下半部分：字段树 + Hex dump -->
    <div class="lower">
      <!-- 协议字段树（左下） -->
      <div class="field-tree">
        <div v-if="!selected" class="empty-hint">点击上方报文查看协议字段</div>
        <template v-else>
          <div v-for="(f, i) in selected.detail.layers" :key="i" class="field-row" @click="toggleField(i)">
            <span class="arrow">{{ expandedFields.includes(i) ? '▾' : '▸' }}</span>
            <span class="fname">{{ f.name }}</span>
            <span class="fvalue">{{ f.value }}</span>
          </div>
        </template>
      </div>

      <!-- Hex dump（右下） -->
      <div class="hex-view">
        <div class="hex-head">Hex Dump</div>
        <pre v-if="selected" class="hex-pre">{{ selected.hex_dump }}</pre>
        <div v-else class="empty-hint">Hex 数据</div>
      </div>
    </div>

    <!-- 上传捕获弹窗 -->
    <div v-if="modalVisible" class="modal-mask" @click.self="modalVisible = false">
      <div
        class="modal-box"
        :style="{ left: modalPos.x + 'px', top: modalPos.y + 'px' }"
        ref="modalBox"
      >
        <div class="modal-head" @mousedown="startDrag">
          <span class="ok">◈ 上传流量捕获</span>
          <span class="dim">{{ modalPackets.length }} 个报文</span>
          <span class="close" @click="modalVisible = false">✕</span>
        </div>
        <div class="modal-body">
          <table class="mini-table">
            <thead>
              <tr>
                <th class="c-no">No.</th>
                <th class="c-time">Time</th>
                <th class="c-src">Source</th>
                <th class="c-dst">Destination</th>
                <th class="c-proto">Proto</th>
                <th class="c-len">Len</th>
                <th>Info</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="p in modalPackets"
                :key="p.no"
                :class="{ selected: modalSelected?.no === p.no }"
                @click="modalSelected = p"
              >
                <td class="c-no">{{ p.no }}</td>
                <td class="c-time">{{ p.time.toFixed(6) }}</td>
                <td class="c-src">{{ p.src_ip }}<span v-if="p.src_port" class="port">:{{ p.src_port }}</span></td>
                <td class="c-dst">{{ p.dst_ip }}<span v-if="p.dst_port" class="port">:{{ p.dst_port }}</span></td>
                <td class="c-proto" :class="protoClass(p.protocol)">{{ p.protocol }}</td>
                <td class="c-len">{{ p.length }}</td>
                <td class="info">{{ p.info }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="modalSelected" class="modal-detail">
            <div class="modal-fields">
              <div v-for="(f, i) in modalSelected.detail.layers" :key="i" class="field-row">
                <span class="arrow">▾</span>
                <span class="fname">{{ f.name }}</span>
                <span class="fvalue">{{ f.value }}</span>
              </div>
            </div>
            <pre class="modal-hex">{{ modalSelected.hex_dump }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { http } from '../api/client'

interface PacketField {
  name: string
  value: string
  detail: string
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
  detail: { layers: PacketField[] }
  hex_dump: string
}

const packets = ref<Packet[]>([])
const selected = ref<Packet | null>(null)
const loading = ref(false)
const expandedFields = ref<number[]>([])

// 上传捕获弹窗
const modalVisible = ref(false)
const modalPackets = ref<Packet[]>([])
const modalSelected = ref<Packet | null>(null)
const modalPos = ref({ x: 0, y: 0 })
const dragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })

function startDrag(e: MouseEvent) {
  dragging.value = true
  dragOffset.value = {
    x: e.clientX - modalPos.value.x,
    y: e.clientY - modalPos.value.y,
  }
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}
function onDrag(e: MouseEvent) {
  if (!dragging.value) return
  modalPos.value = {
    x: e.clientX - dragOffset.value.x,
    y: e.clientY - dragOffset.value.y,
  }
}
function stopDrag() {
  dragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

function restoreModal() {
  modalVisible.value = true
}

function protoClass(proto: string) {
  return { TCP: 'tcp', UDP: 'udp', HTTP: 'http', DNS: 'dns' }[proto] || ''
}

function toggleField(i: number) {
  const idx = expandedFields.value.indexOf(i)
  if (idx >= 0) expandedFields.value.splice(idx, 1)
  else expandedFields.value.push(i)
}

async function load() {
  loading.value = true
  try {
    packets.value = await http.get<Packet[]>('/traffic/capture')
    selected.value = packets.value[0] || null
    expandedFields.value = packets.value[0]?.detail.layers.map((_, i) => i) || []
  } catch (e) {
    alert('加载失败: ' + (e as Error).message)
  } finally {
    loading.value = false
  }
}

async function onUpload(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  loading.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    modalPackets.value = await http.postForm<Packet[]>('/traffic/upload-capture', fd)
    modalSelected.value = modalPackets.value[0] || null
    // 弹窗初始居中
    modalPos.value = {
      x: (window.innerWidth - 1200) / 2,
      y: (window.innerHeight - 680) / 2,
    }
    modalVisible.value = true
  } catch (e) {
    alert('上传捕获失败: ' + (e as Error).message)
  } finally {
    loading.value = false
    input.value = ''
  }
}

onMounted(load)
</script>

<style scoped>
.traffic-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: calc(100vh - 120px);
  min-height: 600px;
}
.traffic-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.tb-left { font-family: var(--mono); font-size: 14px; }
.tb-left .ok { color: var(--green); }
.tb-right { display: flex; align-items: center; }
.dim { color: var(--dim); font-size: 13px; }
.upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: rgba(0, 255, 159, 0.1);
  border: 1px solid var(--green);
  border-radius: 6px;
  color: var(--green);
  font-size: 13px;
  cursor: pointer;
  transition: 0.15s;
}
.upload-btn:hover {
  background: rgba(0, 255, 159, 0.2);
  box-shadow: 0 0 12px rgba(0, 255, 159, 0.2);
}

/* 报文列表 */
.packet-list {
  flex: 1;
  min-height: 200px;
  overflow: auto;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.packet-list table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--mono);
  font-size: 12px;
}
.packet-list thead th {
  position: sticky;
  top: 0;
  background: var(--panel2);
  color: var(--muted);
  text-align: left;
  padding: 8px 10px;
  border-bottom: 1px solid var(--line);
  font-weight: 600;
  z-index: 1;
}
.packet-list tbody tr {
  cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.03);
}
.packet-list tbody tr:hover { background: rgba(0, 255, 159, 0.04); }
.packet-list tbody tr.selected { background: rgba(0, 224, 255, 0.1); border-left: 3px solid var(--cyan); }
.packet-list td { padding: 6px 10px; color: var(--text); }
.c-no { width: 50px; color: var(--dim); }
.c-time { width: 80px; color: var(--muted); }
.c-src { width: 130px; }
.c-dst { width: 130px; }
.c-proto { width: 60px; font-weight: 700; }
.c-proto.tcp { color: var(--green); }
.c-proto.udp { color: var(--amber); }
.c-proto.http { color: var(--cyan); }
.c-proto.dns { color: #ff7ab8; }
.c-len { width: 60px; color: var(--muted); }
.port { color: var(--dim); font-size: 11px; }
.info { color: var(--text); }

/* 下半部分 */
.lower {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  min-height: 200px;
}
.field-tree, .hex-view {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: auto;
  padding: 10px;
}
.field-row {
  display: flex;
  gap: 8px;
  padding: 5px 8px;
  font-family: var(--mono);
  font-size: 12px;
  cursor: pointer;
  border-radius: 4px;
}
.field-row:hover { background: rgba(0, 255, 159, 0.05); }
.field-row .arrow { color: var(--cyan); width: 16px; flex-shrink: 0; }
.fname { color: var(--green); font-weight: 600; min-width: 200px; }
.fvalue { color: var(--text); }

.hex-head {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--muted);
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 8px;
}
.hex-pre {
  font-family: var(--mono);
  font-size: 12px;
  line-height: 1.6;
  color: var(--amber);
  white-space: pre;
}
.empty-hint {
  text-align: center;
  color: var(--dim);
  padding: 30px;
  font-size: 13px;
  font-family: var(--mono);
}

/* 上传捕获弹窗 */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(4, 10, 15, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.modal-box {
  position: fixed;
  width: 1200px;
  max-width: 96vw;
  height: 680px;
  max-height: 92vh;
  background: var(--panel);
  border: 1px solid var(--green);
  box-shadow: 0 0 40px rgba(0, 255, 159, 0.15);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.modal-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
  font-family: var(--mono);
  font-size: 14px;
  cursor: move;
  user-select: none;
}
.modal-head .ok { color: var(--green); }
.modal-head .dim { color: var(--dim); font-size: 12px; }
.modal-head .close {
  margin-left: auto;
  cursor: pointer;
  color: var(--dim);
  font-size: 16px;
  padding: 2px 8px;
}
.modal-head .close:hover { color: var(--red); }
.modal-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.mini-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--mono);
  font-size: 11px;
  display: block;
  max-height: 280px;
  overflow-y: auto;
}
.mini-table thead, .mini-table tbody { display: table; width: 100%; table-layout: fixed; }
.mini-table th {
  text-align: left;
  padding: 6px 8px;
  background: var(--panel2);
  color: var(--muted);
  border-bottom: 1px solid var(--line);
  font-weight: 600;
  position: sticky;
  top: 0;
}
.mini-table td { padding: 5px 8px; border-bottom: 1px solid rgba(255,255,255,0.03); }
.mini-table tbody tr { cursor: pointer; }
.mini-table tbody tr:hover { background: rgba(0, 255, 159, 0.04); }
.mini-table tbody tr.selected { background: rgba(0, 224, 255, 0.1); }
.modal-detail {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  border-top: 1px solid var(--line);
  overflow: hidden;
}
.modal-fields {
  padding: 10px 14px;
  border-right: 1px solid var(--line);
  overflow: auto;
}
.modal-fields .field-row {
  display: flex;
  gap: 10px;
  padding: 6px 0;
  font-family: var(--mono);
  font-size: 12px;
  align-items: baseline;
}
.modal-fields .fname {
  color: var(--green);
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
  min-width: 280px;
}
.modal-fields .fvalue {
  color: var(--text);
  flex: 1;
}
.modal-hex {
  padding: 10px 14px;
  font-family: var(--mono);
  font-size: 12px;
  color: var(--amber);
  white-space: pre;
  overflow: auto;
  margin: 0;
}
</style>
