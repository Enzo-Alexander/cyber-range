<template>
  <div
    ref="rootRef"
    class="library-journey"
    :class="{ ready: libraryReady }"
    @mousemove="onPointerMove"
    @mouseleave="clearBookHover"
    @click="onRootClick"
  >
    <canvas ref="canvasRef" class="journey-canvas"></canvas>
    <div class="journey-flash" :class="{ active: flashActive }"></div>
    <div class="journey-exit-veil" :class="{ active: exitVeilActive }"></div>
    <div class="journey-handoff" :class="{ active: exitHandoffActive }"></div>

    <button
      v-if="!exiting"
      class="journey-exit"
      type="button"
      aria-label="退出图书馆"
      title="退出"
      @click="beginExit"
    >×</button>

    <template v-if="libraryReady">
      <button
        v-if="facingSide !== 'left'"
        class="shelf-arrow shelf-arrow-left"
        type="button"
        aria-label="向左转，面向左侧书架"
        @click="turn(-1)"
      >‹</button>
      <button
        v-if="facingSide !== 'right'"
        class="shelf-arrow shelf-arrow-right"
        type="button"
        aria-label="向右转，面向右侧书架"
        @click="turn(1)"
      >›</button>

      <div
        v-if="hoverTitle"
        class="book-label"
        :style="{ left: `${labelX}px`, top: `${labelY}px` }"
      >{{ hoverTitle }}</div>
    </template>

    <div
      v-if="readerOpen"
      class="book-reader"
      @click.self="closeReader"
    >
      <div class="reader-shell">
        <div class="reader-head">
          <div>
            <span class="reader-title">{{ readerBook?.title }}</span>
            <span class="reader-author">{{ readerBook?.author }}</span>
          </div>
          <button class="reader-close" type="button" @click="closeReader">×</button>
        </div>

        <div
          v-if="currentReaderPage"
          class="reader-book"
          :class="{
            'flipping-next': flipDirection === 'next',
            'flipping-prev': flipDirection === 'prev',
          }"
        >
          <article class="reader-page reader-page-left">
            <template v-if="leftReaderPage">
              <p class="reader-text">{{ leftReaderPage.content }}</p>
              <img v-if="leftReaderPage.image" class="reader-image" :src="bookImageUrl(leftReaderPage.image)" alt="" />
            </template>
            <div v-else class="reader-cover">
              <span>CyberRange Library</span>
              <strong>{{ readerBook?.title }}</strong>
            </div>
            <span class="reader-page-no">{{ Math.max(1, readerPageIndex) }}</span>
          </article>

          <article class="reader-page reader-page-right">
            <p class="reader-text">{{ currentReaderPage.content }}</p>
            <img v-if="currentReaderPage.image" class="reader-image" :src="bookImageUrl(currentReaderPage.image)" alt="" />
            <span class="reader-page-no">{{ readerPageIndex + 1 }}</span>
          </article>

          <div v-if="flipDirection && flipPage" class="reader-flip-sheet" :class="flipDirection">
            <p class="reader-text">{{ flipPage.content }}</p>
            <img v-if="flipPage.image" class="reader-image" :src="bookImageUrl(flipPage.image)" alt="" />
          </div>
        </div>

        <div class="reader-controls">
          <button
            class="reader-nav"
            type="button"
            :disabled="readerPageIndex <= 0 || Boolean(flipDirection)"
            @click="turnReaderPage(-1)"
          >‹ 上一页</button>
          <span>{{ readerPageIndex + 1 }} / {{ readerBook?.pages.length }}</span>
          <button
            class="reader-nav"
            type="button"
            :disabled="readerPageIndex >= (readerBook?.pages.length ?? 1) - 1 || Boolean(flipDirection)"
            @click="turnReaderPage(1)"
          >下一页 ›</button>
        </div>
      </div>
    </div>

    <GuardianTheater
      v-if="libraryReady || holdTheaterDuringExit"
      ref="theaterRef"
      @close="beginExit"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import * as THREE from 'three'
import GuardianTheater from './GuardianTheater.vue'
import {
  booksApi,
  bookImageUrl,
  type BookDetail,
  type BookPage,
  type BookSummary,
} from '../api/books'

const emit = defineEmits<{ close: [] }>()
type GuardianTheaterHandle = {
  closeWithAnimation: () => void
}

const rootRef = ref<HTMLElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const theaterRef = ref<GuardianTheaterHandle | null>(null)
const libraryReady = ref(false)
const flashActive = ref(false)
const exiting = ref(false)
const holdTheaterDuringExit = ref(false)
const exitVeilActive = ref(false)
const exitHandoffActive = ref(false)
const hoverTitle = ref('')
const facingSide = ref<'front' | 'left' | 'right'>('front')
const readerOpen = ref(false)
const readerBook = ref<BookDetail | null>(null)
const readerPageIndex = ref(0)
const flipDirection = ref<'next' | 'prev' | null>(null)
const flipPage = ref<BookPage | null>(null)
const labelX = ref(0)
const labelY = ref(0)

