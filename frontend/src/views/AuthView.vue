<template>
  <div class="auth-page">
    <!-- 背景：左侧绿色代码流 + 右侧彩色网络拓扑 -->
    <div class="auth-bg" aria-hidden="true">
      <div class="bg-grid"></div>
      <div class="bg-glow"></div>
      <div class="bg-scan"></div>
      <div class="bg-noise"></div>

      <pre class="bg-code"><code><span class="dim"># network forensics / packet analysis</span>
<span class="c">import</span> socket, struct, ssl, json, hashlib
<span class="c">from</span> scapy.all <span class="c">import</span> sniff, IP, TCP, Raw, hexdump

<span class="c">def</span> <span class="fn">parse_pcap</span>(path, max_frames=1000):
    stream = <span class="fn">open</span>(path, <span class="s">'rb'</span>)
    <span class="c">for</span> frame <span class="c">in</span> <span class="fn">iter_frames</span>(stream):
        eth  = <span class="fn">decode_ethernet</span>(frame.payload)          <span class="dim"># Ethernet II header</span>
        ipv4 = <span class="fn">decode_ipv4</span>(eth.payload, version=4)      <span class="dim"># IPv4 protocol fields</span>
        tcp  = <span class="fn">decode_tcp</span>(ipv4.payload, window=8192)     <span class="dim"># TCP segment fields</span>
        <span class="y">yield</span> {<span class="s">'src'</span>: ipv4.src, <span class="s">'dst'</span>: ipv4.dst,
               <span class="s">'sport'</span>: tcp.sport, <span class="s">'dport'</span>: tcp.dport, <span class="s">'seq'</span>: tcp.seq}

<span class="c">class</span> <span class="fn">PacketStream</span>:
    <span class="c">def</span> <span class="fn">__init__</span>(self, iface=<span class="s">'eth0'</span>, filter=<span class="s">'tcp'</span>, promisc=<span class="s">False</span>):
        self.iface, self.filter, self.promisc = iface, filter, promisc

    <span class="c">def</span> <span class="fn">sniff</span>(self, count=0):
        <span class="c">while</span> <span class="fn">capture</span>(self.iface, self.filter):
            pkt = <span class="fn">read_frame</span>(nonblock=<span class="s">True</span>)
            <span class="c">if</span> pkt.flags == <span class="s">'SYN'</span>:                <span class="dim"># three-way handshake</span>
                <span class="fn">handle_handshake</span>(pkt, timeout=<span class="s">0.5</span>)

