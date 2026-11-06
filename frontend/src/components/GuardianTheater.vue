<template>
  <div
    class="guardian-theater"
    :class="{
      'stage-hidden': !showStage,
      'theater-closing': closing,
    }"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
  >
    <div class="theater-parallax">
      <div class="theater-back-wall"></div>

      <div class="proscenium-arch"></div>
      <div class="stage-truss stage-truss-top"></div>
      <div class="stage-truss stage-truss-left"></div>
      <div class="stage-truss stage-truss-right"></div>

      <div class="stage-curtain stage-curtain-left"></div>
      <div class="stage-curtain stage-curtain-right"></div>
      <div class="stage-curtain stage-curtain-top"></div>

      <div class="inner-stage-frame">
        <div class="stage-screen"></div>
      </div>
      <div class="stage-platform"></div>

      <div class="overhead-lighting">
        <div
          v-for="character in characters"
          :key="`light-${character.id}`"
          class="stage-spot"
          :class="{ active: hoveredId === character.id || actingId === character.id }"
        >
          <span class="stage-fixture"></span>
          <span class="overhead-beam"></span>
        </div>
      </div>

      <div class="stage-floor"></div>
      <div class="stage-front-lip"></div>
      <div class="audience-silhouette"></div>
    </div>

    <div class="standee-row">
      <div
        v-for="(character, index) in characters"
        :key="character.id"
        class="standee-wrap"
        :class="{
          hovered: hoveredId === character.id,
          acting: actingId === character.id,
        }"
        :style="{ '--index': index }"
      >
        <div
          :ref="(element) => setCharacterElement(character.id, element)"
          class="paper-standee"
          :style="characterStyle(character.id)"
          @pointerdown.stop.prevent="onPointerDown(character.id, $event)"
          @pointerenter="hoveredId = character.id"
          @pointerleave="onPointerLeave(character.id)"
        >
          <div class="paper-inner">
            <img
              class="character-image"
              :src="character.image"
              :alt="character.name"
              draggable="false"
            />
            <svg
              v-if="character.id === 'guardian'"
              class="character-svg"
              viewBox="0 0 220 360"
              aria-hidden="true"
            >
              <path d="M70 145Q110 118 150 145L166 288H54Z" fill="#263943" />
              <path d="M84 145L110 166L136 145L130 235H90Z" fill="#3d5963" />
              <path d="M74 149L49 242L65 249L91 175Z" fill="#263943" />
              <path d="M146 149L174 237L158 246L131 175Z" fill="#263943" />
              <circle cx="110" cy="92" r="36" fill="#d6ae88" />
              <path d="M75 86Q84 42 119 48Q153 55 145 100L132 75Q108 84 75 86Z" fill="#17262d" />
              <path d="M63 77Q110 50 157 77L149 91Q109 72 70 91Z" fill="#1d3038" />
              <path d="M102 104Q110 111 119 104" fill="none" stroke="#7e5944" stroke-width="3" stroke-linecap="round" />
              <path d="M55 286L86 286L78 320H61Z" fill="#1c2a30" />
              <path d="M134 286L165 286L159 320H141Z" fill="#1c2a30" />
              <path d="M177 115V278" stroke="#a6845f" stroke-width="5" stroke-linecap="round" />
              <path d="M177 115Q143 91 112 120Q151 126 184 157Q210 128 177 115Z" fill="#355967" />
              <path d="M177 115Q206 100 218 125" fill="none" stroke="#7694a0" stroke-width="4" stroke-linecap="round" />
            </svg>

            <svg
              v-else-if="character.id === 'observer'"
              class="character-svg"
              viewBox="0 0 220 360"
              aria-hidden="true"
            >
              <path d="M72 143Q110 118 148 143L161 286H58Z" fill="#2e5362" />
              <path d="M87 145L110 158L134 145L128 238H91Z" fill="#477180" />
              <path d="M77 151L57 227L72 234L94 176Z" fill="#2e5362" />
              <path d="M144 151L170 225L155 234L132 178Z" fill="#2e5362" />
              <circle cx="110" cy="91" r="36" fill="#d7b08b" />
              <path d="M75 82Q83 48 112 47Q145 49 146 89Q123 74 75 82Z" fill="#1c2c34" />
              <circle cx="96" cy="94" r="12" fill="none" stroke="#d7e8e7" stroke-width="3" />
              <circle cx="125" cy="94" r="12" fill="none" stroke="#d7e8e7" stroke-width="3" />
              <path d="M108 94H113" stroke="#d7e8e7" stroke-width="3" />
              <path d="M57 294L87 294L81 324H60Z" fill="#1c2d34" />
              <path d="M133 294L163 294L158 324H137Z" fill="#1c2d34" />
              <path d="M151 226L198 200L210 223L164 248Z" fill="#b58a55" />
              <circle cx="202" cy="211" r="14" fill="#9edbe4" />
              <path d="M151 217L173 228" stroke="#e3cda5" stroke-width="3" />
            </svg>

            <svg
              v-else
              class="character-svg"
              viewBox="0 0 220 360"
              aria-hidden="true"
            >
              <path d="M67 145Q109 117 153 145L168 288H52Z" fill="#5a3b2b" />
              <path d="M84 145L110 163L137 145L132 242H88Z" fill="#846043" />
              <path d="M72 151L48 231L65 239L91 177Z" fill="#5a3b2b" />
              <path d="M149 151L174 226L157 235L132 178Z" fill="#5a3b2b" />
              <circle cx="110" cy="92" r="36" fill="#d7ae86" />
              <path d="M73 87Q74 43 113 44Q153 48 148 91Q126 71 73 87Z" fill="#33251f" />
              <path d="M88 64Q114 41 142 61" fill="none" stroke="#6d4b3a" stroke-width="4" stroke-linecap="round" />
              <path d="M54 293L86 293L79 325H58Z" fill="#34251f" />
              <path d="M135 293L166 293L160 325H139Z" fill="#34251f" />
              <path d="M65 188H145V245H65Z" fill="#7c5034" />
              <path d="M75 197H135V235H75Z" fill="#d7c49d" />
              <path d="M82 210H128M82 221H119" stroke="#856d4d" stroke-width="3" />
              <path d="M158 151L181 170L160 207L143 181Z" fill="#9e7449" />
            </svg>
            <span class="standee-sparkles" aria-hidden="true">
              <span
                v-for="(sparkle, sparkleIndex) in standeeSparkles"
                :key="`sparkle-${character.id}-${sparkleIndex}`"
                class="standee-sparkle"
                :class="[
                  `shape-${sparkleIndex % 3}`,
                  { cool: sparkle.cool },
                ]"
                :style="sparkleStyle(sparkle)"
              ></span>
            </span>
          </div>
        </div>
        <span class="standee-lever" :style="leverStyle(character.id)"></span>
        <span class="standee-foot"></span>
      </div>
    </div>

    <button
      class="theater-close"
      type="button"
      aria-label="离开美好守夜剧场"
      :disabled="closing"
      @click="closeWithAnimation"
    >×</button>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'