const currentReaderPage = computed(
  () => readerBook.value?.pages[readerPageIndex.value] ?? null,
)
const leftReaderPage = computed(
  () => readerBook.value?.pages[readerPageIndex.value - 1] ?? null,
)

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let tunnelGroup: THREE.Group | null = null
let libraryGroup: THREE.Group | null = null
let lightRig: THREE.Group | null = null
let lightHalo: THREE.Sprite | null = null
let lightCore: THREE.Mesh | null = null
let raycaster: THREE.Raycaster | null = null
let animationFrame = 0
let startTime = 0
let currentYaw = 0
let targetYaw = 0
let hoveredBook: THREE.Mesh | null = null
let glowTexture: THREE.CanvasTexture | null = null
let exitMode = false
let exitStartTime = 0
let exitEnding = false
let exitHandoffTriggered = false
let exitStageTimer = 0
let exitEmitTimer = 0
let pageFlipTimer = 0
let pageFlipCleanupTimer = 0
const pointer = new THREE.Vector2()
const bookMeshes: THREE.Mesh[] = []

const tunnelBackground = new THREE.Color(0x02050c)
const exitBackground = new THREE.Color(0xe6c48d)
const libraryBackground = new THREE.Color(0x2c1b12)

function createGlowTexture() {
  const canvas = document.createElement('canvas')
  canvas.width = 256
  canvas.height = 256
  const context = canvas.getContext('2d')
  if (context) {
    const gradient = context.createRadialGradient(128, 128, 0, 128, 128, 128)
    gradient.addColorStop(0, 'rgba(255, 248, 220, 1)')
    gradient.addColorStop(0.16, 'rgba(190, 230, 255, 0.9)')
    gradient.addColorStop(0.48, 'rgba(72, 145, 255, 0.34)')
    gradient.addColorStop(1, 'rgba(31, 78, 160, 0)')
    context.fillStyle = gradient
    context.fillRect(0, 0, 256, 256)
  }
  return new THREE.CanvasTexture(canvas)
}

function createTunnelRing(radius: number, material: THREE.Material) {
  const positions: number[] = []
  const segments = 96
  for (let index = 0; index < segments; index += 1) {
    const angle = (index / segments) * Math.PI * 2
    const nextAngle = ((index + 1) / segments) * Math.PI * 2
    positions.push(
      Math.cos(angle) * radius,
      Math.sin(angle) * radius,
      0,
      Math.cos(nextAngle) * radius,
      Math.sin(nextAngle) * radius,
      0,
    )
  }

  const tickCount = 48
  for (let index = 0; index < tickCount; index += 1) {
    const angle = (index / tickCount) * Math.PI * 2
    const innerRadius = radius - 0.13
    const outerRadius = radius + (index % 6 === 0 ? 0.24 : 0.13)
    positions.push(
      Math.cos(angle) * innerRadius,
      Math.sin(angle) * innerRadius,
      0,
      Math.cos(angle) * outerRadius,
      Math.sin(angle) * outerRadius,
      0,
    )
  }

  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  return new THREE.LineSegments(geometry, material)
}