session = <span class="fn">PacketStream</span>(<span class="s">'eth0'</span>, filter=<span class="s">'tcp and http'</span>)
session.<span class="fn">sniff</span>(count=<span class="s">128</span>)</code></pre>

      <svg class="bg-network" viewBox="0 0 420 420" fill="none" xmlns="http://www.w3.org/2000/svg">
        <!-- 静态链路 -->
        <g class="topo-links">
          <path id="tn1" d="M210 258 L112 92" />
          <path id="tn2" d="M210 258 L306 86" />
          <path id="tn3" d="M210 258 L362 178" />
          <path id="tn4" d="M210 258 L330 358" />
          <path id="tn5" d="M210 258 L214 392" />
          <path id="tn6" d="M210 258 L108 360" />
          <path d="M112 92 L156 170" />
          <path d="M156 170 L108 360" />
          <path d="M306 86 L256 120" />
          <path d="M256 120 L362 178" />
          <path d="M362 178 L330 358" />
          <path d="M330 358 L268 328" />
          <path d="M268 328 L214 392" />
          <path d="M214 392 L108 360" />
          <path d="M112 92 L306 86" />
        </g>

        <!-- 链路上的流光 -->
        <g class="topo-flow">
          <path d="M210 258 L112 92" />
          <path d="M210 258 L306 86" />
          <path d="M210 258 L362 178" />
          <path d="M210 258 L330 358" />
          <path d="M210 258 L214 392" />
          <path d="M210 258 L108 360" />
          <path d="M256 120 L362 178" />
          <path d="M268 328 L214 392" />
        </g>

        <!-- 沿链路移动的数据包 -->
        <g class="topo-pulses">
          <circle r="2.6">
            <animateMotion dur="5.2s" begin="0s" repeatCount="indefinite">
              <mpath href="#tn3"></mpath>
            </animateMotion>
          </circle>
          <circle r="2.2">
            <animateMotion dur="6.4s" begin="-2s" repeatCount="indefinite">
              <mpath href="#tn6"></mpath>
            </animateMotion>
          </circle>
          <circle r="2.2">
            <animateMotion dur="4.6s" begin="-1.2s" repeatCount="indefinite">
              <mpath href="#tn5"></mpath>
            </animateMotion>
          </circle>
        </g>

        <!-- 节点 -->
        <g class="topo-nodes">
          <circle class="halo" cx="210" cy="258" r="14" />

          <circle class="ping p1" cx="112" cy="92" r="4.5" />
          <circle class="dot" cx="112" cy="92" r="3.6" />
          <circle class="ping p2" cx="306" cy="86" r="4.5" />
          <circle class="dot amber" cx="306" cy="86" r="3.6" />
          <circle class="ping p3" cx="362" cy="178" r="4.5" />
          <circle ref="upperNodeRef" class="dot cyan" cx="362" cy="178" r="3.6" />
          <circle class="ping p1" cx="330" cy="358" r="4.5" />
          <circle ref="lowerNodeRef" class="dot" cx="330" cy="358" r="3.6" />
          <circle class="ping p2" cx="214" cy="392" r="4.5" />
          <circle class="dot cyan" cx="214" cy="392" r="3.6" />
          <circle class="ping p3" cx="108" cy="360" r="4.5" />
          <circle class="dot" cx="108" cy="360" r="3.6" />

          <circle class="ping p2" cx="156" cy="170" r="3" />
          <circle class="dot dim" cx="156" cy="170" r="2.6" />
          <circle class="ping p3" cx="268" cy="328" r="3" />
          <circle ref="auxNodeRef" class="dot dim" cx="268" cy="328" r="2.6" />
          <circle class="ping p1" cx="256" cy="120" r="3" />
          <circle ref="aux2NodeRef" class="dot dim" cx="256" cy="120" r="2.6" />

          <circle class="ping p2" cx="210" cy="258" r="7" />
          <circle ref="coreNodeRef" class="dot core" cx="210" cy="258" r="5.5" />
        </g>
      </svg>
    </div>

    <!-- 登录卡片接入网络拓扑的多条链路 -->
    <svg class="merge-link" aria-hidden="true">
      <g v-for="(link, i) in links" :key="i">
        <path class="link-base" :d="link.d" />
        <path
          class="link-flow"
          :d="link.d"
          :style="{ animationDelay: `${-i * 0.7}s` }"
        />
        <circle class="link-port-ring" :cx="link.x" :cy="link.y" r="7" />
        <circle class="link-port" :cx="link.x" :cy="link.y" r="4" />
      </g>
    </svg>

    <div class="auth-theme">
      <ThemeToggle />
    </div>

    <div class="auth-viewport">
      <div class="auth-brand">
        <svg class="shield" viewBox="0 0 72 78" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient :id="shieldGradientId" x1="8" y1="4" x2="64" y2="74" gradientUnits="userSpaceOnUse">
              <stop stop-color="#7ff6ff" />
              <stop offset="0.5" stop-color="#22c8c0" />
              <stop offset="1" stop-color="#0b7f8c" />
            </linearGradient>
          </defs>
          <path d="M36 3 68 14v26c0 18-13 30-32 35C17 70 4 58 4 40V14L36 3Z"
            :stroke="`url(#${shieldGradientId})`" stroke-width="2.5" fill="rgba(20,60,70,0.35)" />
          <path d="M36 16 56 23v15c0 11-8 18-20 22C24 56 16 49 16 38V23L36 16Z"
            stroke="#5fd0c8" stroke-width="1.2" stroke-opacity="0.7" fill="rgba(0,229,200,0.06)" />
          <path d="M36 26v20M28 34h11l6-6M28 42h11l6 6" stroke="#7ff6ff" stroke-width="1.6"
            stroke-linecap="round" fill="none" />
          <circle cx="36" cy="36" r="3" fill="#7ff6ff" />
        </svg>
        <h1 class="brand-name">CYBERRANGE</h1>
        <p class="brand-sub">security training platform</p>
      </div>

      <div class="auth-card-wrap">
        <button type="button" class="switch-btn" @click="toggleMode">
          {{ mode === 'login' ? '切换到注册' : '切换到登录' }}
        </button>

        <div ref="cardRef" class="auth-card">
        <h2 class="auth-title">{{ mode === 'login' ? '登录' : '注册' }}</h2>

        <form class="auth-form" novalidate @submit.prevent="submit">
          <p v-if="error" class="err" role="alert">{{ error }}</p>

          <div class="field">
            <div class="field-head">
              <span>用户名</span>
              <span class="hint">{{ mode === 'login' ? '帐号' : '注册' }}</span>
            </div>
            <label class="input-wrap">
              <svg class="input-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="1.6" stroke-linecap="round">
                <circle cx="12" cy="8" r="3.2" />
                <path d="M5.6 19.4c.7-3.3 3.2-5.1 6.4-5.1s5.7 1.8 6.4 5.1" />
              </svg>
              <input
                ref="usernameInput"
                v-model.trim="username"
                type="text"
                placeholder="用户名"
                autocomplete="username"
              />
            </label>
          </div>

          <div v-if="mode === 'register'" class="field">
            <div class="field-head"><span>邮箱</span></div>
            <label class="input-wrap">
              <svg class="input-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3.5" y="5.5" width="17" height="13" rx="2.5" />
                <path d="m4.5 7 7.5 6 7.5-6" />
              </svg>
              <input v-model.trim="email" type="email" placeholder="邮箱" autocomplete="email" />
            </label>
          </div>

          <div class="field">
            <div class="field-head">
              <span>密码</span>
              <span class="hint">{{ mode === 'login' ? '帐号' : '注册' }}</span>
            </div>
            <label class="input-wrap">
              <svg class="input-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <rect x="4.5" y="10" width="15" height="10" rx="2.5" />
                <path d="M8 10V7.8a4 4 0 0 1 8 0V10" />
              </svg>
              <input
                v-model="password"
                type="password"
                placeholder="密码"
                :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
              />
            </label>
          </div>

          <button class="submit" type="submit" :disabled="loading">
            {{ loading ? '处理中…' : mode === 'login' ? '登录' : '注册' }}
          </button>
        </form>

        <p class="alt">
          {{ mode === 'login' ? '还没有账号？' : '已经有账号了？' }}
          <a href="#" @click.prevent="toggleMode">{{ mode === 'login' ? '注册' : '登录' }}</a>
        </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, useId, watch } from 'vue'