const emit = defineEmits<{ close: [] }>()

interface SpringState {
  angle: number
  angularVelocity: number
  shiftX: number
  shiftY: number
  velocityX: number
  velocityY: number
  dragging: boolean
  headLag: number
}

interface StandeeSparkle {
  x: number
  y: number
  size: number
  delay: number
  duration: number
  drift: number
  rotation: number
  cool?: boolean
}

const zodiacCharacters = [
  {
    id: 'aries',
    name: '白羊座',
    image: '/zodiac/aries.png',
    lines: ['先迈出一步，路才会出现。', '勇气有时候比答案更重要。'],
  },
  {
    id: 'taurus',
    name: '金牛座',
    image: '/zodiac/taurus.png',
    lines: ['慢一点，也能走到很远的地方。', '值得守护的东西，从来不嫌沉重。'],
  },
  {
    id: 'gemini',
    name: '双子座',
    image: '/zodiac/gemini.png',
    lines: ['两个念头碰在一起，就有了新故事。', '好奇心是最轻的翅膀。'],
  },
  {
    id: 'cancer',
    name: '巨蟹座',
    image: '/zodiac/cancer.png',
    lines: ['柔软并不等于脆弱。', '记得回来的方向，就敢去更远的地方。'],
  },
  {
    id: 'leo',
    name: '狮子座',
    image: '/zodiac/leo.png',
    lines: ['光不是用来证明自己，而是照亮别人。', '真正的勇气，也包含温柔。'],
  },
  {
    id: 'virgo',
    name: '处女座',
    image: '/zodiac/virgo.png',
    lines: ['细节里藏着世界的秩序。', '认真本身，就是一种浪漫。'],
  },
  {
    id: 'libra',
    name: '天秤座',
    image: '/zodiac/libra.png',
    lines: ['平衡不是停滞，而是继续选择。', '每一种美好，都有自己的重量。'],
  },
  {
    id: 'scorpio',
    name: '天蝎座',
    image: '/zodiac/scorpio.png',
    lines: ['深渊也会反射星光。', '沉默之下，往往藏着最坚定的答案。'],
  },
  {
    id: 'sagittarius',
    name: '射手座',
    image: '/zodiac/sagittarius.png',
    lines: ['箭头指向的地方，未必是终点。', '去更远的地方，带上好奇就够了。'],
  },
  {
    id: 'capricorn',
    name: '摩羯座',
    image: '/zodiac/capricorn.png',
    lines: ['山不会自己走来，所以我们向上。', '耐心是看不见的攀登。'],
  },
  {
    id: 'aquarius',
    name: '水瓶座',
    image: '/zodiac/aquarius.png',
    lines: ['让想法像水一样，找到新的形状。', '不一样，也可以是正确的方向。'],
  },
  {
    id: 'pisces',
    name: '双鱼座',
    image: '/zodiac/pisces.png',
    lines: ['梦会退潮，但不会真正消失。', '在光影之间，也能找到路。'],
  },
]