function buildTunnel() {
  const group = new THREE.Group()
  const ringMaterial = new THREE.LineBasicMaterial({
    color: 0x3f8cff,
    transparent: true,
    opacity: 0.64,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  })

  for (let index = 0; index < 30; index += 1) {
    const ring = createTunnelRing(4.6, ringMaterial)
    ring.position.z = -index * 2.35 - 1
    ring.rotation.z = index * 0.055
    group.add(ring)
  }

  const particles: number[] = []
  for (let index = 0; index < 420; index += 1) {
    const angle = Math.random() * Math.PI * 2
    const radius = 4.1 + Math.random() * 0.7
    particles.push(
      Math.cos(angle) * radius,
      Math.sin(angle) * radius,
      -Math.random() * 72,
    )
  }
  const particleGeometry = new THREE.BufferGeometry()
  particleGeometry.setAttribute('position', new THREE.Float32BufferAttribute(particles, 3))
  group.add(new THREE.Points(
    particleGeometry,
    new THREE.PointsMaterial({
      color: 0xb9ddff,
      size: 0.035,
      transparent: true,
      opacity: 0.78,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
  ))

  return group
}

function buildLightRig() {
  const group = new THREE.Group()
  glowTexture = createGlowTexture()
  lightHalo = new THREE.Sprite(new THREE.SpriteMaterial({
    map: glowTexture,
    color: 0xcfeaff,
    transparent: true,
    opacity: 0.82,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  }))
  lightHalo.scale.setScalar(4.2)
  group.add(lightHalo)

  lightCore = new THREE.Mesh(
    new THREE.SphereGeometry(0.24, 24, 16),
    new THREE.MeshBasicMaterial({ color: 0xfff8dc }),
  )
  group.add(lightCore)
  group.position.z = 2
  return group
}

function createBookMaterial(index: number) {
  const colors = [0x8b332d, 0x294c66, 0x405d35, 0x8a672f, 0x4f345f, 0x70412d, 0x315c58]
  return new THREE.MeshStandardMaterial({
    color: colors[index % colors.length],
    roughness: 0.82,
    metalness: 0.03,
  })
}

function createWoodTexture() {
  const canvas = document.createElement('canvas')
  canvas.width = 256
  canvas.height = 256
  const context = canvas.getContext('2d')
  if (context) {
    context.fillStyle = '#815433'
    context.fillRect(0, 0, 256, 256)
    for (let index = 0; index < 90; index += 1) {
      const y = Math.random() * 256
      context.beginPath()
      context.moveTo(0, y)
      context.bezierCurveTo(
        64,
        y + (Math.random() - 0.5) * 18,
        176,
        y + (Math.random() - 0.5) * 14,
        256,
        y + (Math.random() - 0.5) * 10,
      )
      context.strokeStyle = `rgba(45, 22, 10, ${0.08 + Math.random() * 0.16})`
      context.lineWidth = 0.5 + Math.random() * 1.4
      context.stroke()
    }
  }
  const texture = new THREE.CanvasTexture(canvas)
  texture.wrapS = THREE.RepeatWrapping
  texture.wrapT = THREE.RepeatWrapping
  texture.repeat.set(2.2, 2.2)
  texture.colorSpace = THREE.SRGBColorSpace
  return texture
}

function buildShelf(books: BookSummary[], width = 10.2, height = 6.8) {
  const group = new THREE.Group()
  const woodTexture = createWoodTexture()
  const wood = new THREE.MeshStandardMaterial({
    color: 0x9a6a43,
    map: woodTexture,
    roughness: 0.84,
    metalness: 0.02,
  })
  const woodEdge = new THREE.MeshStandardMaterial({
    color: 0x704629,
    map: woodTexture,
    roughness: 0.78,
  })
  const labelMaterial = new THREE.MeshStandardMaterial({
    color: 0xd7c49d,
    roughness: 0.68,
  })
  const bandMaterial = new THREE.MeshStandardMaterial({
    color: 0xb99455,
    roughness: 0.52,
    metalness: 0.28,
  })

  const back = new THREE.Mesh(new THREE.BoxGeometry(width, height, 0.18), wood)
  back.position.z = -0.31
  group.add(back)

  const sideGeometry = new THREE.BoxGeometry(0.28, height + 0.16, 0.92)
  for (const x of [-width / 2 - 0.04, width / 2 + 0.04]) {
    const post = new THREE.Mesh(sideGeometry, woodEdge)
    post.position.set(x, 0, 0.16)
    group.add(post)
  }

  const crown = new THREE.Mesh(
    new THREE.BoxGeometry(width + 0.56, 0.3, 1.04),
    woodEdge,
  )
  crown.position.set(0, height / 2 + 0.14, 0.16)
  group.add(crown)

  const base = new THREE.Mesh(
    new THREE.BoxGeometry(width + 0.4, 0.26, 0.96),
    woodEdge,
  )
  base.position.set(0, -height / 2 - 0.1, 0.16)
  group.add(base)

  const rows = 4
  const rowHeight = height / rows
  for (let row = 0; row < rows; row += 1) {
    const y = -height / 2 + row * rowHeight
    const shelf = new THREE.Mesh(
      new THREE.BoxGeometry(width - 0.04, 0.14, 0.92),
      woodEdge,
    )
    shelf.position.set(0, y, 0.18)
    group.add(shelf)
  }

  for (const x of [-width / 4, width / 4]) {
    const divider = new THREE.Mesh(
      new THREE.BoxGeometry(0.1, height - 0.2, 0.76),
      wood,
    )
    divider.position.set(x, 0, 0.05)
    group.add(divider)
  }

  const maxBooksPerRow = 12
  for (let row = 0; row < rows; row += 1) {
    const y = -height / 2 + row * rowHeight + 0.34
    const rowBooks = books.slice(
      row * maxBooksPerRow,
      (row + 1) * maxBooksPerRow,
    )
    rowBooks.forEach((bookData, index) => {
      const bookHeight = rowHeight * (0.52 + Math.random() * 0.24)
      const slotWidth = width / (rowBooks.length + 1)
      const bookWidth = Math.min(0.92, slotWidth * (0.55 + Math.random() * 0.18))
      const bookDepth = 0.36 + Math.random() * 0.16
      const book = new THREE.Mesh(
        new THREE.BoxGeometry(bookWidth, bookHeight, bookDepth),
        createBookMaterial(row * maxBooksPerRow + index),
      )
      const x = -width / 2 + (index + 1) * slotWidth
      book.position.set(x, y + bookHeight / 2, 0.395)
      book.rotation.z = (Math.random() - 0.5) * 0.035
      book.userData.baseZ = book.position.z
      book.userData.offset = 0
      book.userData.targetOffset = 0
      book.userData.bookId = bookData.id
      book.userData.title = bookData.title

      const label = new THREE.Mesh(
        new THREE.BoxGeometry(bookWidth * 0.68, 0.085, 0.016),
        labelMaterial,
      )
      label.position.set(0, bookHeight * 0.04, bookDepth / 2 + 0.01)
      book.add(label)

      if (index % 3 === 0) {
        for (const offset of [-0.32, 0.31]) {
          const band = new THREE.Mesh(
            new THREE.BoxGeometry(bookWidth + 0.008, 0.025, 0.02),
            bandMaterial,
          )
          band.position.set(0, bookHeight * offset, bookDepth / 2 + 0.012)
          book.add(band)
        }
      }

      bookMeshes.push(book)
      group.add(book)
    })
  }

  return group
}

function buildLibrary(books: BookSummary[]) {
  const group = new THREE.Group()
  group.visible = false
  const frontBooks = books.filter((_, index) => index % 3 === 0)
  const leftBooks = books.filter((_, index) => index % 3 === 1)
  const rightBooks = books.filter((_, index) => index % 3 === 2)

  const wallMaterial = new THREE.MeshStandardMaterial({
    color: 0x4a2d20,
    roughness: 0.94,
  })
  const floorMaterial = new THREE.MeshStandardMaterial({
    color: 0x2d1b13,
    roughness: 0.9,
  })
  const ceilingMaterial = new THREE.MeshStandardMaterial({
    color: 0x342116,
    roughness: 0.95,
  })

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(22, 24), floorMaterial)
  floor.rotation.x = -Math.PI / 2
  floor.position.y = -1.5
  group.add(floor)

  const rug = new THREE.Mesh(
    new THREE.PlaneGeometry(8.5, 12),
    new THREE.MeshStandardMaterial({
      color: 0x44251b,
      roughness: 0.96,
    }),
  )
  rug.rotation.x = -Math.PI / 2
  rug.position.set(0, -1.47, -1.8)
  group.add(rug)

  const ceiling = new THREE.Mesh(new THREE.PlaneGeometry(22, 24), ceilingMaterial)
  ceiling.rotation.x = Math.PI / 2
  ceiling.position.y = 7.4
  group.add(ceiling)

  const frontWall = new THREE.Mesh(new THREE.PlaneGeometry(22, 10), wallMaterial)
  frontWall.position.set(0, 2.8, -9.2)
  group.add(frontWall)

  const leftWall = new THREE.Mesh(new THREE.PlaneGeometry(24, 10), wallMaterial)
  leftWall.rotation.y = Math.PI / 2
  leftWall.position.set(-10.2, 2.8, 0)
  group.add(leftWall)

  const rightWall = new THREE.Mesh(new THREE.PlaneGeometry(24, 10), wallMaterial)
  rightWall.rotation.y = -Math.PI / 2
  rightWall.position.set(10.2, 2.8, 0)
  group.add(rightWall)

  const frontShelf = buildShelf(frontBooks)
  frontShelf.position.set(0, 2.35, -8.45)
  group.add(frontShelf)

  const leftShelf = buildShelf(leftBooks)
  leftShelf.rotation.y = Math.PI / 2
  leftShelf.position.set(-9.55, 2.35, 0)
  group.add(leftShelf)

  const rightShelf = buildShelf(rightBooks)
  rightShelf.rotation.y = -Math.PI / 2
  rightShelf.position.set(9.55, 2.35, 0)
  group.add(rightShelf)

  const ambient = new THREE.AmbientLight(0xffd7a3, 1.45)
  group.add(ambient)

  const centerLight = new THREE.PointLight(0xffc477, 42, 30, 1.7)
  centerLight.position.set(0, 6.4, 2.5)
  group.add(centerLight)

  const frontLight = new THREE.PointLight(0xffb35e, 34, 24, 1.75)
  frontLight.position.set(0, 4.8, -4)
  group.add(frontLight)

  for (const x of [-6.8, 6.8]) {
    const sideLight = new THREE.PointLight(0xffa64f, 24, 20, 1.85)
    sideLight.position.set(x, 4.4, 1)
    group.add(sideLight)
  }

  return group
}

function switchToLibrary() {
  if (!scene || !camera || !tunnelGroup || !libraryGroup) return
  tunnelGroup.visible = false
  libraryGroup.visible = true
  scene.background = libraryBackground.clone()
  scene.fog = new THREE.FogExp2(0x2c1b12, 0.014)
  camera.fov = 55
  camera.updateProjectionMatrix()
  camera.position.set(0, 2.65, 0)
  camera.rotation.set(-0.035, 0, 0)
  currentYaw = 0
  targetYaw = 0
  facingSide.value = 'front'
  libraryReady.value = true
  flashActive.value = true
  exitStageTimer = window.setTimeout(() => {
    flashActive.value = false
  }, 420)
}

function beginExit() {
  if (exiting.value) return
  exiting.value = true
  holdTheaterDuringExit.value = true
  libraryReady.value = false
  clearBookHover()
  exitVeilActive.value = true

  window.setTimeout(() => {
    if (!scene || !camera || !tunnelGroup || !libraryGroup || !lightRig || !lightHalo || !lightCore) {
      holdTheaterDuringExit.value = false
      emit('close')
      return
    }
    libraryGroup.visible = false
    tunnelGroup.visible = true
    lightRig.visible = true
    lightRig.position.z = -58
    lightHalo.scale.setScalar(24)
    lightHalo.material.opacity = 1
    lightCore.scale.setScalar(3.8)
    scene.background = tunnelBackground.clone()
    scene.fog = null
    camera.position.set(0, 0, -30)
    camera.rotation.set(0, 0, 0)
    camera.fov = 68
    camera.updateProjectionMatrix()
    exitMode = true
    exitStartTime = performance.now()
    exitHandoffTriggered = false
    exitVeilActive.value = false
    holdTheaterDuringExit.value = false
    exitHandoffActive.value = false
  }, 780)
}

function turn(direction: -1 | 1) {
  targetYaw = THREE.MathUtils.clamp(
    targetYaw - direction * Math.PI / 2,
    -Math.PI / 2,
    Math.PI / 2,
  )
  clearBookHover()
}

function clearBookHover() {
  if (hoveredBook) {
    hoveredBook.userData.targetOffset = 0
  }
  hoveredBook = null
  hoverTitle.value = ''
  if (canvasRef.value) canvasRef.value.style.cursor = 'default'
}

function pickBookAt(clientX: number, clientY: number) {
  if (!camera || !raycaster) return null
  pointer.x = (clientX / window.innerWidth) * 2 - 1
  pointer.y = -(clientY / window.innerHeight) * 2 + 1
  raycaster.setFromCamera(pointer, camera)
  return (raycaster.intersectObjects(bookMeshes, false)[0]?.object as THREE.Mesh | undefined) ?? null
}

async function openBook(bookId: number) {
  clearBookHover()
  try {
    const book = await booksApi.get(bookId)
    if (!book.pages.length) return
    readerBook.value = book
    readerPageIndex.value = 0
    flipDirection.value = null
    flipPage.value = null
    readerOpen.value = true
  } catch {
    // 读取失败时保持图书馆视图。
  }
}

function closeReader() {
  clearTimeout(pageFlipTimer)
  clearTimeout(pageFlipCleanupTimer)
  flipDirection.value = null
  flipPage.value = null
  readerOpen.value = false
}

function turnReaderPage(direction: -1 | 1) {
  if (!readerBook.value || flipDirection.value || !currentReaderPage.value) return
  const nextIndex = readerPageIndex.value + direction
  if (nextIndex < 0 || nextIndex >= readerBook.value.pages.length) return

  flipPage.value = currentReaderPage.value
  flipDirection.value = direction > 0 ? 'next' : 'prev'
  clearTimeout(pageFlipTimer)
  clearTimeout(pageFlipCleanupTimer)
  pageFlipTimer = window.setTimeout(() => {
    readerPageIndex.value = nextIndex
  }, 340)
  pageFlipCleanupTimer = window.setTimeout(() => {
    flipDirection.value = null
    flipPage.value = null
  }, 760)
}

function onRootClick(event: MouseEvent) {
  if (!libraryReady.value || readerOpen.value || exiting.value) return
  const target = event.target as HTMLElement | null
  if (target?.closest('.guardian-theater')) return
  if (target?.closest('button')) return
  const book = pickBookAt(event.clientX, event.clientY)
  const bookId = Number(book?.userData.bookId ?? 0)
  if (bookId) openBook(bookId)
}

function onPointerMove(event: MouseEvent) {
  if ((event.target as HTMLElement | null)?.closest('.guardian-theater')) return
  if (
    !libraryReady.value
    || readerOpen.value
    || !camera
    || !raycaster
    || !canvasRef.value
  ) return

  const target = event.target as HTMLElement | null
  if (target?.closest('button')) {
    clearBookHover()
    return
  }

  const hit = pickBookAt(event.clientX, event.clientY) ?? undefined

  if (hit !== hoveredBook) {
    if (hoveredBook) hoveredBook.userData.targetOffset = 0
    hoveredBook = hit ?? null
    if (hoveredBook) hoveredBook.userData.targetOffset = 0.32
  }

  if (hoveredBook) {
    hoverTitle.value = String(hoveredBook.userData.title ?? '')
    labelX.value = Math.min(event.clientX + 18, window.innerWidth - 220)
    labelY.value = Math.max(24, event.clientY - 42)
    canvasRef.value.style.cursor = 'pointer'
  } else {
    hoverTitle.value = ''
    canvasRef.value.style.cursor = 'default'
  }
}

function onResize() {
  if (!renderer || !camera) return
  const width = window.innerWidth
  const height = window.innerHeight
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(width, height, false)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
}

function easeInOutCubic(value: number) {
  return value < 0.5
    ? 4 * value * value * value
    : 1 - Math.pow(-2 * value + 2, 3) / 2
}

function animate(now: number) {
  if (!renderer || !scene || !camera) return
  if (!startTime) startTime = now
  const elapsed = (now - startTime) / 1000
  const delta = Math.min(0.05, 1 / 60)

  if (exiting.value) {
    if (
      exitMode
      && tunnelGroup
      && lightRig
      && lightHalo
      && lightCore
    ) {
      const reverseElapsed = Math.min(1, (now - exitStartTime) / 2800)
      const reverseProgress = Math.pow(reverseElapsed, 1.35)
      camera.position.z = -30 + 38 * reverseProgress
      camera.fov = THREE.MathUtils.lerp(68, 55, reverseProgress)
      camera.updateProjectionMatrix()
      lightHalo.scale.setScalar(THREE.MathUtils.lerp(24, 4.2, reverseProgress))
      lightHalo.material.opacity = THREE.MathUtils.lerp(1, 0.72, reverseProgress)
      lightCore.scale.setScalar(THREE.MathUtils.lerp(3.8, 1, reverseProgress))
      scene.background = tunnelBackground.clone()

      if (reverseProgress > 0.72 && !exitHandoffTriggered) {
        exitHandoffTriggered = true
        exitHandoffActive.value = true
      }

      if (reverseProgress >= 1 && !exitEnding) {
        exitEnding = true
        exitVeilActive.value = true
        exitEmitTimer = window.setTimeout(() => {
          emit('close')
        }, 650)
      }
    }
  } else if (!libraryReady.value && tunnelGroup && lightRig && lightHalo && lightCore) {
    const cameraProgress = easeInOutCubic(Math.min(1, elapsed / 3.7))
    camera.position.z = 8 - 38 * cameraProgress
    lightRig.position.z = 2 - 58 * easeInOutCubic(Math.min(1, elapsed / 3.2))

    const glowProgress = THREE.MathUtils.clamp((elapsed - 2.7) / 1.7, 0, 1)
    const glowScale = THREE.MathUtils.lerp(4.2, 24, glowProgress * glowProgress)
    lightHalo.scale.setScalar(glowScale)
    lightHalo.material.opacity = THREE.MathUtils.lerp(0.72, 1, glowProgress)
    lightCore.scale.setScalar(THREE.MathUtils.lerp(1, 3.8, glowProgress))
    camera.fov = THREE.MathUtils.lerp(55, 68, glowProgress)
    camera.updateProjectionMatrix()

    const backgroundProgress = THREE.MathUtils.clamp((elapsed - 3.5) / 1.15, 0, 1)
    scene.background = tunnelBackground.clone().lerp(
      exitBackground,
      easeInOutCubic(backgroundProgress),
    )

    if (elapsed >= 4.7) switchToLibrary()
  } else if (libraryReady.value) {
    currentYaw += (targetYaw - currentYaw) * Math.min(1, delta * 5.2)
    camera.rotation.y = currentYaw

    if (currentYaw > 1.02 && facingSide.value !== 'left') {
      facingSide.value = 'left'
    } else if (currentYaw < -1.02 && facingSide.value !== 'right') {
      facingSide.value = 'right'
    } else if (Math.abs(currentYaw) < 0.34 && facingSide.value !== 'front') {
      facingSide.value = 'front'
    }

    for (const book of bookMeshes) {
      const current = Number(book.userData.offset ?? 0)
      const target = Number(book.userData.targetOffset ?? 0)
      const next = current + (target - current) * Math.min(1, delta * 8)
      book.userData.offset = next
      book.position.z = Number(book.userData.baseZ ?? 0) + next
    }
  }

  renderer.render(scene, camera)
  animationFrame = requestAnimationFrame(animate)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape') return
  if (readerOpen.value) {
    closeReader()
  } else if (libraryReady.value && !exiting.value) {
    theaterRef.value?.closeWithAnimation()
  } else {
    beginExit()
  }
}

function disposeScene() {
  cancelAnimationFrame(animationFrame)
  clearTimeout(exitStageTimer)
  clearTimeout(exitEmitTimer)
  clearTimeout(pageFlipTimer)
  clearTimeout(pageFlipCleanupTimer)
  window.removeEventListener('resize', onResize)
  window.removeEventListener('keydown', onKeydown)

  if (scene) {
    const geometries = new Set<THREE.BufferGeometry>()
    const materials = new Set<THREE.Material>()
    const textures = new Set<THREE.Texture>()
    scene.traverse((object) => {
      if (object instanceof THREE.Mesh || object instanceof THREE.Line || object instanceof THREE.Points) {
        geometries.add(object.geometry)
        const objectMaterials = Array.isArray(object.material) ? object.material : [object.material]
        for (const material of objectMaterials) {
          materials.add(material)
          const map = (material as THREE.MeshStandardMaterial).map
          if (map) textures.add(map)
        }
      }
    })
    for (const geometry of geometries) geometry.dispose()
    for (const material of materials) material.dispose()
    for (const texture of textures) texture.dispose()
  }

  glowTexture?.dispose()
  renderer?.dispose()
  renderer = null
  scene = null
  camera = null
  tunnelGroup = null
  libraryGroup = null
  lightRig = null
  lightHalo = null
  lightCore = null
  raycaster = null
  bookMeshes.length = 0
}

onMounted(async () => {
  const canvas = canvasRef.value
  if (!canvas) return

  renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
    powerPreference: 'high-performance',
  })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(window.innerWidth, window.innerHeight, false)

  scene = new THREE.Scene()
  scene.background = tunnelBackground.clone()

  camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 200)
  camera.position.set(0, 0, 8)
  camera.rotation.order = 'YXZ'

  raycaster = new THREE.Raycaster()
  tunnelGroup = buildTunnel()
  lightRig = buildLightRig()
  let books: BookSummary[] = []
  try {
    books = await booksApi.list()
  } catch {
    books = []
  }
  libraryGroup = buildLibrary(books)
  scene.add(tunnelGroup, lightRig, libraryGroup)

  window.addEventListener('resize', onResize)
  window.addEventListener('keydown', onKeydown)
  animationFrame = requestAnimationFrame(animate)
})