import { useRouter } from 'vue-router'
import ThemeToggle from '../components/ThemeToggle.vue'
import { useAuthStore } from '../stores/auth'

const props = defineProps<{ mode?: string }>()
const router = useRouter()
const auth = useAuthStore()

const mode = ref(props.mode === 'register' ? 'register' : 'login')
watch(
  () => props.mode,
  (m) => {
    mode.value = m === 'register' ? 'register' : 'login'
    error.value = ''
    nextTick(() => {
      usernameInput.value?.focus()
      scheduleLink()
    })
  }
)

const username = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const usernameInput = ref<HTMLInputElement | null>(null)
const shieldGradientId = `shield-edge-${useId()}`

// 卡片与右侧拓扑之间的连接线：按实际屏幕坐标绘制，随布局变化更新
const cardRef = ref<HTMLElement | null>(null)
const coreNodeRef = ref<SVGCircleElement | null>(null)
const upperNodeRef = ref<SVGCircleElement | null>(null)
const lowerNodeRef = ref<SVGCircleElement | null>(null)
const auxNodeRef = ref<SVGCircleElement | null>(null)
const aux2NodeRef = ref<SVGCircleElement | null>(null)
const links = ref<{ d: string; x: number; y: number }[]>([])
let linkObserver: ResizeObserver | null = null
let linkRaf = 0

function updateLink() {
  const card = cardRef.value
  if (!card) {
    links.value = []
    return
  }
  const cr = card.getBoundingClientRect()
  // 从卡片右边缘不同高度引出五条链路，故意打乱上下的对应关系，让链路交叉
  const anchors = [
    { node: lowerNodeRef.value, ratio: 0.18 },
    { node: upperNodeRef.value, ratio: 0.34 },
    { node: coreNodeRef.value, ratio: 0.5 },
    { node: aux2NodeRef.value, ratio: 0.66 },
    { node: auxNodeRef.value, ratio: 0.82 },
  ]
  const next: { d: string; x: number; y: number }[] = []
  for (const { node, ratio } of anchors) {
    // 小屏下拓扑被隐藏，不画连接线
    if (!node || node.getBoundingClientRect().width === 0) continue
    const nr = node.getBoundingClientRect()
    const sx = cr.right
    const sy = cr.top + cr.height * ratio
    const ex = nr.left + nr.width / 2
    const ey = nr.top + nr.height / 2
    if (ex <= sx + 8) continue
    const dx = ex - sx
    const dy = ey - sy
    const cx = sx + dx * 0.42
    // 控制点向连线方向外侧鼓出，避免所有线都朝同一个方向弯
    const cy = sy + dy * 0.5 + (dy >= 0 ? 1 : -1) * Math.min(70, Math.abs(dy) * 0.25)
    next.push({
      d: `M ${sx.toFixed(1)} ${sy.toFixed(1)} Q ${cx.toFixed(1)} ${cy.toFixed(1)} ${ex.toFixed(1)} ${ey.toFixed(1)}`,
      x: Math.round(sx),
      y: Math.round(sy),
    })
  }
  links.value = next
}

function scheduleLink() {
  cancelAnimationFrame(linkRaf)
  // 等布局稳定后再测量，避免读到切换瞬间的旧尺寸
  linkRaf = requestAnimationFrame(() => requestAnimationFrame(updateLink))
}