function dailySeed() {
  const now = new Date()
  const key = `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`
  let hash = 2166136261
  for (let index = 0; index < key.length; index += 1) {
    hash ^= key.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

function randomGenerator(seed: number) {
  let value = seed
  return () => {
    value += 0x6d2b79f5
    let result = value
    result = Math.imul(result ^ (result >>> 15), result | 1)
    result ^= result + Math.imul(result ^ (result >>> 7), result | 61)
    return ((result ^ (result >>> 14)) >>> 0) / 4294967296
  }
}

function pickDailyCharacters() {
  const pool = [...zodiacCharacters]
  const random = randomGenerator(dailySeed())
  for (let index = pool.length - 1; index > 0; index -= 1) {
    const target = Math.floor(random() * (index + 1))
    ;[pool[index], pool[target]] = [pool[target], pool[index]]
  }
  return pool.slice(0, 3).map((character, index) => ({
    ...character,
    phase: index * 1.9 + 0.3,
    stiffness: 0.08 - index * 0.004,
    damping: 0.988 - index * 0.004,
  }))
}

const characters = pickDailyCharacters()
const LEVER_REST_LENGTH = 136
const LEVER_IMAGE_OVERLAP = 40
const DRAG_Y_SENSITIVITY = 0.2
const MAX_DRAG_Y = 92
const CURTAIN_CLOSE_DURATION = 1400
const showStage = false

const standeeSparkles: StandeeSparkle[] = [
  { x: 13, y: 46, size: 3.2, delay: 0.08, duration: 1.9, drift: -12, rotation: 18 },
  { x: 25, y: 20, size: 2.4, delay: 0.48, duration: 1.65, drift: -8, rotation: -24, cool: true },
  { x: 41, y: 9, size: 3.8, delay: 0.24, duration: 2.2, drift: -16, rotation: 32 },
  { x: 59, y: 13, size: 2.2, delay: 0.72, duration: 1.75, drift: -9, rotation: 14, cool: true },
  { x: 78, y: 24, size: 3.1, delay: 0.18, duration: 2.05, drift: -14, rotation: -28 },
  { x: 89, y: 48, size: 2.6, delay: 0.58, duration: 1.8, drift: -10, rotation: 22 },
  { x: 11, y: 66, size: 2.3, delay: 0.86, duration: 1.7, drift: -7, rotation: -18, cool: true },
  { x: 91, y: 69, size: 3.4, delay: 0.34, duration: 2.15, drift: -13, rotation: 30 },
  { x: 17, y: 84, size: 2.8, delay: 0.65, duration: 1.95, drift: -11, rotation: 16 },
  { x: 33, y: 91, size: 2.1, delay: 0.12, duration: 1.6, drift: -6, rotation: -22, cool: true },
  { x: 68, y: 92, size: 3.1, delay: 0.52, duration: 2.1, drift: -12, rotation: 24 },
  { x: 84, y: 84, size: 2.5, delay: 0.94, duration: 1.85, drift: -9, rotation: -30 },
  { x: 35, y: 48, size: 1.9, delay: 0.4, duration: 1.55, drift: -5, rotation: 12, cool: true },
  { x: 66, y: 43, size: 2.2, delay: 0.78, duration: 1.72, drift: -7, rotation: -16 },
]

const hoveredId = ref('')
const actingId = ref('')
const closing = ref(false)
const characterElements = new Map<string, HTMLElement>()
const states = reactive<Record<string, SpringState>>(
  Object.fromEntries(characters.map((character) => [
    character.id,
    {
      angle: 0,
      angularVelocity: 0,
      shiftX: 0,
      shiftY: 0,
      velocityX: 0,
      velocityY: 0,
      dragging: false,
      headLag: 0,
    },
  ])),
)

let animationFrame = 0
let previousTime = 0
let actingTimer = 0
let closeTimer = 0
let activePointerId: number | null = null
let activeCharacterId = ''
let dragStartX = 0
let dragStartY = 0
let lastPointerX = 0
let lastPointerY = 0
let dragDistance = 0
let dragStartedAt = 0

function setCharacterElement(id: string, element: unknown) {
  if (element instanceof HTMLElement) characterElements.set(id, element)
}

function stateFor(id: string) {
  return states[id]
}

function characterStyle(id: string) {
  const state = stateFor(id)
  return {
    '--tilt': `${state.angle}deg`,
    '--shift-x': `${state.shiftX}px`,
    '--shift-y': `${state.shiftY}px`,
    '--head-lag': `${state.headLag}deg`,
  }
}

function sparkleStyle(sparkle: StandeeSparkle) {
  return {
    '--sparkle-x': `${sparkle.x}%`,
    '--sparkle-y': `${sparkle.y}%`,
    '--sparkle-size': `${sparkle.size}px`,
    '--sparkle-delay': `${sparkle.delay}s`,
    '--sparkle-duration': `${sparkle.duration}s`,
    '--sparkle-drift': `${sparkle.drift}px`,
    '--sparkle-rotation': `${sparkle.rotation}deg`,
  }
}

function leverStyle(id: string) {
  const state = stateFor(id)
  const verticalReach = LEVER_REST_LENGTH - state.shiftY
  const leverReach = Math.hypot(state.shiftX, verticalReach)
  const leverAngle = Math.atan2(state.shiftX, verticalReach) * 180 / Math.PI
  return {
    '--lever-height': `${leverReach + LEVER_IMAGE_OVERLAP}px`,
    '--lever-angle': `${leverAngle}deg`,
  }
}

function onPointerDown(id: string, event: PointerEvent) {
  const state = stateFor(id)
  state.dragging = true
  state.angularVelocity = 0
  state.velocityX = 0
  state.velocityY = 0
  activePointerId = event.pointerId
  activeCharacterId = id
  dragStartX = event.clientX
  dragStartY = event.clientY
  lastPointerX = event.clientX
  lastPointerY = event.clientY
  dragDistance = 0
  dragStartedAt = performance.now()
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
}

function onPointerMove(event: PointerEvent) {
  if (!activeCharacterId || event.pointerId !== activePointerId) return
  const state = stateFor(activeCharacterId)
  const deltaX = event.clientX - dragStartX
  const deltaY = event.clientY - dragStartY
  const movementX = event.clientX - lastPointerX
  const movementY = event.clientY - lastPointerY
  dragDistance += Math.hypot(movementX, movementY)
  lastPointerX = event.clientX
  lastPointerY = event.clientY

  state.angle = Math.max(-60, Math.min(60, deltaX * 0.1))
  const radians = state.angle * Math.PI / 180
  state.shiftX = LEVER_REST_LENGTH * Math.sin(radians)
  state.shiftY = Math.max(
    -MAX_DRAG_Y,
    Math.min(MAX_DRAG_Y, deltaY * DRAG_Y_SENSITIVITY),
  )
  state.angularVelocity = 0
  state.velocityX = 0
  state.velocityY = 0
  state.headLag = -state.angle * 0.14
}

function onPointerUp(event: PointerEvent) {
  if (!activeCharacterId || event.pointerId !== activePointerId) return
  const id = activeCharacterId
  const state = stateFor(id)
  state.dragging = false
  activeCharacterId = ''
  activePointerId = null

  if (dragDistance < 7 && performance.now() - dragStartedAt < 420) {
    triggerCharacter(id)
  }
}

function closeWithAnimation() {
  if (closing.value) return
  closing.value = true
  closeTimer = window.setTimeout(() => {
    emit('close')
  }, CURTAIN_CLOSE_DURATION)
}

function onPointerLeave(id: string) {
  if (hoveredId.value === id && !stateFor(id).dragging) hoveredId.value = ''
}

function triggerCharacter(id: string) {
  const character = characters.find((item) => item.id === id)
  if (!character) return
  actingId.value = id
  clearTimeout(actingTimer)
  actingTimer = window.setTimeout(() => {
    actingId.value = ''
  }, 1800)
}

function animate(now: number) {
  const delta = previousTime ? Math.min(2.4, (now - previousTime) / 16.67) : 1
  previousTime = now

  for (const character of characters) {
    const state = stateFor(character.id)

    if (!state.dragging) {
      const damping = Math.pow(character.damping, delta)
      state.angularVelocity +=
        -2 * state.angle * character.stiffness * 1.2 * delta
      state.angularVelocity *= damping
      state.angle += state.angularVelocity * delta

      state.velocityY += -2 * state.shiftY * character.stiffness * delta
      state.velocityY *= damping
      state.shiftY += state.velocityY * delta
      state.shiftY = Math.max(-MAX_DRAG_Y, Math.min(MAX_DRAG_Y, state.shiftY))

      const radians = state.angle * Math.PI / 180
      state.shiftX = LEVER_REST_LENGTH * Math.sin(radians)
      state.headLag += (-state.angle * 0.14 - state.headLag) * 0.12 * delta

      if (
        Math.abs(state.angle) < 0.05
        && Math.abs(state.angularVelocity) < 0.05
        && Math.abs(state.shiftY) < 0.05
        && Math.abs(state.velocityY) < 0.05
      ) {
        state.angle = 0
        state.angularVelocity = 0
        state.shiftX = 0
        state.shiftY = 0
        state.velocityY = 0
      }
    }

    const element = characterElements.get(character.id)
    if (element) {
      element.style.setProperty('--tilt', `${state.angle.toFixed(3)}deg`)
      element.style.setProperty('--shift-x', `${state.shiftX.toFixed(2)}px`)
      element.style.setProperty('--shift-y', `${state.shiftY.toFixed(2)}px`)
      element.style.setProperty('--head-lag', `${state.headLag.toFixed(3)}deg`)
    }
  }

  animationFrame = requestAnimationFrame(animate)
}

onMounted(() => {
  animationFrame = requestAnimationFrame(animate)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animationFrame)
  clearTimeout(actingTimer)
  clearTimeout(closeTimer)
})

defineExpose({ closeWithAnimation })
</script>

<style scoped>
.guardian-theater {
  --standee-height: min(27vw, 370px);
  --standee-lever-gap: 136px;
  --lever-midpoint: 88px;
  --stage-screen-bottom: calc(
    77%
    - max(50%, var(--standee-height) + var(--standee-lever-gap))
    + var(--lever-midpoint)
  );
  position: absolute;
  inset: 0;
  z-index: 8;
  overflow: hidden;
  background:
    linear-gradient(180deg, #04070d 0%, #09121d 47%, #120c09 100%);
  color: #f3e7ce;
  user-select: none;
  touch-action: none;
}

.guardian-theater.stage-hidden .proscenium-arch,
.guardian-theater.stage-hidden .stage-truss,
.guardian-theater.stage-hidden .stage-floor,
.guardian-theater.stage-hidden .stage-front-lip,
.guardian-theater.stage-hidden .audience-silhouette {
  display: none;
}

.guardian-theater.stage-hidden .inner-stage-frame {
  top: 10%;
  right: 9%;
  bottom: var(--stage-screen-bottom);
  left: 9%;
  border-color: transparent;
  background: transparent;
  box-shadow: none;
}

.guardian-theater.stage-hidden .stage-screen {
  inset: 2% 2% 0;
}

.theater-parallax {
  position: absolute;
  inset: 0;
}

.theater-back-wall {
  position: absolute;
  inset: 4% 5% 5%;
  border-radius: 72px 72px 10px 10px;
  background:
    radial-gradient(ellipse at 50% 16%, rgba(125, 164, 178, 0.2), transparent 44%),
    linear-gradient(180deg, #263846 0%, #1a2731 54%, #111820 100%);
  box-shadow:
    inset 0 0 80px rgba(0, 0, 0, 0.55),
    0 0 0 1px rgba(137, 169, 179, 0.14);
}

.proscenium-arch {
  position: absolute;
  inset: 1.8% 2.8% 3%;
  border: 12px solid #20252a;
  border-bottom: 0;
  border-radius: 86px 86px 0 0;
  box-shadow:
    0 0 0 2px rgba(112, 126, 134, 0.25),
    inset 0 0 26px rgba(0, 0, 0, 0.72);
}

.stage-truss {
  z-index: 4;
  border: 2px solid rgba(165, 178, 184, 0.7);
  background:
    repeating-linear-gradient(45deg, transparent 0 12px, rgba(181, 193, 199, 0.58) 13px 15px, transparent 16px 27px),
    repeating-linear-gradient(-45deg, transparent 0 12px, rgba(145, 158, 165, 0.48) 13px 15px, transparent 16px 27px);
  box-shadow: 0 0 0 1px rgba(22, 25, 28, 0.85);
}

.stage-truss-top {
  position: absolute;
  top: 10%;
  right: 7%;
  left: 7%;
  height: 34px;
}

.stage-truss-left,
.stage-truss-right {
  position: absolute;
  top: 10%;
  bottom: 17%;
  width: 32px;
}

.stage-truss-left { left: 4%; }
.stage-truss-right { right: 4%; }

.stage-curtain {
  z-index: 3;
  background:
    repeating-linear-gradient(90deg, rgba(36, 5, 12, 0.82) 0 17px, rgba(102, 21, 31, 0.92) 18px 34px, rgba(45, 7, 14, 0.86) 35px 54px);
  box-shadow:
    inset 20px 0 32px rgba(0, 0, 0, 0.44),
    0 8px 22px rgba(0, 0, 0, 0.42);
}

.stage-curtain-left,
.stage-curtain-right {
  position: absolute;
  top: 7%;
  bottom: 14%;
  width: 7%;
}

.stage-curtain-left {
  left: 1.2%;
  border-radius: 62px 0 0 8px;
}

.stage-curtain-right {
  right: 1.2%;
  border-radius: 0 62px 8px 0;
}

.stage-curtain-top {
  position: absolute;
  top: 6%;
  right: 7%;
  left: 7%;
  height: 8%;
  border-radius: 48px 48px 0 0;
  clip-path: polygon(0 0, 100% 0, 100% 72%, 96% 84%, 92% 73%, 88% 86%, 84% 74%, 80% 87%, 76% 74%, 72% 87%, 68% 74%, 64% 87%, 60% 74%, 56% 87%, 52% 74%, 48% 87%, 44% 74%, 40% 87%, 36% 74%, 32% 87%, 28% 74%, 24% 87%, 20% 74%, 16% 86%, 12% 73%, 8% 84%, 4% 72%, 0 80%);
}

.guardian-theater.stage-hidden .stage-curtain {
  z-index: 4;
  background:
    repeating-linear-gradient(
      90deg,
      #560a16 0 15px,
      #9d1f2a 16px 32px,
      #680e1b 33px 48px
    );
  box-shadow:
    inset 18px 0 28px rgba(30, 2, 8, 0.44),
    inset -18px 0 28px rgba(30, 2, 8, 0.38),
    0 10px 24px rgba(0, 0, 0, 0.36);
}

.guardian-theater.stage-hidden .stage-curtain-left,
.guardian-theater.stage-hidden .stage-curtain-right {
  top: 4%;
  bottom: 5%;
  width: 45%;
  animation-duration: 1.6s;
  animation-delay: 0.25s;
  animation-timing-function: cubic-bezier(0.72, 0, 0.22, 1);
  animation-fill-mode: both;
}

.guardian-theater.stage-hidden .stage-curtain-left {
  left: 5%;
  border-radius: 66px 0 8px 8px;
  animation-name: open-curtain-left;
}

.guardian-theater.stage-hidden .stage-curtain-right {
  right: 5%;
  border-radius: 0 66px 8px 8px;
  animation-name: open-curtain-right;
}

.guardian-theater.theater-closing .stage-curtain-left {
  z-index: 8;
  animation: close-curtain-left 1.2s cubic-bezier(0.64, 0, 0.24, 1) forwards;
}

.guardian-theater.theater-closing .stage-curtain-right {
  z-index: 8;
  animation: close-curtain-right 1.2s cubic-bezier(0.64, 0, 0.24, 1) forwards;
}

.guardian-theater.theater-closing .standee-row,
.guardian-theater.theater-closing .theater-close {
  pointer-events: none;
}

.guardian-theater.theater-closing .theater-close {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.guardian-theater.stage-hidden .stage-curtain-top {
  top: 4%;
  right: 5%;
  left: 5%;
  height: 7.5%;
  border-radius: 70px 70px 0 0;
}

.inner-stage-frame {
  position: absolute;
  top: 21%;
  right: 15%;
  bottom: 48%;
  left: 15%;
  z-index: 1;
  border: 1px solid rgba(151, 184, 195, 0.24);
  border-bottom-color: rgba(145, 170, 177, 0.38);
  background: linear-gradient(180deg, rgba(29, 45, 55, 0.54), rgba(20, 31, 39, 0.2));
  box-shadow: inset 0 0 46px rgba(0, 0, 0, 0.22);
}

.stage-screen {
  position: absolute;
  inset: 8% 7% 0;
  overflow: hidden;
  border: 5px solid #090c10;
  border-radius: 4px;
  background:
    radial-gradient(ellipse at 50% 20%, rgba(77, 139, 155, 0.16), transparent 58%),
    linear-gradient(180deg, #16232c, #0e171e 72%, #0a1117);
  box-shadow:
    0 0 0 1px rgba(150, 186, 198, 0.18),
    inset 0 0 42px rgba(0, 0, 0, 0.44),
    0 8px 22px rgba(0, 0, 0, 0.28);
}

.stage-screen::before {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    to bottom,
    transparent 0,
    transparent 4px,
    rgba(135, 204, 220, 0.025) 5px,
    transparent 6px
  );
}

.stage-screen::after {
  content: '';
  position: absolute;
  top: -20%;
  left: -20%;
  width: 65%;
  height: 140%;
  background: linear-gradient(90deg, transparent, rgba(162, 220, 231, 0.035), transparent);
  transform: rotate(12deg);
}

.stage-platform {
  display: none;
}

.guardian-theater.stage-hidden .stage-platform {
  position: absolute;
  top: calc(100% - var(--stage-screen-bottom) - 1px);
  right: 0;
  bottom: 5%;
  left: 0;
  z-index: 1;
  display: block;
  clip-path: polygon(10.64% 0, 89.36% 0, 95% 100%, 5% 100%);
  border-top: 1px solid rgba(237, 208, 158, 0.5);
  background:
    repeating-linear-gradient(
      to bottom,
      transparent 0 41px,
      rgba(255, 228, 178, 0.07) 42px,
      rgba(39, 23, 13, 0.26) 43px,
      transparent 44px
    ),
    linear-gradient(180deg, #76593d 0%, #664b32 52%, #3f2d20 100%);
  box-shadow:
    inset 0 18px 30px rgba(255, 226, 166, 0.14),
    inset 0 -28px 42px rgba(0, 0, 0, 0.34),
    0 -10px 28px rgba(0, 0, 0, 0.24);
}

.guardian-theater.stage-hidden .stage-platform::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(20, 13, 9, 0.36), transparent 14%, transparent 86%, rgba(20, 13, 9, 0.36)),
    radial-gradient(ellipse at 50% 0, rgba(255, 233, 183, 0.16), transparent 54%);
  pointer-events: none;
}

.guardian-theater.stage-hidden .overhead-lighting {
  top: 4%;
  right: 10.64%;
  left: 10.64%;
  z-index: 5;
  display: grid;
  height: 56%;
}

.guardian-theater.stage-hidden .overhead-beam {
  top: 22px;
  width: min(280px, 22vw);
  height: 47vh;
}

.guardian-theater.stage-hidden .stage-spot.active .overhead-beam {
  opacity: 0.66;
}

.overhead-lighting {
  position: absolute;
  top: 14%;
  right: 12%;
  left: 12%;
  z-index: 2;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  height: 48%;
  pointer-events: none;
}

.stage-spot {
  position: relative;
}

.stage-fixture {
  position: absolute;
  top: 0;
  left: 50%;
  width: 34px;
  height: 30px;
  border: 1px solid rgba(135, 146, 151, 0.66);
  border-radius: 5px 5px 9px 9px;
  background: linear-gradient(180deg, #20252a, #080a0c);
  transform: translateX(-50%);
  box-shadow: 0 6px 10px rgba(0, 0, 0, 0.44);
}

.stage-fixture::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 50%;
  width: 18px;
  height: 7px;
  border-radius: 50%;
  background: rgba(255, 231, 173, 0.26);
  transform: translateX(-50%);
  transition: background 0.2s ease, box-shadow 0.2s ease;
}

.stage-spot.active .stage-fixture::after {
  background: #fff1b9;
  box-shadow: 0 0 14px rgba(255, 224, 142, 0.9);
}

.overhead-beam {
  position: absolute;
  top: 24px;
  left: 50%;
  width: min(430px, 34vw);
  height: 58vh;
  clip-path: polygon(48% 0, 52% 0, 100% 100%, 0 100%);
  background: linear-gradient(180deg, rgba(255, 239, 187, 0.42), rgba(154, 194, 207, 0.06) 74%, transparent 100%);
  filter: blur(10px);
  opacity: 0;
  transform: translateX(-50%);
  mix-blend-mode: screen;
  transition: opacity 0.28s ease;
}

.stage-spot.active .overhead-beam {
  opacity: 0.88;
}

.stage-floor {
  position: absolute;
  top: 52%;
  right: 7%;
  bottom: 18%;
  left: 7%;
  z-index: 1;
  background:
    repeating-linear-gradient(
      to bottom,
      transparent 0,
      transparent 57px,
      rgba(43, 26, 15, 0.28) 58px,
      rgba(255, 228, 178, 0.035) 59px,
      transparent 60px
    ),
    repeating-linear-gradient(90deg, transparent 0 118px, rgba(46, 28, 17, 0.16) 119px 121px),
    linear-gradient(180deg, #76593d 0%, #644a32 62%, #4b3727 100%);
  border-top: 1px solid rgba(237, 208, 158, 0.45);
  box-shadow:
    inset 0 15px 28px rgba(255, 226, 166, 0.12),
    inset 0 -24px 38px rgba(0, 0, 0, 0.26),
    0 -8px 24px rgba(0, 0, 0, 0.22);
}

.stage-floor::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 10%, rgba(255, 234, 183, 0.24), transparent 48%);
}

.stage-front-lip {
  position: absolute;
  right: 7%;
  bottom: 10%;
  left: 7%;
  z-index: 4;
  height: 8%;
  border: 1px solid rgba(138, 103, 67, 0.35);
  border-radius: 0 0 10px 10px;
  background:
    repeating-linear-gradient(90deg, transparent 0 164px, rgba(9, 7, 6, 0.35) 165px 168px),
    linear-gradient(180deg, #32231a 0%, #1d1713 72%, #0b0a09 100%);
  box-shadow:
    inset 0 5px 0 rgba(153, 113, 73, 0.32),
    0 -3px 10px rgba(0, 0, 0, 0.5);
}

.audience-silhouette {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 5;
  height: 11%;
  background:
    radial-gradient(ellipse at 24px 100%, #080a0d 0 26px, transparent 27px) 0 0 / 58px 52px repeat-x,
    linear-gradient(180deg, rgba(5, 7, 9, 0.3), #05070a 75%);
}

.standee-row {
  position: absolute;
  right: 11%;
  bottom: 27%;
  left: 11%;
  z-index: 6;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-items: flex-end;
  height: 50%;
}

.standee-wrap {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
}

.paper-standee {
  --tilt: 0deg;
  --shift-x: 0px;
  --shift-y: 0px;
  --head-lag: 0deg;
  position: relative;
  z-index: 2;
  width: min(22vw, 300px);
  height: var(--standee-height);
  margin-bottom: var(--standee-lever-gap);
  cursor: grab;
  transform:
    translate3d(var(--shift-x), var(--shift-y), 0)
    rotate(var(--tilt));
  transform-origin: 50% 100%;
  transition: filter 0.18s ease;
  filter: drop-shadow(0 20px 12px rgba(0, 0, 0, 0.42));
}

.paper-standee:active {
  cursor: grabbing;
}

.standee-wrap.hovered .paper-standee {
  filter:
    drop-shadow(0 20px 12px rgba(0, 0, 0, 0.42))
    drop-shadow(0 0 14px rgba(255, 226, 157, 0.34))
    drop-shadow(0 0 34px rgba(255, 203, 105, 0.18));
  scale: 1.012;
}

.paper-inner {
  position: absolute;
  inset: 0;
  width: 100%;
  height: auto;
  transform: rotate(var(--head-lag));
  transform-origin: 50% 82%;
}

.standee-sparkles {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.24s ease;
}

.standee-sparkles::before {
  content: '';
  position: absolute;
  inset: 5% 2% 3%;
  border-radius: 48%;
  background: radial-gradient(
    ellipse at 50% 48%,
    rgba(255, 237, 183, 0.14) 0%,
    rgba(255, 215, 126, 0.06) 42%,
    transparent 70%
  );
  filter: blur(5px);
  mix-blend-mode: screen;
}

.standee-wrap.hovered .standee-sparkles,
.standee-wrap.acting .standee-sparkles {
  opacity: 1;
}

.standee-sparkle {
  position: absolute;
  top: var(--sparkle-y);
  left: var(--sparkle-x);
  width: calc(var(--sparkle-size) * 4);
  height: calc(var(--sparkle-size) * 4);
  border-radius: 50%;
  opacity: 0;
  background: radial-gradient(
    circle,
    rgba(255, 248, 207, 0.54) 0%,
    rgba(255, 222, 133, 0.18) 24%,
    transparent 68%
  );
  filter: drop-shadow(0 0 4px rgba(255, 228, 151, 0.72));
  mix-blend-mode: screen;
  transform: translate(-50%, -50%) scale(0.2);
  will-change: transform, opacity;
}

.standee-sparkle.cool {
  background: radial-gradient(
    circle,
    rgba(231, 251, 255, 0.6) 0%,
    rgba(161, 229, 255, 0.2) 24%,
    transparent 68%
  );
  filter: drop-shadow(0 0 4px rgba(166, 231, 255, 0.76));
}

.standee-sparkle::before {
  content: '';
  position: absolute;
  inset: 32%;
  background: #fff8d5;
  clip-path: polygon(
    50% 0%,
    58% 38%,
    100% 50%,
    58% 62%,
    50% 100%,
    42% 62%,
    0% 50%,
    42% 38%
  );
  box-shadow: 0 0 5px rgba(255, 242, 190, 0.95);
  transform: rotate(var(--sparkle-rotation));
}

.standee-sparkle.cool::before {
  background: #e5fbff;
  box-shadow: 0 0 5px rgba(176, 237, 255, 0.95);
}

.standee-sparkle.shape-1::before {
  inset: 38%;
  border-radius: 50%;
  clip-path: none;
}

.standee-sparkle.shape-2::before {
  inset: 34%;
  clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
}

.standee-wrap.hovered .standee-sparkle,
.standee-wrap.acting .standee-sparkle {
  animation:
    standee-sparkle-twinkle var(--sparkle-duration) ease-in-out var(--sparkle-delay) infinite;
}

.character-svg {
  display: none;
}

.character-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  pointer-events: none;
  filter: saturate(0.94) contrast(1.02);
  transition: filter 0.22s ease;
}

.standee-wrap.hovered .character-image {
  filter: saturate(1.04) contrast(1.03) brightness(1.045);
}

.standee-lever {
  position: absolute;
  bottom: 0;
  left: 50%;
  z-index: 1;
  width: 5px;
  height: var(--lever-height, 176px);
  border: 1px solid rgba(196, 172, 127, 0.42);
  border-radius: 3px;
  background: linear-gradient(90deg, #5f4c38, #b08c5f 42%, #4e3c2d);
  transform: translateX(-50%) rotate(var(--lever-angle, 0deg));
  transform-origin: 50% 100%;
  box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.32);
}

.standee-foot {
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 44%;
  height: 15px;
  background: linear-gradient(180deg, #6d4b2f, #2a1b13);
  border: 1px solid rgba(199, 161, 105, 0.5);
  transform: translateX(-50%) skewX(-7deg);
  box-shadow: 0 7px 10px rgba(0, 0, 0, 0.4);
  z-index: 4;
}

.standee-wrap.acting .paper-standee {
  animation: standee-bow 0.72s ease-in-out;
}

.theater-close {
  position: absolute;
  top: 18px;
  right: 22px;
  z-index: 10;
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  padding: 0;
  border: 1px solid rgba(176, 215, 235, 0.3);
  border-radius: 50%;
  background: rgba(6, 12, 18, 0.62);
  color: rgba(220, 237, 247, 0.78);
  font-size: 21px;
  cursor: pointer;
}

@keyframes standee-bow {
  0%, 100% { transform: translate3d(var(--shift-x), var(--shift-y), 0) rotate(var(--tilt)); }
  34% { transform: translate3d(var(--shift-x), calc(var(--shift-y) - 16px), 0) rotate(calc(var(--tilt) - 9deg)); }
  62% { transform: translate3d(var(--shift-x), calc(var(--shift-y) + 4px), 0) rotate(calc(var(--tilt) + 3deg)); }
}

@keyframes standee-sparkle-twinkle {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.18) rotate(0deg);
  }
  18% {
    opacity: 1;
    transform: translate(-50%, -50%) translateY(-3px) scale(1) rotate(10deg);
  }
  46% {
    opacity: 0.16;
    transform: translate(-50%, -50%) translateY(-6px) scale(0.48) rotate(18deg);
  }
  68% {
    opacity: 0.82;
    transform: translate(-50%, -50%) translateY(-8px) scale(0.78) rotate(28deg);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) translateY(var(--sparkle-drift)) scale(0.12) rotate(40deg);
  }
}

@keyframes open-curtain-left {
  0% {
    z-index: 7;
    width: 45%;
  }
  99% {
    z-index: 7;
  }
  100% {
    z-index: 4;
    width: 5.64%;
  }
}

@keyframes open-curtain-right {
  0% {
    z-index: 7;
    width: 45%;
  }
  99% {
    z-index: 7;
  }
  100% {
    z-index: 4;
    width: 5.64%;
  }
}

@keyframes close-curtain-left {
  from {
    z-index: 8;
    width: 5.64%;
  }
  to {
    z-index: 8;
    width: 45%;
  }
}

@keyframes close-curtain-right {
  from {
    z-index: 8;
    width: 5.64%;
  }
  to {
    z-index: 8;
    width: 45%;
  }
}

@media (max-width: 760px) {
  .guardian-theater {
    --stage-screen-bottom: calc(8% + var(--lever-midpoint));
  }

  .standee-row {
    right: 2%;
    bottom: 8%;
    left: 2%;
    height: 60%;
  }

  .standee-wrap {
    width: 100%;
  }

  .paper-standee {
    width: 94%;
    height: auto;
    aspect-ratio: 1;
  }

}

@media (prefers-reduced-motion: reduce) {
  .guardian-theater.stage-hidden .stage-curtain-left,
  .guardian-theater.stage-hidden .stage-curtain-right {
    animation-duration: 0.01ms;
    animation-delay: 0ms;
  }

  .standee-sparkle {
    display: none;
  }

  .standee-wrap.hovered .paper-standee {
    scale: 1;
  }
}
</style>