onBeforeUnmount(disposeScene)
</script>

<style scoped>
.library-journey {
  position: fixed;
  inset: 0;
  z-index: 200;
  overflow: hidden;
  background: #02050c;
  pointer-events: auto;
  animation: journey-appear 0.45s ease-out both;
}

.journey-canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.journey-flash {
  position: absolute;
  inset: 0;
  background: #fff2cf;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.5s ease;
}

.journey-flash.active {
  opacity: 0.9;
}

.journey-exit-veil {
  position: absolute;
  inset: 0;
  z-index: 20;
  background: #02050c;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.72s ease;
}

.journey-exit-veil.active {
  opacity: 1;
}

.journey-handoff {
  position: absolute;
  inset: 0;
  z-index: 4;
  pointer-events: none;
  opacity: 0;
  background: repeating-linear-gradient(
    to bottom,
    transparent 0,
    transparent 29px,
    rgba(104, 201, 255, 0.2) 30px,
    transparent 32px,
    transparent 67px,
    rgba(255, 255, 255, 0.1) 68px,
    transparent 70px
  );
  mix-blend-mode: screen;
  transition: opacity 0.35s ease;
}

.journey-handoff::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(99, 195, 255, 0.14) 22%,
    transparent 25%,
    transparent 58%,
    rgba(255, 255, 255, 0.13) 60%,
    transparent 63%
  );
  animation: handoff-tear 0.22s steps(2, end) infinite;
}