onMounted(() => {
  usernameInput.value?.focus()
  nextTick(scheduleLink)
  window.addEventListener('resize', scheduleLink)
  if (cardRef.value) {
    linkObserver = new ResizeObserver(scheduleLink)
    linkObserver.observe(cardRef.value)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', scheduleLink)
  linkObserver?.disconnect()
  linkObserver = null
  cancelAnimationFrame(linkRaf)
})

function toggleMode() {
  router.replace(mode.value === 'login' ? '/register' : '/login')
}

async function submit() {
  error.value = ''

  if (!username.value) {
    error.value = '请输入用户名'
    usernameInput.value?.focus()
    return
  }
  if (mode.value === 'register' && !email.value) {
    error.value = '请输入邮箱'
    return
  }
  if (!password.value) {
    error.value = '请输入密码'
    return
  }

  loading.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(username.value, password.value)
    } else {
      await auth.register(username.value, email.value, password.value)
    }
    router.push('/')
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  overflow: hidden;
  background: #04070b;
}
.auth-theme {
  position: fixed;
  z-index: 60;
  top: 26px;
  right: 190px;
}

/* ---------- 背景装饰层 ---------- */
.auth-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(31, 202, 166, 0.055) 1px, transparent 1px),
    linear-gradient(90deg, rgba(31, 202, 166, 0.055) 1px, transparent 1px),
    linear-gradient(rgba(var(--cyan-rgb), 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--cyan-rgb), 0.04) 1px, transparent 1px);
  background-size: 26px 26px, 26px 26px, 130px 130px, 130px 130px;
  mask-image: radial-gradient(ellipse 85% 75% at 50% 45%, #000 32%, transparent 100%);
}
.bg-glow {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(700px 520px at 62% 8%, rgba(31, 202, 166, 0.16), transparent 62%),
    radial-gradient(900px 700px at 76% 82%, rgba(31, 120, 170, 0.1), transparent 68%),
    radial-gradient(760px 620px at 10% 88%, rgba(var(--green-rgb), 0.08), transparent 66%);
}
/* 缓慢下移的扫描光带，给静态背景一点“在线”的感觉 */
.bg-scan {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 16%;
  background: linear-gradient(
    180deg,
    transparent,
    rgba(0, 255, 200, 0.03) 42%,
    rgba(120, 255, 235, 0.065) 50%,
    rgba(0, 255, 200, 0.03) 58%,
    transparent
  );
  animation: bgScan 11s linear infinite;
}
@keyframes bgScan {
  from { transform: translateY(-20vh); }
  to { transform: translateY(112vh); }
}
/* 极淡的颗粒噪点，消除大面积渐变的塑料感 */
.bg-noise {
  position: absolute;
  inset: 0;
  opacity: 0.038;
  mix-blend-mode: soft-light;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23n)' opacity='0.55'/%3E%3C/svg%3E");
  background-size: 180px 180px;
}
.bg-code {
  position: absolute;
  left: 2%;
  top: 50%;
  transform: translateY(-50%);
  width: 52%;
  max-width: 760px;
  margin: 0;
  font-family: var(--mono);
  font-size: 13px;
  line-height: 1.9;
  color: rgba(var(--green-rgb), 0.62);
  white-space: pre;
  filter: blur(1.8px);
  text-shadow: 0 0 12px rgba(var(--green-rgb), 0.35);
  mask-image: linear-gradient(90deg, #000 55%, transparent 100%);
}
.bg-code .dim { color: rgba(120, 145, 165, 0.85); }
.bg-code .c { color: rgba(120, 145, 165, 1); }
.bg-code .fn { color: rgba(var(--cyan-rgb), 0.82); }
.bg-code .s { color: rgba(245, 180, 70, 0.85); }
.bg-code .y { color: rgba(245, 180, 70, 0.85); }
.bg-network {
  position: absolute;
  /* 让拓扑最下方的节点与登录卡片下边框基本齐平 */
  top: calc(50% - 332px);
  right: -70px;
  width: 58%;
  max-width: 760px;
  opacity: 0.92;
  pointer-events: none;
  filter: drop-shadow(0 0 20px rgba(var(--cyan-rgb), 0.16));
}
/* ---------- 网络拓扑 ---------- */
.topo-links path {
  stroke: rgba(96, 226, 216, 0.34);
  stroke-width: 1;
}
/* 链路上流动的光点 */
.topo-flow path {
  stroke: rgba(150, 255, 238, 0.7);
  stroke-width: 1;
  stroke-dasharray: 3 20;
  animation: topoFlow 6s linear infinite;
}
.topo-flow path:nth-child(2) { animation-duration: 7.4s; animation-delay: -1.6s; }
.topo-flow path:nth-child(3) { animation-duration: 5.6s; animation-delay: -3.1s; }
.topo-flow path:nth-child(4) { animation-duration: 6.8s; animation-delay: -0.8s; }
.topo-flow path:nth-child(5) { animation-duration: 5.2s; animation-delay: -2.4s; }
.topo-flow path:nth-child(6) { animation-duration: 7.8s; animation-delay: -4.2s; }
.topo-flow path:nth-child(7) { animation-duration: 6.2s; animation-delay: -1.1s; }
.topo-flow path:nth-child(8) { animation-duration: 5.8s; animation-delay: -3.6s; }
@keyframes topoFlow {
  to { stroke-dashoffset: -138; }
}

/* 沿链路移动的数据包 */
.topo-pulses circle {
  fill: #b4ffe8;
  filter: drop-shadow(0 0 6px rgba(120, 255, 220, 0.95));
}

/* 节点 */
.topo-nodes .dot {
  fill: #2ee6b0;
  filter: drop-shadow(0 0 5px rgba(46, 230, 176, 0.85));
}
.topo-nodes .dot.cyan {
  fill: #4fd4ea;
  filter: drop-shadow(0 0 5px rgba(79, 212, 234, 0.85));
}
.topo-nodes .dot.amber {
  fill: #f5a623;
  filter: drop-shadow(0 0 6px rgba(var(--amber-rgb), 0.85));
}
.topo-nodes .dot.dim {
  fill: #5f8fb0;
  filter: none;
}
.topo-nodes .dot.core {
  fill: #8dffe0;
  filter: drop-shadow(0 0 8px rgba(141, 255, 224, 0.95));
}
.topo-nodes .halo {
  fill: rgba(31, 202, 166, 0.1);
  stroke: rgba(96, 236, 214, 0.45);
  stroke-width: 1;
}
.topo-nodes .ping {
  fill: none;
  stroke: rgba(96, 236, 214, 0.5);
  stroke-width: 1;
  transform-box: fill-box;
  transform-origin: center;
  animation: topoPing 4.2s ease-out infinite;
}
.topo-nodes .ping.p2 { animation-delay: -1.4s; }
.topo-nodes .ping.p3 { animation-delay: -2.8s; }
@keyframes topoPing {
  0% { transform: scale(1); opacity: 0.75; }
  72%, 100% { transform: scale(3.2); opacity: 0; }
}

/* ---------- 卡片接入拓扑的连接线 ---------- */
.merge-link {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  pointer-events: none;
  overflow: visible;
}
.link-base {
  fill: none;
  stroke: rgba(96, 226, 216, 0.36);
  stroke-width: 1.1;
}
.link-flow {
  fill: none;
  stroke: rgba(150, 255, 238, 0.8);
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-dasharray: 4 9;
  animation: linkFlow 2.6s linear infinite;
}
@keyframes linkFlow {
  to { stroke-dashoffset: -60; }
}
.link-port {
  fill: #8dffe0;
  filter: drop-shadow(0 0 8px rgba(120, 255, 220, 0.95));
}
.link-port-ring {
  fill: none;
  stroke: rgba(120, 255, 220, 0.55);
  stroke-width: 1;
  transform-box: fill-box;
  transform-origin: center;
  animation: portPing 2.8s ease-out infinite;
}
@keyframes portPing {
  0% { transform: scale(1); opacity: 0.8; }
  85%, 100% { transform: scale(3.2); opacity: 0; }
}

/* ---------- 主体布局 ---------- */
.auth-viewport {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  margin: auto;
  padding: 24px;
}
.auth-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  margin-bottom: 40px;
}
.auth-brand .shield {
  width: 96px;
  height: 104px;
  filter: drop-shadow(0 0 18px rgba(var(--cyan-rgb), 0.35));
}
.brand-name {
  font-family: var(--mono);
  font-size: 40px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #ffffff;
  text-shadow: 0 0 18px rgba(120, 240, 255, 0.35);
}
.brand-sub {
  font-family: var(--mono);
  font-size: 16px;
  letter-spacing: 0.5px;
  color: #cfe6ef;
  margin-top: 8px;
}

