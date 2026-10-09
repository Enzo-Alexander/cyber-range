<template>
  <div class="auth-page">
    <!-- 背景：左侧绿色代码流 + 右侧彩色网络拓扑 -->
    <div class="auth-bg" aria-hidden="true">
      <div class="bg-grid"></div>
      <div class="bg-glow"></div>

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
        <g class="radar">
          <circle cx="210" cy="210" r="200" stroke="#00E0FF" stroke-opacity="0.22" />
          <circle cx="210" cy="210" r="150" stroke="#00E0FF" stroke-opacity="0.2" />
          <circle cx="210" cy="210" r="100" stroke="#00E0FF" stroke-opacity="0.18" />
          <circle cx="210" cy="210" r="50" stroke="#00E0FF" stroke-opacity="0.16" />
          <line x1="210" y1="210" x2="330" y2="210" stroke="#00E0FF" stroke-opacity="0.35" />
          <line x1="210" y1="210" x2="210" y2="60" stroke="#00E0FF" stroke-opacity="0.35" />
          <path d="M210 210 L210 10 A200 200 0 0 1 383 110 Z" fill="rgba(0,255,159,0.10)" class="radar-sweep" />
          <g fill="#00FF9F">
            <circle cx="150" cy="150" r="4" />
            <circle cx="300" cy="118" r="3" />
            <circle cx="118" cy="282" r="3" />
          </g>
        </g>
      </svg>
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

        <div class="auth-card">
        <h2 class="auth-title">{{ mode === 'login' ? '登录' : '注册' }}</h2>

        <form class="auth-form" novalidate @submit.prevent="submit">
          <p v-if="error" class="err" role="alert">{{ error }}</p>

          <div class="field">
            <div class="field-head">
              <span>用户名</span>
              <span class="hint">{{ mode === 'login' ? '帐号' : '注册' }}</span>
            </div>
            <input
              ref="usernameInput"
              v-model.trim="username"
              type="text"
              placeholder="用户名"
              autocomplete="username"
            />
          </div>

          <div v-if="mode === 'register'" class="field">
            <div class="field-head"><span>邮箱</span></div>
            <input v-model.trim="email" type="email" placeholder="邮箱" autocomplete="email" />
          </div>

          <div class="field">
            <div class="field-head">
              <span>密码</span>
              <span class="hint">{{ mode === 'login' ? '帐号' : '注册' }}</span>
            </div>
            <input
              v-model="password"
              type="password"
              placeholder="密码"
              :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
            />
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
import { nextTick, onMounted, ref, useId, watch } from 'vue'
import { useRouter } from 'vue-router'
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
    nextTick(() => usernameInput.value?.focus())
  }
)

const username = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const usernameInput = ref<HTMLInputElement | null>(null)
const shieldGradientId = `shield-edge-${useId()}`

onMounted(() => usernameInput.value?.focus())

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
    linear-gradient(rgba(31, 202, 166, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(31, 202, 166, 0.045) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: radial-gradient(ellipse 90% 80% at 50% 40%, #000 30%, transparent 100%);
}
.bg-glow {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(700px 520px at 62% 8%, rgba(31, 202, 166, 0.16), transparent 62%),
    radial-gradient(900px 700px at 76% 82%, rgba(31, 120, 170, 0.1), transparent 68%),
    radial-gradient(760px 620px at 10% 88%, rgba(0, 255, 159, 0.08), transparent 66%);
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
  color: rgba(0, 255, 159, 0.62);
  white-space: pre;
  filter: blur(1.8px);
  text-shadow: 0 0 12px rgba(0, 255, 159, 0.35);
  mask-image: linear-gradient(90deg, #000 55%, transparent 100%);
}
.bg-code .dim { color: rgba(120, 145, 165, 0.85); }
.bg-code .c { color: rgba(120, 145, 165, 1); }
.bg-code .fn { color: rgba(0, 224, 255, 0.82); }
.bg-code .s { color: rgba(245, 180, 70, 0.85); }
.bg-code .y { color: rgba(245, 180, 70, 0.85); }
.bg-network {
  position: absolute;
  top: 5%;
  right: -30px;
  width: 42%;
  max-width: 540px;
  opacity: 0.5;
  pointer-events: none;
}
.radar-sweep {
  transform-box: view-box;
  transform-origin: 210px 210px;
  animation: radarSpin 7s linear infinite;
}
@keyframes radarSpin {
  to { transform: rotate(360deg); }
}
.radar g[fill] circle {
  animation: blip 4s ease-in-out infinite;
}
@keyframes blip {
  0%, 100% { opacity: 0.9; }
  50% { opacity: 0.35; }
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
  filter: drop-shadow(0 0 18px rgba(0, 224, 255, 0.35));
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
  background: linear-gradient(180deg, rgba(10, 26, 34, 0.82), rgba(6, 16, 22, 0.76));
  clip-path: polygon(
    14px 0, calc(100% - 14px) 0, 100% 14px, 100% calc(100% - 14px),
    calc(100% - 14px) 100%, 14px 100%, 0 calc(100% - 14px), 0 14px
  );
  box-shadow:
    inset 0 0 0 1px rgba(31, 202, 166, 0.55),
    inset 0 0 42px rgba(0, 200, 180, 0.08),
    0 0 40px rgba(0, 190, 170, 0.18);
}
.auth-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(31, 202, 166, 0.16), transparent 26%);
  pointer-events: none;
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
  background: rgba(255, 60, 45, 0.22);
  box-shadow: 0 0 18px rgba(255, 60, 45, 0.45);
}
.auth-title {
  position: relative;
  text-align: center;
  font-size: 32px;
  font-weight: 800;
  color: #ffffff;
  margin-bottom: 28px;
  letter-spacing: 4px;
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
  padding: 13px 20px;
  font-size: 19px;
  color: #e9f5fb;
  background: rgba(9, 22, 30, 0.9);
  border: 1px solid #2b4756;
  border-radius: 6px;
  outline: none;
  transition: 0.15s;
}
.field input::placeholder {
  color: #6f8a9b;
}
.field input:focus {
  border-color: var(--green);
  box-shadow: 0 0 0 3px rgba(0, 255, 159, 0.14), 0 0 18px rgba(0, 255, 159, 0.18);
}
.submit {
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
  box-shadow: 0 0 26px rgba(0, 255, 159, 0.35);
  transition: 0.15s;
}
.submit:hover:not(:disabled) {
  filter: brightness(1.08);
  box-shadow: 0 0 34px rgba(0, 255, 159, 0.55);
}
.submit:disabled {
  opacity: 0.7;
  cursor: default;
}
.err {
  margin-bottom: 18px;
  padding: 10px 14px;
  font-size: 14px;
  color: #ffb4ac;
  background: rgba(255, 60, 45, 0.12);
  border: 1px solid rgba(255, 60, 45, 0.5);
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
  .auth-brand {
    margin-bottom: 64px;
  }
  .auth-title {
    font-size: 26px;
    margin-bottom: 28px;
  }
  .field input {
    font-size: 16px;
    padding: 13px 16px;
  }
  .submit {
    font-size: 19px;
    padding: 15px;
  }
  .bg-code,
  .bg-network {
    display: none;
  }
}
</style>