.journey-handoff.active {
  opacity: 0.86;
  animation: handoff-jitter 0.18s steps(2, end) infinite;
}

.journey-exit {
  position: absolute;
  top: 18px;
  right: 22px;
  z-index: 5;
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  padding: 0;
  border: 1px solid rgba(244, 218, 173, 0.34);
  border-radius: 50%;
  background: rgba(40, 24, 16, 0.45);
  color: rgba(244, 218, 173, 0.78);
  font-size: 21px;
  line-height: 1;
  cursor: pointer;
  backdrop-filter: blur(6px);
}

.journey-exit:hover {
  border-color: rgba(255, 232, 191, 0.8);
  color: #fff2cf;
}

.shelf-arrow {
  position: absolute;
  top: 50%;
  z-index: 4;
  display: grid;
  place-items: center;
  width: 52px;
  height: 88px;
  padding: 0;
  border: 1px solid rgba(241, 210, 160, 0.28);
  background: rgba(35, 20, 13, 0.36);
  color: rgba(255, 233, 198, 0.8);
  font-family: Georgia, serif;
  font-size: 46px;
  line-height: 1;
  cursor: pointer;
  transform: translateY(-50%);
  backdrop-filter: blur(5px);
  transition: 0.18s ease;
}

.shelf-arrow:hover {
  border-color: rgba(255, 226, 175, 0.7);
  background: rgba(71, 42, 25, 0.58);
  color: #fff4dc;
}