/* ---------- 登录卡片 ---------- */
.auth-card-wrap {
  position: relative;
  z-index: 2;
  width: min(100%, 550px);
  margin: 0 auto;
}
.auth-card {
  position: relative;
  width: 100%;
  margin: 0 auto;
  padding: 44px 72px 40px;
  /* 1px 渐变描边：左上偏亮、右下偏暗，模拟环境光，避免整圈同色的“塑料边” */
  border: 1px solid transparent;
  border-radius: 18px;
  background:
    linear-gradient(180deg, rgba(4, 12, 15, 0.94), rgba(3, 9, 12, 0.94)) padding-box,
    linear-gradient(
      155deg,
      rgba(150, 246, 255, 0.85) 0%,
      rgba(44, 206, 190, 0.45) 24%,
      rgba(18, 58, 68, 0.6) 58%,
      rgba(38, 150, 150, 0.42) 100%
    ) border-box;
  /* 磨砂玻璃：让卡片底色透出周围的光，减小与背景的色差 */
  -webkit-backdrop-filter: blur(18px);
  backdrop-filter: blur(18px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    inset 0 0 60px rgba(0, 210, 190, 0.035),
    0 26px 70px rgba(0, 0, 0, 0.6),
    0 0 28px rgba(0, 190, 170, 0.07);
}
.auth-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  /* 顶部柔和的冷色反光，替换原来那条均匀的绿色亮带 */
  background:
    radial-gradient(90% 42% at 50% 0%, rgba(96, 226, 232, 0.045), transparent 72%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.015), transparent 18%);
  pointer-events: none;
}
/* 卡片内侧四角的 HUD 角标，增加终端面板的细节 */
.auth-card::after {
  content: '';
  position: absolute;
  inset: 12px;
  pointer-events: none;
  opacity: 0.45;
  background:
    linear-gradient(rgba(140, 245, 245, 0.6), rgba(140, 245, 245, 0.6)) left top / 16px 1px no-repeat,
    linear-gradient(rgba(140, 245, 245, 0.6), rgba(140, 245, 245, 0.6)) left top / 1px 16px no-repeat,
    linear-gradient(rgba(140, 245, 245, 0.6), rgba(140, 245, 245, 0.6)) right top / 16px 1px no-repeat,
    linear-gradient(rgba(140, 245, 245, 0.6), rgba(140, 245, 245, 0.6)) right top / 1px 16px no-repeat,
    linear-gradient(rgba(140, 245, 245, 0.6), rgba(140, 245, 245, 0.6)) left bottom / 16px 1px no-repeat,
    linear-gradient(rgba(140, 245, 245, 0.6), rgba(140, 245, 245, 0.6)) left bottom / 1px 16px no-repeat,
    linear-gradient(rgba(140, 245, 245, 0.6), rgba(140, 245, 245, 0.6)) right bottom / 16px 1px no-repeat,
    linear-gradient(rgba(140, 245, 245, 0.6), rgba(140, 245, 245, 0.6)) right bottom / 1px 16px no-repeat;
}
.switch-btn {
  position: fixed;
  z-index: 50;
  top: 26px;
  right: 30px;
  padding: 10px 22px;
  font-family: var(--sans);
  font-size: 18px;
  font-weight: 600;
  color: #ff6a5a;
  background: rgba(40, 6, 8, 0.85);
  border: 2px solid #ff5140;
  border-radius: 6px;
  cursor: pointer;
  transition: 0.15s;
}
.switch-btn:hover {
  color: #fff;
  background: rgba(var(--red-rgb), 0.22);
  box-shadow: 0 0 18px rgba(var(--red-rgb), 0.45);
}
.auth-title {
  position: relative;
  text-align: center;
  font-size: 32px;
  font-weight: 800;
  margin-bottom: 28px;
  letter-spacing: 6px;
  /* 冷色金属渐变，比纯白更有层次 */
  background: linear-gradient(180deg, #ffffff 0%, #d8f4ff 46%, #8fdcec 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 0 12px rgba(120, 235, 240, 0.22));
}
.auth-title::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -16px;
  width: 108px;
  height: 1px;
  transform: translateX(-50%);
  background: linear-gradient(90deg, transparent, rgba(140, 245, 245, 0.55), transparent);
}
.auth-form {
  position: relative;
  display: flex;
  flex-direction: column;
}
.field {
  margin-bottom: 22px;
}
.field-head {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  color: #a9c2d0;
  margin-bottom: 12px;
}
.field-head .hint {
  font-size: 14px;
  color: #4f6b7d;
}
.field input {
  width: 100%;
  padding: 13px 20px 13px 46px;
  font-size: 19px;
  color: #e9f5fb;
  background: var(--field-bg);
  border: 1px solid #2b4756;
  border-radius: 6px;
  outline: none;
  transition: 0.15s;
}
.input-wrap {
  position: relative;
  display: block;
}
.input-ico {
  position: absolute;
  left: 16px;
  top: 50%;
  width: 18px;
  height: 18px;
  transform: translateY(-50%);
  color: #4d7686;
  pointer-events: none;
  transition: color 0.2s;
}
.input-wrap:focus-within .input-ico {
  color: var(--cyan);
}
.field input::placeholder {
  color: #6f8a9b;
}
.field input:focus {
  border-color: var(--green);
  box-shadow: 0 0 0 3px rgba(var(--green-rgb), 0.14), 0 0 18px rgba(var(--green-rgb), 0.18);
}
/*
 * 浏览器自动填充（账号 / 密码 / 邮箱）时，Chrome/Edge 会强制把输入框刷成
 * 浅色底 + 深色字。这里用超大的 inset 阴影盖回深色底，并固定文字与光标颜色。
 */