.shelf-arrow-left {
  left: 18px;
  border-radius: 0 8px 8px 0;
}

.shelf-arrow-right {
  right: 18px;
  border-radius: 8px 0 0 8px;
}

.book-label {
  position: fixed;
  z-index: 6;
  max-width: 200px;
  padding: 7px 10px;
  border-left: 2px solid #d7a45b;
  background: rgba(37, 22, 14, 0.82);
  color: #f5ddae;
  font-family: 'Microsoft YaHei', system-ui, sans-serif;
  font-size: 12px;
  line-height: 1.45;
  pointer-events: none;
  backdrop-filter: blur(5px);
}

.book-reader {
  position: fixed;
  inset: 0;
  z-index: 10;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(13, 8, 5, 0.74);
  backdrop-filter: blur(10px);
}

.reader-shell {
  width: min(1180px, 96vw);
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.reader-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  color: #f2d9a8;
}

.reader-title {
  display: block;
  font-family: Georgia, 'Microsoft YaHei', serif;
  font-size: 24px;
  font-weight: 700;
}

.reader-author {
  display: block;
  margin-top: 4px;
  color: rgba(239, 210, 158, 0.58);
  font-family: var(--mono);
  font-size: 10px;
}

.reader-close {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  padding: 0;
  border: 1px solid rgba(239, 210, 158, 0.32);
  border-radius: 50%;
  background: rgba(42, 26, 17, 0.7);
  color: #f2d9a8;
  font-size: 21px;
  cursor: pointer;
}

.reader-book {
  position: relative;
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: min(74vh, 760px);
  perspective: 2200px;
  transform-style: preserve-3d;
  filter: drop-shadow(0 30px 40px rgba(0, 0, 0, 0.52));
}

.reader-book::before {
  content: '';
  position: absolute;
  inset: 8px -7px -12px 9px;
  z-index: -1;
  border: 1px solid rgba(151, 116, 70, 0.7);
  border-radius: 7px;
  background: #c9a874;
  box-shadow:
    0 4px 0 #b49262,
    0 8px 0 #a17d50,
    0 14px 24px rgba(0, 0, 0, 0.3);
}

.reader-book::after {
  content: '';
  position: absolute;
  top: 2px;
  bottom: 2px;
  left: 50%;
  z-index: 4;
  width: 46px;
  pointer-events: none;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(76, 47, 25, 0.2) 42%,
    rgba(56, 34, 18, 0.34) 50%,
    rgba(76, 47, 25, 0.2) 58%,
    transparent 100%
  );
  transform: translateX(-50%);
}

.reader-page {
  position: relative;
  overflow: hidden;
  padding: 52px 56px 34px;
  border: 1px solid #b89b6e;
  background:
    radial-gradient(circle at 22% 16%, rgba(255, 252, 240, 0.82), transparent 42%),
    linear-gradient(90deg, rgba(193, 161, 111, 0.08), transparent 12%, transparent 88%, rgba(159, 123, 76, 0.08)),
    #ead7b2;
  color: #433022;
  backface-visibility: hidden;
}

.reader-page-left {
  border-radius: 8px 0 0 8px;
  box-shadow: inset -18px 0 30px rgba(83, 52, 26, 0.16);
}