.field input:-webkit-autofill,
.field input:-webkit-autofill:hover,
.field input:-webkit-autofill:active {
  -webkit-text-fill-color: #e9f5fb;
  caret-color: #e9f5fb;
  border-color: #2b4756;
  box-shadow: 0 0 0 1000px #0a171e inset;
  transition: background-color 999999s ease-in-out 0s;
}
.field input:-webkit-autofill:focus {
  border-color: var(--green);
  box-shadow:
    0 0 0 1000px #0a171e inset,
    0 0 0 3px rgba(var(--green-rgb), 0.14),
    0 0 18px rgba(var(--green-rgb), 0.18);
}
/* Firefox 等支持标准 :autofill 的浏览器 */
.field input:autofill {
  background-color: #0a171e;
  color: #e9f5fb;
}
.submit {
  position: relative;
  overflow: hidden;
  width: 100%;
  margin-top: 6px;
  padding: 15px;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 6px;
  color: #062015;
  background: linear-gradient(180deg, #4dffcf, #00e39a);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  box-shadow: 0 0 26px rgba(var(--green-rgb), 0.35);
  transition: 0.15s;
}
.submit:hover:not(:disabled) {
  filter: brightness(1.08);
  box-shadow: 0 0 34px rgba(var(--green-rgb), 0.55);
}
/* 悬停时一道高光扫过，增加按钮的质感 */
.submit::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -60%;
  width: 40%;
  height: 200%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.35), transparent);
  transform: skewX(-18deg);
  transition: left 0.55s ease;
  pointer-events: none;
}
.submit:hover:not(:disabled)::after {
  left: 120%;
}
.submit:disabled {
  opacity: 0.7;
  cursor: default;
}
.err {
  margin-bottom: 18px;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--red);
  background: rgba(var(--red-rgb), 0.12);
  border: 1px solid rgba(var(--red-rgb), 0.5);
  border-radius: 6px;
}
.alt {
  position: relative;
  margin-top: 24px;
  text-align: center;
  font-size: 16px;
  color: #a9c2d0;
}
.alt a {
  color: var(--green);
}
.alt a:hover {
  text-decoration: underline;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

@media (max-width: 900px) {
  .auth-viewport {
    padding: 72px 20px 44px;
  }
  .auth-brand,
  .auth-card-wrap {
    margin-left: 0;
  }
  .auth-brand {
    margin-bottom: 34px;
  }
  .switch-btn {
    right: 16px;
  }
  .bg-code {
    width: 70%;
    opacity: 0.5;
  }
}

/* 矮屏（如 900x800 的截图台）压缩纵向占用，避免顶部按钮被裁切 */
@media (max-height: 880px) {
  .auth-viewport {
    padding: 78px 24px 34px;
  }
  .auth-brand {
    margin-bottom: 26px;
  }
  .auth-brand .shield {
    width: 72px;
    height: 78px;
  }
  .brand-name {
    font-size: 32px;
  }
  .auth-card {
    padding: 40px 70px 34px;
  }
  .auth-title {
    margin-bottom: 24px;
  }
  .field {
    margin-bottom: 18px;
  }
}

@media (max-width: 600px) {
  .auth-brand .shield {
    width: 70px;
    height: 76px;
  }
  .brand-name {
    font-size: 30px;
  }
  .brand-sub {
    font-size: 13px;
  }
  .auth-card {
    padding: 46px 26px 34px;
  }
  .switch-btn {
    top: 14px;
    right: 12px;
    padding: 7px 12px;
    font-size: 14px;
  }
  .auth-theme {
    top: 14px;
    right: 132px;
  }
  .auth-brand {
    margin-bottom: 64px;
  }
  .auth-title {
    font-size: 26px;
    margin-bottom: 28px;
  }
  .field input {
    font-size: 16px;
    padding: 13px 16px 13px 44px;
  }
  .submit {
    font-size: 19px;
    padding: 15px;
  }
  .bg-code,
  .bg-network,
  .merge-link {
    display: none;
  }
}

:global(html[data-theme='light'] .auth-page) {
  background: #edf5f3;
  color-scheme: light;
}
:global(html[data-theme='light'] .auth-card),
:global(html[data-theme='light'] .auth-form),
:global(html[data-theme='light'] .field) {
  color-scheme: light;
}
:global(html[data-theme='light'] .auth-page input) {
  color-scheme: light !important;
}
:global(html[data-theme='light'] .bg-glow) {
  background:
    radial-gradient(700px 520px at 62% 8%, rgba(0, 125, 80, 0.1), transparent 62%),
    radial-gradient(900px 700px at 76% 82%, rgba(0, 113, 140, 0.07), transparent 68%),
    radial-gradient(760px 620px at 10% 88%, rgba(0, 125, 80, 0.06), transparent 66%);
}
:global(html[data-theme='light'] .bg-code) {
  color: rgba(0, 125, 80, 0.34);
  text-shadow: none;
}
:global(html[data-theme='light'] .bg-code .dim),
:global(html[data-theme='light'] .bg-code .c) {
  color: rgba(62, 88, 99, 0.52);
}
:global(html[data-theme='light'] .bg-code .fn) {
  color: rgba(0, 113, 140, 0.52);
}
:global(html[data-theme='light'] .bg-code .s),
:global(html[data-theme='light'] .bg-code .y) {
  color: rgba(163, 95, 0, 0.52);
}
:global(html[data-theme='light'] .bg-noise) {
  opacity: 0.018;
}
:global(html[data-theme='light'] .brand-name) {
  color: #17333a;
  text-shadow: 0 0 16px rgba(0, 113, 140, 0.18);
}
:global(html[data-theme='light'] .brand-sub) {
  color: #5d707a;
}
:global(html[data-theme='light'] .auth-card) {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(245, 250, 249, 0.94)) padding-box,
    linear-gradient(
      155deg,
      rgba(0, 125, 80, 0.72) 0%,
      rgba(0, 113, 140, 0.42) 30%,
      rgba(188, 203, 209, 0.9) 62%,
      rgba(0, 125, 80, 0.36) 100%
    ) border-box;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.8),
    0 24px 64px rgba(29, 54, 48, 0.16),
    0 0 24px rgba(0, 125, 80, 0.06);
}
:global(html[data-theme='light'] .auth-card::before) {
  background:
    radial-gradient(90% 42% at 50% 0%, rgba(0, 125, 80, 0.06), transparent 72%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.28), transparent 18%);
}
:global(html[data-theme='light'] .auth-title) {
  background: linear-gradient(180deg, #173b42 0%, #006f5a 58%, #007d50 100%);
  -webkit-background-clip: text;
  background-clip: text;
  filter: none;
}
:global(html[data-theme='light'] .auth-title::after) {
  background: linear-gradient(90deg, transparent, rgba(0, 125, 80, 0.48), transparent);
}
:global(html[data-theme='light'] .field-head),
:global(html[data-theme='light'] .alt) {
  color: #526872;
}
:global(html[data-theme='light'] .field-head .hint) {
  color: #84949c;
}
:global(html[data-theme='light'] .field input) {
  color: #26353e;
  background: rgba(255, 255, 255, 0.96);
  border-color: #bccbd1;
}
:global(html[data-theme='light'] .field input::placeholder) {
  color: #84949c;
}
:global(html[data-theme='light'] .input-ico) {
  color: #6f828b;
}
:global(html[data-theme='light'] .field input:-webkit-autofill),
:global(html[data-theme='light'] .field input:-webkit-autofill:hover),
:global(html[data-theme='light'] .field input:-webkit-autofill:active) {
  background-color: #ffffff !important;
  color: #26353e !important;
  -webkit-text-fill-color: #26353e !important;
  caret-color: #26353e !important;
  border-color: #bccbd1 !important;
  box-shadow: 0 0 0 1000px #ffffff inset !important;
  transition: background-color 999999s ease-in-out 0s !important;
}
:global(html[data-theme='light'] .field input:-webkit-autofill:focus) {
  border-color: var(--green) !important;
  box-shadow:
    0 0 0 1000px #ffffff inset,
    0 0 0 3px rgba(var(--green-rgb), 0.14),
    0 0 18px rgba(var(--green-rgb), 0.18) !important;
}
:global(html[data-theme='light'] .field input:autofill) {
  background-color: #ffffff !important;
  color: #26353e !important;
}
:global(html[data-theme='light'] .submit) {
  color: #ffffff;
  background: linear-gradient(180deg, #009a6a, #006b47);
  box-shadow: 0 0 20px rgba(0, 125, 80, 0.2);
}
:global(html[data-theme='light'] .submit:hover:not(:disabled)) {
  box-shadow: 0 0 28px rgba(0, 125, 80, 0.3);
}
:global(html[data-theme='light'] .err) {
  color: #a52822;
  background: rgba(199, 53, 46, 0.08);
}
:global(html[data-theme='light'] .switch-btn) {
  color: #b42f29;
  background: rgba(199, 53, 46, 0.07);
  border-color: #c7352e;
}
:global(html[data-theme='light'] .switch-btn:hover) {
  color: #ffffff;
  background: #c7352e;
  box-shadow: 0 0 16px rgba(199, 53, 46, 0.22);
}
</style>