.reader-page-right {
  border-left: 0;
  border-radius: 0 8px 8px 0;
  box-shadow: inset 18px 0 30px rgba(83, 52, 26, 0.16);
}

.reader-text {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-family: Georgia, 'Microsoft YaHei', serif;
  font-size: 18px;
  line-height: 2;
}

.reader-image {
  display: block;
  max-width: 100%;
  max-height: 48vh;
  margin: 24px auto 0;
  object-fit: contain;
  border: 1px solid rgba(74, 44, 24, 0.25);
}

.reader-page-no {
  position: absolute;
  right: 26px;
  bottom: 16px;
  color: rgba(75, 48, 29, 0.5);
  font-family: var(--mono);
  font-size: 10px;
}

.reader-page-left .reader-page-no {
  right: auto;
  left: 26px;
}

.reader-cover {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18px;
  height: 100%;
  text-align: center;
}

.reader-cover span {
  color: #8a6846;
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 2px;
}

.reader-cover strong {
  max-width: 84%;
  font-family: Georgia, 'Microsoft YaHei', serif;
  font-size: 30px;
  line-height: 1.45;
}

.reader-flip-sheet {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 50%;
  padding: 52px 56px 34px;
  border: 1px solid #b89b6e;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.2), transparent 18%),
    #ead7b2;
  color: #433022;
  backface-visibility: hidden;
  transform-style: preserve-3d;
  will-change: transform;
  z-index: 3;
}

.reader-flip-sheet.next {
  right: 0;
  border-radius: 0 8px 8px 0;
  transform-origin: left center;
  animation: page-turn-next 0.72s cubic-bezier(0.22, 0.72, 0.18, 1) forwards;
}

.reader-flip-sheet.prev {
  left: 0;
  border-radius: 8px 0 0 8px;
  transform-origin: right center;
  animation: page-turn-prev 0.72s cubic-bezier(0.22, 0.72, 0.18, 1) forwards;
}

.reader-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  color: rgba(239, 210, 158, 0.72);
  font-family: var(--mono);
  font-size: 11px;
}

.reader-nav {
  padding: 7px 14px;
  border: 1px solid rgba(239, 210, 158, 0.3);
  border-radius: 5px;
  background: rgba(38, 23, 15, 0.62);
  color: #efd29e;
  font-size: 12px;
  cursor: pointer;
}

.reader-nav:hover:not(:disabled) {
  border-color: rgba(255, 227, 174, 0.72);
  color: #fff2d4;
}

.reader-nav:disabled {
  opacity: 0.3;
  cursor: default;
}

@keyframes page-turn-next {
  0% {
    transform: rotateY(0deg) translateZ(0) translateX(0);
    box-shadow: 0 0 0 rgba(0, 0, 0, 0);
  }
  22% {
    transform: rotateY(-14deg) translateZ(16px) translateX(-2px);
    box-shadow: -18px 0 28px rgba(44, 25, 12, 0.24);
  }
  58% {
    transform: rotateY(-96deg) translateZ(24px);
    box-shadow: -34px 0 38px rgba(44, 25, 12, 0.34);
  }
  100% {
    transform: rotateY(-180deg) translateZ(4px);
    box-shadow: -8px 0 14px rgba(44, 25, 12, 0.12);
  }
}

@keyframes page-turn-prev {
  0% {
    transform: rotateY(-180deg) translateZ(4px);
    box-shadow: 8px 0 14px rgba(44, 25, 12, 0.12);
  }
  42% {
    transform: rotateY(-96deg) translateZ(24px);
    box-shadow: 34px 0 38px rgba(44, 25, 12, 0.34);
  }
  78% {
    transform: rotateY(-14deg) translateZ(16px) translateX(2px);
    box-shadow: 18px 0 28px rgba(44, 25, 12, 0.24);
  }
  100% {
    transform: rotateY(0deg) translateZ(0) translateX(0);
    box-shadow: 0 0 0 rgba(0, 0, 0, 0);
  }
}

@keyframes journey-appear {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes handoff-jitter {
  0%, 100% { transform: translate(0, 0); }
  25% { transform: translate(-4px, 1px); }
  50% { transform: translate(3px, -1px); }
  75% { transform: translate(-2px, 0); }
}

@keyframes handoff-tear {
  0%, 100% { transform: translateX(0); opacity: 0.24; }
  50% { transform: translateX(5%); opacity: 0.7; }
}

@media (max-width: 700px) {
  .shelf-arrow {
    width: 42px;
    height: 72px;
    font-size: 36px;
  }

  .shelf-arrow-left {
    left: 8px;
  }

  .shelf-arrow-right {
    right: 8px;
  }

  .book-reader {
    padding: 12px;
  }

  .reader-shell {
    width: 100%;
  }

  .reader-book {
    grid-template-columns: 1fr;
    min-height: 72vh;
  }

  .reader-page-left {
    display: none;
  }

  .reader-page-right {
    border-left: 1px solid #b89b6e;
    border-radius: 8px;
  }

  .reader-page,
  .reader-flip-sheet {
    padding: 34px 28px 26px;
  }

  .reader-flip-sheet {
    width: 100%;
  }

  .reader-flip-sheet.next {
    right: 0;
    border-radius: 8px;
  }

  .reader-flip-sheet.prev {
    left: 0;
    border-radius: 8px;
  }
}
</style>
