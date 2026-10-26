<template>
  <section class="cyberrange-stage" aria-label="CyberRange 动态球体">
    <canvas ref="canvasRef" class="scene-canvas" aria-hidden="true"></canvas>
    <span
      v-if="canInteract"
      class="projection-cone"
      :class="[
        projectionConePhase,
        {
          suspended: isExpanded || isTransitioning,
          flickering: projectionFlicker,
        },
      ]"
      :style="projectionConeStyle"
    >
      <span class="projection-cone-haze"></span>
      <span class="projection-cone-core"></span>
      <span class="projection-cone-near"></span>
    </span>
    <button
      v-if="canInteract && !isTransitioning && terminalPhase === 'closed'"
      class="sphere-hit"
      :class="{ expanded: isExpanded }"
      :style="hitAreaStyle"
      type="button"
      :aria-label="isExpanded ? 'CyberRange 球体已展开' : '展开 CyberRange 球体'"
      :title="isExpanded ? '' : '点击展开'"
      @click.stop="activateSphere"
    ></button>
    <div
      v-if="canInteract"
      class="hologram"
      :class="[
        projectionPhase,
        {
          suspended: isExpanded || isTransitioning,
          flickering: projectionFlicker,
        },
      ]"
      :style="projectionStyle"
      aria-hidden="true"
    >
      <div class="hologram-copy">
        <span class="hologram-text">{{ projectionText }}</span>
        <span class="hologram-caret"></span>
      </div>
    </div>
    <div
      v-if="terminalPhase !== 'closed' && terminalPhase !== 'collapsing'"
      class="terminal-build"
      :class="terminalPhase"
      :style="terminalStyle"
      aria-hidden="true"
    >
      <span class="terminal-rail rail-top"></span>
      <span class="terminal-rail rail-bottom"></span>
      <span class="terminal-edge edge-left"></span>
      <span class="terminal-edge edge-right"></span>
      <div class="terminal-content">
        <div class="terminal-head">
          <span>CYBERRANGE://SECURE_TERMINAL</span>
          <span class="terminal-online">ONLINE</span>
        </div>
        <div class="terminal-log">
          <p><span class="terminal-prompt">$</span> secure channel initialized</p>
          <p><span class="terminal-prompt">$</span> node cyberrange-core connected</p>
          <p class="terminal-input">
            <span class="terminal-prompt">root@cyberrange:~$</span>
            <span class="terminal-block"></span>
          </p>
        </div>
      </div>
    </div>
    <p v-if="sceneError" class="scene-error">{{ sceneError }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { LineMaterial } from 'three/addons/lines/LineMaterial.js'
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js'
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js'
import { useThemeStore } from '../stores/theme'

type ColorMaterial =
  | THREE.LineBasicMaterial
  | THREE.PointsMaterial
  | THREE.MeshBasicMaterial

interface TintEntry {
  material: ColorMaterial
  dark: THREE.ColorRepresentation
  light: THREE.ColorRepresentation
  darkOpacity: number
  lightOpacity: number
  additive: boolean
}

interface OutwardParticle {
  angle: number
  travel: number
  life: number
  phase: number
  size: number
  arc: number
  z: number
}

interface OutwardParticleSystem {
  geometry: THREE.BufferGeometry
  material: THREE.ShaderMaterial
  positions: Float32Array
  alphas: Float32Array
  sizes: Float32Array
  particles: OutwardParticle[]
  points: THREE.Points
}

interface FatLineEntry {
  material: LineMaterial
  dark: THREE.ColorRepresentation
  light: THREE.ColorRepresentation
  darkOpacity: number
  lightOpacity: number
}

type TerminalPhase = 'closed' | 'collapsing' | 'line' | 'opening' | 'open' | 'closing'

const theme = useThemeStore()
const canvasRef = ref<HTMLCanvasElement | null>(null)
const sceneError = ref('')
const viewportSize = ref({
  width: window.innerWidth,
  height: window.innerHeight,
})
const canInteract = ref(false)
const isExpanded = ref(false)
const isTransitioning = ref(false)
const projectionText = ref('')
const projectionPhase = ref<'emitting' | 'stabilizing' | 'typing' | 'holding' | 'dissolving'>(
  'emitting',
)
const projectionConePhase = ref<'idle' | 'emitting' | 'stable'>('idle')
const projectionIndex = ref(0)
const projectionClosing = ref(false)
const projectionFlicker = ref(false)
const terminalPhase = ref<TerminalPhase>('closed')

const tintedMaterials: TintEntry[] = []
const fatLineMaterials: FatLineEntry[] = []

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.OrthographicCamera | null = null
let visualGroup: THREE.Group | null = null
let sphereGroup: THREE.Group | null = null
let orbitGroup: THREE.Group | null = null
let outwardParticles: OutwardParticleSystem | null = null
let animationFrame = 0
let startTime = 0
let expansionProgress = 0
let expansionStartTime = 0
let expansionStartProgress = 0
let expansionTargetValue = 0
let sceneTime = 0
let reducedMotion = false
let hasStartedProjection = false
let projectionToken = 0
let projectionTimers: ReturnType<typeof setTimeout>[] = []
let interactionTimers: ReturnType<typeof setTimeout>[] = []
let terminalTimers: ReturnType<typeof setTimeout>[] = []
let terminalProgress = 0
let terminalStartProgress = 0
let terminalTargetProgress = 0
let terminalStartTime = 0

const settleTravelDuration = 1.6
const interactionTravelDuration = 3.6

const projectionLines = [
  '为一切美好而战',
  '在看不见的地方，守护看得见的世界',
  '每一次入侵，都是一次理解的开始',
  '保持好奇，也保持敬畏',
]

const cyberBluePalette = {
  sphereOuter: 0x178de0,
  sphereInner: 0x37cdf2,
  sphereLink: 0x20ace3,
  node: 0xace8ff,
  ring: 0x235bff,
  ringBright: 0x4b7dff,
  ringDust: 0x2d72ff,
  outwardParticle: 0xb9ddff,
}

const darkPalette = cyberBluePalette
const lightPalette = {
  sphereOuter: 0x075d9b,
  sphereInner: 0x0789ad,
  sphereLink: 0x0a739b,
  node: 0x075d76,
  ring: 0x18399f,
  ringBright: 0x2f5bd1,
  ringDust: 0x2350b3,
  outwardParticle: 0x2f5bd1,
}

let randomState = 0x2f6e2b1

function random() {
  randomState = (Math.imul(randomState, 1664525) + 1013904223) >>> 0
  return randomState / 4294967296
}

function clamp01(value: number) {
  return Math.max(0, Math.min(1, value))
}

function easeOutCubic(value: number) {
  return 1 - Math.pow(1 - value, 3)
}

function easeInOutCubic(value: number) {
  return value < 0.5
    ? 4 * value * value * value
    : 1 - Math.pow(-2 * value + 2, 3) / 2
}

function tint<T extends ColorMaterial>(
  material: T,
  dark: THREE.ColorRepresentation,
  light: THREE.ColorRepresentation,
  darkOpacity: number,
  lightOpacity: number,
  additive = true,
): T {
  tintedMaterials.push({
    material,
    dark,
    light,
    darkOpacity,
    lightOpacity,
    additive,
  })
  return material
}

function applyTheme() {
  const light = theme.resolved === 'light'
  for (const entry of tintedMaterials) {
    entry.material.color.set(light ? entry.light : entry.dark)
    entry.material.opacity = light ? entry.lightOpacity : entry.darkOpacity
    entry.material.blending = !light && entry.additive
      ? THREE.AdditiveBlending
      : THREE.NormalBlending
    entry.material.needsUpdate = true
  }
  for (const entry of fatLineMaterials) {
    entry.material.color.set(light ? entry.light : entry.dark)
    entry.material.opacity = light ? entry.lightOpacity : entry.darkOpacity
    entry.material.blending = light
      ? THREE.NormalBlending
      : THREE.AdditiveBlending
    entry.material.needsUpdate = true
  }
  if (outwardParticles) {
    outwardParticles.material.uniforms.uColor.value.set(
      light ? lightPalette.ringBright : darkPalette.outwardParticle,
    )
    outwardParticles.material.blending = light
      ? THREE.NormalBlending
      : THREE.AdditiveBlending
    outwardParticles.material.needsUpdate = true
  }
}

function lineMaterial(
  dark: THREE.ColorRepresentation,
  light: THREE.ColorRepresentation,
  darkOpacity: number,
  lightOpacity: number,
  additive = true,
) {
  return tint(
    new THREE.LineBasicMaterial({
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    }),
    dark,
    light,
    darkOpacity,
    lightOpacity,
    additive,
  )
}

function pointMaterial(
  dark: THREE.ColorRepresentation,
  light: THREE.ColorRepresentation,
  darkOpacity: number,
  lightOpacity: number,
  size: number,
) {
  return tint(
    new THREE.PointsMaterial({
      size,
      sizeAttenuation: true,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    }),
    dark,
    light,
    darkOpacity,
    lightOpacity,
  )
}

function fatLineMaterial(
  dark: THREE.ColorRepresentation,
  light: THREE.ColorRepresentation,
  darkOpacity: number,
  lightOpacity: number,
  lineWidth: number,
) {
  const material = new LineMaterial({
    color: dark,
    transparent: true,
    depthWrite: false,
    opacity: darkOpacity,
    blending: THREE.AdditiveBlending,
  })
  material.uniforms.linewidth.value = lineWidth
  fatLineMaterials.push({
    material,
    dark,
    light,
    darkOpacity,
    lightOpacity,
  })
  return material
}

function circlePoints(radius: number, segments = 192) {
  const points: THREE.Vector3[] = []
  for (let index = 0; index < segments; index += 1) {
    const angle = (index / segments) * Math.PI * 2
    points.push(new THREE.Vector3(
      Math.cos(angle) * radius,
      Math.sin(angle) * radius,
      0,
    ))
  }
  return points
}

function createFatWireframe(
  source: THREE.BufferGeometry,
  material: LineMaterial,
) {
  const wireframe = new THREE.WireframeGeometry(source)
  const geometry = new LineSegmentsGeometry().fromWireframeGeometry(wireframe)
  wireframe.dispose()
  source.dispose()
  const lines = new LineSegments2(geometry, material)
  lines.frustumCulled = false
  return lines
}

function createFatCircle(radius: number, material: LineMaterial) {
  const points = circlePoints(radius, 192)
  const positions: number[] = []
  for (let index = 0; index < points.length; index += 1) {
    const current = points[index]
    const next = points[(index + 1) % points.length]
    positions.push(current.x, current.y, current.z, next.x, next.y, next.z)
  }
  const geometry = new LineSegmentsGeometry().setPositions(positions)
  const line = new LineSegments2(geometry, material)
  line.frustumCulled = false
  return line
}

function buildSphere() {
  const group = new THREE.Group()

  const outerMaterial = fatLineMaterial(
    darkPalette.sphereOuter,
    lightPalette.sphereOuter,
    0.62,
    0.7,
    1.2,
  )
  group.add(createFatWireframe(
    new THREE.IcosahedronGeometry(1.68, 2),
    outerMaterial,
  ))

  const innerMaterial = fatLineMaterial(
    darkPalette.sphereInner,
    lightPalette.sphereInner,
    0.84,
    0.9,
    1.65,
  )
  const innerSphere = new THREE.Group()
  innerSphere.add(createFatWireframe(
    new THREE.IcosahedronGeometry(1.14, 1),
    innerMaterial,
  ))
  innerSphere.rotation.set(0.58, -0.42, 0.2)
  group.add(innerSphere)

  const nodes: THREE.Vector3[] = []
  const nodeCount = 72
  const goldenAngle = Math.PI * (3 - Math.sqrt(5))
  for (let index = 0; index < nodeCount; index += 1) {
    const y = 1 - ((index + 0.5) / nodeCount) * 2
    const radius = Math.sqrt(1 - y * y)
    const theta = goldenAngle * index
    nodes.push(new THREE.Vector3(
      Math.cos(theta) * radius * 1.69,
      y * 1.69,
      Math.sin(theta) * radius * 1.69,
    ))
  }

  const nodePositions = new Float32Array(nodes.length * 3)
  nodes.forEach((node, index) => {
    nodePositions.set([node.x, node.y, node.z], index * 3)
  })
  const nodeGeometry = new THREE.BufferGeometry()
  nodeGeometry.setAttribute('position', new THREE.BufferAttribute(nodePositions, 3))
  group.add(new THREE.Points(
    nodeGeometry,
    pointMaterial(
      darkPalette.node,
      lightPalette.node,
      1,
      0.86,
      0.06,
    ),
  ))
  group.add(new THREE.Points(
    nodeGeometry,
    pointMaterial(
      darkPalette.node,
      lightPalette.node,
      0.14,
      0.09,
      0.12,
    ),
  ))

  const connected = new Set<string>()
  const connectionPositions: number[] = []
  nodes.forEach((node, index) => {
    const nearest = nodes
      .map((candidate, candidateIndex) => ({
        candidate,
        candidateIndex,
        distance: node.distanceToSquared(candidate),
      }))
      .filter((item) => item.candidateIndex !== index)
      .sort((a, b) => a.distance - b.distance)
      .slice(0, 3)

    for (const item of nearest) {
      const low = Math.min(index, item.candidateIndex)
      const high = Math.max(index, item.candidateIndex)
      const key = `${low}:${high}`
      if (connected.has(key)) continue
      connected.add(key)
      connectionPositions.push(
        node.x,
        node.y,
        node.z,
        item.candidate.x,
        item.candidate.y,
        item.candidate.z,
      )
    }
  })

  const connectionGeometry = new LineSegmentsGeometry().setPositions(connectionPositions)
  const connections = new LineSegments2(
    connectionGeometry,
    fatLineMaterial(
      darkPalette.sphereLink,
      lightPalette.sphereLink,
      0.6,
      0.56,
      0.9,
    ),
  )
  connections.frustumCulled = false
  group.add(connections)

  const ringMaterial = fatLineMaterial(
    darkPalette.sphereOuter,
    lightPalette.sphereOuter,
    0.62,
    0.7,
    1.1,
  )
  const ringRotations = [
    [0.2, 0.16, 0],
    [1.1, 0.35, 0.42],
    [0.72, -0.62, -0.35],
  ]
  for (const rotation of ringRotations) {
    const ring = createFatCircle(1.7, ringMaterial)
    ring.rotation.set(rotation[0], rotation[1], rotation[2])
    group.add(ring)
  }

  return group
}

function buildOutwardParticles() {
  const count = 140
  const positions = new Float32Array(count * 3)
  const alphas = new Float32Array(count)
  const sizes = new Float32Array(count)
  const particles: OutwardParticle[] = []

  for (let index = 0; index < count; index += 1) {
    const life = 1.45 + random() * 1.35
    particles.push({
      angle: random() * Math.PI * 2,
      travel: 0.38 + random() * 0.72,
      life,
      phase: random() * life,
      size: 3.4 + random() * 5.4,
      arc: (random() - 0.5) * 0.38,
      z: (random() - 0.5) * 0.5,
    })
  }

  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('aAlpha', new THREE.BufferAttribute(alphas, 1))
  geometry.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1))

  const material = new THREE.ShaderMaterial({
    uniforms: {
      uColor: { value: new THREE.Color(darkPalette.outwardParticle) },
      uPixelRatio: { value: renderer?.getPixelRatio() ?? 1 },
      uScale: { value: 1 },
    },
    vertexShader: `
      attribute float aAlpha;
      attribute float aSize;
      uniform float uPixelRatio;
      uniform float uScale;
      varying float vAlpha;

      void main() {
        vAlpha = aAlpha;
        vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
        gl_Position = projectionMatrix * viewPosition;
        gl_PointSize = clamp(
          aSize * uPixelRatio * uScale,
          uPixelRatio,
          6.0 * uPixelRatio
        );
      }
    `,
    fragmentShader: `
      uniform vec3 uColor;
      varying float vAlpha;

      void main() {
        float distanceToCenter = length(gl_PointCoord * 2.0 - 1.0);
        if (distanceToCenter > 1.0) discard;
        float glow = pow(1.0 - distanceToCenter, 1.2);
        gl_FragColor = vec4(uColor, vAlpha * glow);
      }
    `,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  })

  const points = new THREE.Points(geometry, material)
  points.frustumCulled = false

  outwardParticles = {
    geometry,
    material,
    positions,
    alphas,
    sizes,
    particles,
    points,
  }

  return points
}

function updateOutwardParticles(time: number) {
  if (!outwardParticles) return

  const {
    geometry,
    positions,
    alphas,
    sizes,
    particles,
  } = outwardParticles

  for (let index = 0; index < particles.length; index += 1) {
    const particle = particles[index]
    const age = (time + particle.phase) % particle.life
    const progress = age / particle.life
    const radius = 2.86 + easeOutCubic(progress) * particle.travel
    const angle = particle.angle + progress * particle.arc
    const offset = index * 3

    positions[offset] = Math.cos(angle) * radius
    positions[offset + 1] = Math.sin(angle) * radius
    positions[offset + 2] = particle.z + Math.sin(progress * Math.PI) * 0.16

    const fadeIn = THREE.MathUtils.smoothstep(progress, 0, 0.16)
    const fadeOut = 1 - THREE.MathUtils.smoothstep(progress, 0.58, 1)
    alphas[index] = fadeIn * fadeOut * (reducedMotion ? 0.7 : 1)
    sizes[index] = particle.size * (1 - progress * 0.22)
  }

  geometry.attributes.position.needsUpdate = true
  geometry.attributes.aAlpha.needsUpdate = true
  geometry.attributes.aSize.needsUpdate = true
}

function buildOrbit() {
  const group = new THREE.Group()

  const tickCount = 104
  const tickGeometry = new THREE.PlaneGeometry(1, 1)
  tickGeometry.translate(0, 0.5, 0)
  const tickMaterial = tint(
    new THREE.MeshBasicMaterial({
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
    }),
    darkPalette.ringBright,
    lightPalette.ringBright,
    0.98,
    1,
  )
  const ticks = new THREE.InstancedMesh(tickGeometry, tickMaterial, tickCount)
  const matrix = new THREE.Matrix4()
  const quaternion = new THREE.Quaternion()
  const position = new THREE.Vector3()
  const scale = new THREE.Vector3()
  const zAxis = new THREE.Vector3(0, 0, 1)

  for (let index = 0; index < tickCount; index += 1) {
    const angle = (index / tickCount) * Math.PI * 2
    const startRadius = 2.27
    const tickLength = index % 8 === 0 ? 0.32 : index % 3 === 0 ? 0.24 : 0.17
    const tickWidth = index % 8 === 0 ? 0.032 : index % 3 === 0 ? 0.024 : 0.018
    position.set(
      Math.cos(angle) * startRadius,
      Math.sin(angle) * startRadius,
      0,
    )
    quaternion.setFromAxisAngle(zAxis, angle - Math.PI / 2)
    scale.set(tickWidth, tickLength, 1)
    matrix.compose(position, quaternion, scale)
    ticks.setMatrixAt(index, matrix)
  }
  ticks.instanceMatrix.needsUpdate = true
  group.add(ticks)

  const orbitLineMaterial = lineMaterial(
    darkPalette.ring,
    lightPalette.ring,
    0.54,
    0.42,
  )
  for (const radius of [2.14, 2.68, 2.78]) {
    const orbitLine = new THREE.LineLoop(
      new THREE.BufferGeometry().setFromPoints(circlePoints(radius)),
      orbitLineMaterial,
    )
    group.add(orbitLine)
  }

  const dottedPositions: number[] = []
  for (let index = 0; index < 168; index += 1) {
    const angle = (index / 168) * Math.PI * 2
    dottedPositions.push(
      Math.cos(angle) * 2.23,
      Math.sin(angle) * 2.23,
      0,
    )
  }
  const dottedGeometry = new THREE.BufferGeometry()
  dottedGeometry.setAttribute('position', new THREE.Float32BufferAttribute(dottedPositions, 3))
  group.add(new THREE.Points(
    dottedGeometry,
    pointMaterial(
      darkPalette.node,
      lightPalette.node,
      0.94,
      0.78,
      0.034,
    ),
  ))

  const dustPositions: number[] = []
  const dustCount = 360
  for (let index = 0; index < dustCount; index += 1) {
    const angle = random() * Math.PI * 2
    const radius = 2.42 + random() * 0.82
    dustPositions.push(
      Math.cos(angle) * radius,
      Math.sin(angle) * radius,
      (random() - 0.5) * 0.72,
    )
  }
  const dustGeometry = new THREE.BufferGeometry()
  dustGeometry.setAttribute('position', new THREE.Float32BufferAttribute(dustPositions, 3))
  group.add(new THREE.Points(
    dustGeometry,
    pointMaterial(
      darkPalette.ringDust,
      lightPalette.ringDust,
      0.9,
      0.66,
      0.042,
    ),
  ))

  const farDustPositions: number[] = []
  const farDustCount = 84
  for (let index = 0; index < farDustCount; index += 1) {
    const angle = random() * Math.PI * 2
    const radius = 2.82 + random() * 0.5
    farDustPositions.push(
      Math.cos(angle) * radius,
      Math.sin(angle) * radius,
      (random() - 0.5) * 1.1,
    )
  }
  const farDustGeometry = new THREE.BufferGeometry()
  farDustGeometry.setAttribute('position', new THREE.Float32BufferAttribute(farDustPositions, 3))
  group.add(new THREE.Points(
    farDustGeometry,
    pointMaterial(
      darkPalette.ringBright,
      lightPalette.ringBright,
      0.78,
      0.56,
      0.06,
    ),
  ))

  const markerPositions: number[] = []
  const markerCount = 18
  for (let index = 0; index < markerCount; index += 1) {
    const angle = (index / markerCount) * Math.PI * 2 + 0.08
    const radius = 2.72 + (index % 3) * 0.035
    markerPositions.push(
      Math.cos(angle) * radius,
      Math.sin(angle) * radius,
      (index % 2 === 0 ? 1 : -1) * 0.12,
    )
  }
  const markerGeometry = new THREE.BufferGeometry()
  markerGeometry.setAttribute('position', new THREE.Float32BufferAttribute(markerPositions, 3))
  group.add(new THREE.Points(
    markerGeometry,
    pointMaterial(
      darkPalette.node,
      lightPalette.node,
      1,
      0.84,
      0.075,
    ),
  ))

  group.add(buildOutwardParticles())

  return group
}

function screenToWorld(x: number, y: number) {
  if (!camera) return new THREE.Vector3()
  const visibleHeight = camera.top - camera.bottom
  const visibleWidth = camera.right - camera.left
  return new THREE.Vector3(
    (x / window.innerWidth - 0.5) * visibleWidth,
    (0.5 - y / window.innerHeight) * visibleHeight,
    0,
  )
}

function responsiveLayout(width: number, height: number) {
  const compact = width < 700
  const stacked = width < 960
  const finalScale = compact
    ? 0.31
    : THREE.MathUtils.clamp(width / 3200, 0.38, 0.46)
  const finalX = stacked
    ? THREE.MathUtils.clamp(width * 0.24, 112, 220)
    : THREE.MathUtils.clamp(width * 0.22, 240, 360)
  const finalY = stacked ? height * 0.34 : height * 0.5
  const ringDiameter = (height / 8.06) * 5.64
  const expandedScale = Math.min(
    1,
    (width * 0.88) / ringDiameter,
    (height * 0.72) / ringDiameter,
  )

  return {
    stacked,
    finalX,
    finalY,
    finalScale,
    ringDiameter,
    expandedScale,
  }
}

function terminalLayout(width: number, height: number) {
  const base = responsiveLayout(width, height)
  const stacked = base.stacked
  const sphereX = stacked ? width * 0.32 : width * 0.25
  const sphereY = stacked ? height * 0.4 : height * 0.5
  const left = stacked ? 24 : width * 0.48
  const right = stacked ? width - 24 : width * 0.94
  const top = stacked ? height * 0.56 : height * 0.22
  const bottom = stacked ? height * 0.9 : height * 0.78
  const targetScale = Math.max(
    0.28,
    base.expandedScale * (stacked ? 0.68 : 0.82),
  )

  return {
    sphereX,
    sphereY,
    left,
    right,
    top,
    bottom,
    width: right - left,
    height: bottom - top,
    targetScale,
    lineCenterX: (left + right) / 2,
    lineCenterY: (top + bottom) / 2,
    lineWidth: base.ringDiameter * targetScale,
  }
}

function finalPlacement() {
  const width = window.innerWidth
  const height = window.innerHeight
  const layout = responsiveLayout(width, height)

  return {
    position: screenToWorld(layout.finalX, layout.finalY),
    scale: layout.finalScale,
    expandedScale: layout.expandedScale,
  }
}

const terminalStyle = computed<Record<string, string>>(() => {
  const { width, height } = viewportSize.value
  const layout = terminalLayout(width, height)
  return {
    left: `${layout.left}px`,
    top: `${layout.top}px`,
    width: `${layout.width}px`,
    height: `${layout.height}px`,
    '--terminal-line-width': `${layout.lineWidth}px`,
  }
})

const hitAreaStyle = computed(() => {
  const { width, height } = viewportSize.value
  const layout = responsiveLayout(width, height)
  const scale = isExpanded.value ? layout.expandedScale : layout.finalScale
  const diameter = Math.max(44, layout.ringDiameter * scale + 18)
  const centerX = isExpanded.value ? width / 2 : layout.finalX
  const centerY = isExpanded.value ? height / 2 : layout.finalY

  return {
    width: `${diameter}px`,
    height: `${diameter}px`,
    left: `${centerX - diameter / 2}px`,
    top: `${centerY - diameter / 2}px`,
  }
})

const projectionStyle = computed(() => {
  const { width, height } = viewportSize.value
  const layout = responsiveLayout(width, height)
  const textWidth = layout.stacked
    ? Math.max(220, width - 48)
    : Math.max(420, Math.min(width * 0.5, 680))

  return {
    left: '50%',
    top: layout.stacked ? '52%' : '50%',
    width: `${textWidth}px`,
  }
})

const projectionConeStyle = computed(() => {
  const { width, height } = viewportSize.value
  const layout = responsiveLayout(width, height)
  const targetHalfWidth = layout.stacked
    ? Math.min(width * 0.36, 180)
    : Math.min(width * 0.3, 400)
  const targetHalfHeight = Math.min(height * 0.25, 220)
  const targetTop = height / 2 - targetHalfHeight
  const targetBottom = height / 2 + targetHalfHeight
  const targetRight = width / 2 + targetHalfWidth

  return {
    left: `${layout.finalX}px`,
    top: `${targetTop}px`,
    width: `${Math.max(180, targetRight - layout.finalX)}px`,
    height: `${targetBottom - targetTop}px`,
  }
})

function clearProjectionTimers() {
  projectionToken += 1
  for (const timer of projectionTimers) clearTimeout(timer)
  projectionTimers = []
}

function scheduleProjection(callback: () => void, delay: number, token: number) {
  const timer = setTimeout(() => {
    if (token === projectionToken) callback()
  }, delay)
  projectionTimers.push(timer)
}

function playProjectionLine() {
  clearProjectionTimers()
  const token = projectionToken
  const characters = Array.from(projectionLines[projectionIndex.value] ?? '')
  let characterIndex = 0

  projectionText.value = ''
  projectionPhase.value = 'typing'

  const typeNextCharacter = () => {
    if (characterIndex >= characters.length) {
      projectionPhase.value = 'holding'
      scheduleProjection(() => {
        projectionPhase.value = 'dissolving'
        scheduleProjection(() => {
          projectionIndex.value = (projectionIndex.value + 1) % projectionLines.length
          playProjectionLine()
        }, 900, token)
      }, 3400, token)
      return
    }

    const character = characters[characterIndex]
    projectionText.value += character
    characterIndex += 1
    const delay = character === '，' || character === '。' ? 240 : 72
    scheduleProjection(typeNextCharacter, delay, token)
  }

  scheduleProjection(typeNextCharacter, 100, token)
}

function startProjectionSequence() {
  if (hasStartedProjection) return
  hasStartedProjection = true
  projectionIndex.value = 0
  projectionText.value = ''
  projectionConePhase.value = 'emitting'
  projectionPhase.value = 'emitting'
  clearProjectionTimers()
  const token = projectionToken

  scheduleProjection(() => {
    projectionConePhase.value = 'stable'
    projectionPhase.value = 'stabilizing'
    scheduleProjection(() => {
      playProjectionLine()
    }, 420, token)
  }, 820, token)
}

function clearInteractionTimers() {
  for (const timer of interactionTimers) clearTimeout(timer)
  interactionTimers = []
}

function beginSphereExpansion() {
  isExpanded.value = true
  isTransitioning.value = true
  expansionStartTime = sceneTime
  expansionStartProgress = expansionProgress
  expansionTargetValue = 1
}

function clearTerminalTimers() {
  for (const timer of terminalTimers) clearTimeout(timer)
  terminalTimers = []
}

function scheduleTerminal(callback: () => void, delay: number) {
  terminalTimers.push(setTimeout(callback, delay))
}

function startTerminalConstruction() {
  if (!isExpanded.value || isTransitioning.value || terminalPhase.value !== 'closed') return
  clearTerminalTimers()
  terminalPhase.value = 'collapsing'
  terminalStartProgress = terminalProgress
  terminalTargetProgress = 1
  terminalStartTime = sceneTime
}

function closeTerminal() {
  if (!['line', 'opening', 'open'].includes(terminalPhase.value)) return
  clearTerminalTimers()
  terminalPhase.value = 'closing'
  terminalStartProgress = terminalProgress
  terminalTargetProgress = 0
  terminalStartTime = sceneTime
  if (orbitGroup) orbitGroup.visible = true
}

function activateSphere() {
  if (!isExpanded.value) {
    expandSphere()
    return
  }
  startTerminalConstruction()
}

function expandSphere() {
  if (
    !canInteract.value
    || isTransitioning.value
    || isExpanded.value
    || projectionClosing.value
  ) return

  clearProjectionTimers()
  projectionText.value = projectionLines[projectionIndex.value] ?? ''
  projectionPhase.value = 'holding'
  projectionClosing.value = true
  projectionFlicker.value = false
  clearInteractionTimers()
  interactionTimers.push(setTimeout(() => {
    projectionFlicker.value = true
  }, 320))
  interactionTimers.push(setTimeout(() => {
    projectionFlicker.value = false
    projectionClosing.value = false
    beginSphereExpansion()
  }, 880))
}

function collapseSphere() {
  if (!isExpanded.value || isTransitioning.value) return
  isExpanded.value = false
  isTransitioning.value = true
  expansionStartTime = sceneTime
  expansionStartProgress = expansionProgress
  expansionTargetValue = 0
}

function onDocumentPointerDown(event: PointerEvent) {
  if (!isExpanded.value || isTransitioning.value) return
  const target = event.target as Element | null
  if (!target) return
  if (target.closest('.sphere-hit')) return
  if (target.closest('a, button, input, textarea, select, label, [role="button"], [contenteditable="true"]')) {
    return
  }
  if (terminalPhase.value !== 'closed') {
    if (target.closest('.terminal-build')) return
    closeTerminal()
    return
  }
  collapseSphere()
}

function updateScene(time: number) {
  if (!renderer || !visualGroup || !sphereGroup || !orbitGroup) return

  sceneTime = time
  const intro = reducedMotion ? 1 : clamp01(time / 1.45)
  const travel = reducedMotion ? 1 : clamp01((time - 3.85) / settleTravelDuration)
  const travelEase = easeInOutCubic(travel)
  const introScale = THREE.MathUtils.lerp(2.9, 1, easeOutCubic(intro))
  const target = finalPlacement()
  const center = screenToWorld(window.innerWidth / 2, window.innerHeight / 2)
  if (isTransitioning.value) {
    const transition = reducedMotion
      ? 1
      : clamp01((time - expansionStartTime) / interactionTravelDuration)
    expansionProgress = THREE.MathUtils.lerp(
      expansionStartProgress,
      expansionTargetValue,
      easeInOutCubic(transition),
    )
    if (transition >= 1) {
      expansionProgress = expansionTargetValue
      isTransitioning.value = false
      if (!isExpanded.value) playProjectionLine()
    }
  }
  if (terminalPhase.value === 'collapsing' || terminalPhase.value === 'closing') {
    const terminalTransition = reducedMotion
      ? 1
      : clamp01((time - terminalStartTime) / 1.2)
    terminalProgress = THREE.MathUtils.lerp(
      terminalStartProgress,
      terminalTargetProgress,
      easeInOutCubic(terminalTransition),
    )

    if (terminalTransition >= 1) {
      terminalProgress = terminalTargetProgress
      if (terminalPhase.value === 'collapsing') {
        orbitGroup.visible = false
        terminalPhase.value = 'line'
        scheduleTerminal(() => {
          if (terminalPhase.value === 'line') terminalPhase.value = 'opening'
        }, 280)
        scheduleTerminal(() => {
          if (terminalPhase.value === 'opening') terminalPhase.value = 'open'
        }, 1080)
      } else {
        terminalProgress = 0
        terminalPhase.value = 'closed'
        orbitGroup.visible = true
        orbitGroup.position.x = 0
        orbitGroup.position.y = 0
        orbitGroup.scale.set(1, 1, 1)
      }
    }
  }
  const expansionEase = easeInOutCubic(expansionProgress)
  const terminalEase = easeInOutCubic(terminalProgress)
  const terminalTarget = terminalLayout(window.innerWidth, window.innerHeight)

  const settledPosition = center.clone().lerp(target.position, travelEase)
  const expandedPosition = settledPosition.clone().lerp(center, expansionEase)
  const settledScale = THREE.MathUtils.lerp(introScale, target.scale, travelEase)
  const expandedScale = THREE.MathUtils.lerp(settledScale, target.expandedScale, expansionEase)
  const terminalPosition = screenToWorld(terminalTarget.sphereX, terminalTarget.sphereY)
  visualGroup.position.copy(expandedPosition.lerp(terminalPosition, terminalEase))
  const currentScale = THREE.MathUtils.lerp(expandedScale, terminalTarget.targetScale, terminalEase)
  visualGroup.scale.setScalar(currentScale)
  renderer.domElement.style.opacity = String(intro)
  if (travel >= 1 && !canInteract.value) {
    canInteract.value = true
    startProjectionSequence()
  }

  visualGroup.rotation.set(0, 0, 0)
  sphereGroup.rotation.y = time * 0.34
  sphereGroup.rotation.x = Math.sin(time * 0.46) * 0.12
  sphereGroup.rotation.z = Math.sin(time * 0.3) * 0.035
  orbitGroup.rotation.x = 0
  orbitGroup.rotation.y = 0
  orbitGroup.rotation.z = -time * 0.22 * (1 - terminalEase)
  if (terminalProgress > 0 || terminalPhase.value === 'closed') {
    const pixelsPerUnit = (window.innerHeight / 8.06) * Math.max(currentScale, 0.001)
    const lineOffset = terminalTarget.lineCenterX - terminalTarget.sphereX
    const verticalOffset = terminalTarget.lineCenterY - terminalTarget.sphereY
    orbitGroup.position.x = (lineOffset / pixelsPerUnit) * terminalEase
    orbitGroup.position.y = (-verticalOffset / pixelsPerUnit) * terminalEase
    const ringScaleY = terminalPhase.value === 'closing'
      ? Math.pow(Math.max(0.002, 1 - terminalEase), 0.28)
      : Math.max(0.002, 1 - terminalEase)
    orbitGroup.scale.set(1, ringScaleY, 1)
  }

  if (outwardParticles) {
    outwardParticles.material.uniforms.uScale.value = currentScale
    updateOutwardParticles(time)
  }
}

function resizeScene() {
  if (!renderer || !camera) return
  const width = window.innerWidth
  const height = window.innerHeight
  viewportSize.value = { width, height }
  const visibleHeight = 8.06
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(width, height, false)
  for (const entry of fatLineMaterials) {
    entry.material.resolution.set(width, height)
  }
  if (outwardParticles) {
    outwardParticles.material.uniforms.uPixelRatio.value = renderer.getPixelRatio()
  }
  const halfHeight = visibleHeight / 2
  const halfWidth = halfHeight * (width / height)
  camera.left = -halfWidth
  camera.right = halfWidth
  camera.top = halfHeight
  camera.bottom = -halfHeight
  camera.updateProjectionMatrix()
}

function animate(now: number) {
  if (!renderer || !scene || !camera) return
  if (!startTime) startTime = now
  const elapsed = (now - startTime) / 1000
  updateScene(elapsed)
  renderer.render(scene, camera)
  animationFrame = requestAnimationFrame(animate)
}

function initScene() {
  const canvas = canvasRef.value
  if (!canvas) return

  try {
    renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance',
    })
    renderer.setClearColor(0x000000, 0)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

    scene = new THREE.Scene()
    camera = new THREE.OrthographicCamera(-4, 4, 4.03, -4.03, 0.1, 100)
    camera.position.z = 10.5

    visualGroup = new THREE.Group()
    sphereGroup = buildSphere()
    orbitGroup = buildOrbit()
    visualGroup.add(sphereGroup, orbitGroup)
    scene.add(visualGroup)

    reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    renderer.domElement.style.opacity = reducedMotion ? '1' : '0'

    applyTheme()
    resizeScene()
    animationFrame = requestAnimationFrame(animate)
  } catch {
    sceneError.value = '当前浏览器无法初始化 3D 场景'
  }
}

function disposeScene() {
  cancelAnimationFrame(animationFrame)
  clearProjectionTimers()
  clearInteractionTimers()
  clearTerminalTimers()
  window.removeEventListener('resize', resizeScene)

  if (scene) {
    const geometries = new Set<THREE.BufferGeometry>()
    const materials = new Set<THREE.Material>()
    scene.traverse((object) => {
      if (object instanceof THREE.Mesh || object instanceof THREE.Line || object instanceof THREE.Points) {
        geometries.add(object.geometry)
        const objectMaterials = Array.isArray(object.material) ? object.material : [object.material]
        for (const material of objectMaterials) materials.add(material)
      }
    })
    for (const geometry of geometries) geometry.dispose()
    for (const material of materials) material.dispose()
  }

  renderer?.dispose()
  renderer = null
  scene = null
  camera = null
  visualGroup = null
  sphereGroup = null
  orbitGroup = null
  outwardParticles = null
  tintedMaterials.length = 0
  fatLineMaterials.length = 0
}

watch(
  () => theme.resolved,
  () => applyTheme(),
)

onMounted(() => {
  theme.init()
  initScene()
  window.addEventListener('resize', resizeScene)
  document.addEventListener('pointerdown', onDocumentPointerDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocumentPointerDown)
  disposeScene()
})
</script>

<style scoped>
.cyberrange-stage {
  position: fixed;
  inset: 0;
  z-index: 1;
  overflow: hidden;
  pointer-events: none;
}

.scene-canvas {
  display: block;
  width: 100%;
  height: 100%;
  opacity: 0;
  filter: drop-shadow(0 0 7px rgba(var(--cyan-rgb), 0.2));
}

.projection-cone {
  position: fixed;
  z-index: 1;
  pointer-events: none;
  transform-origin: left center;
  transition: opacity 0.25s ease, visibility 0.25s ease;
}

.projection-cone-haze,
.projection-cone-core,
.projection-cone-near {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.projection-cone-haze {
  filter: blur(30px);
  transform: scaleY(1.08);
  opacity: 0.68;
}

.projection-cone-haze::before {
  content: '';
  position: absolute;
  inset: 0;
  clip-path: polygon(0 50%, 100% 0, 100% 100%);
  background: linear-gradient(
    90deg,
    rgba(var(--cyan-rgb), 0) 0%,
    rgba(var(--cyan-rgb), 0.05) 28%,
    rgba(var(--cyan-rgb), 0.08) 72%,
    rgba(var(--cyan-rgb), 0) 100%
  );
}

.projection-cone-core {
  filter: blur(12px);
  mix-blend-mode: screen;
  animation: projection-breathe 3.2s ease-in-out infinite;
}

.projection-cone-core::before {
  content: '';
  position: absolute;
  inset: 0;
  clip-path: polygon(0 50%, 100% 12%, 100% 88%);
  background: linear-gradient(
    90deg,
    rgba(var(--cyan-rgb), 0) 0%,
    rgba(var(--cyan-rgb), 0.04) 20%,
    rgba(var(--cyan-rgb), 0.16) 62%,
    rgba(var(--cyan-rgb), 0.05) 100%
  );
}

.projection-cone-near {
  filter: blur(1.2px);
  mix-blend-mode: screen;
  opacity: 0.9;
}

.projection-cone-near::before {
  content: '';
  position: absolute;
  inset: 0;
  clip-path: polygon(0 50%, 100% 24%, 100% 76%);
  background: linear-gradient(
    90deg,
    rgba(var(--cyan-rgb), 0.2) 0%,
    rgba(var(--cyan-rgb), 0.1) 34%,
    rgba(var(--cyan-rgb), 0.03) 68%,
    transparent 100%
  );
  -webkit-mask-image: linear-gradient(
    90deg,
    #000 0%,
    rgba(0, 0, 0, 0.92) 28%,
    rgba(0, 0, 0, 0.42) 72%,
    transparent 100%
  );
  mask-image: linear-gradient(
    90deg,
    #000 0%,
    rgba(0, 0, 0, 0.92) 28%,
    rgba(0, 0, 0, 0.42) 72%,
    transparent 100%
  );
}

.projection-cone::before {
  content: '';
  position: absolute;
  top: calc(50% - 7px);
  left: -7px;
  z-index: 2;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: rgba(var(--cyan-rgb), 0.34);
  box-shadow:
    0 0 12px rgba(var(--cyan-rgb), 0.75),
    0 0 30px rgba(var(--cyan-rgb), 0.38);
}

.projection-cone::after {
  content: '';
  position: absolute;
  top: 10%;
  right: 2%;
  width: 54%;
  height: 80%;
  border-radius: 50%;
  background: radial-gradient(
    ellipse at center,
    rgba(var(--cyan-rgb), 0.12),
    rgba(var(--cyan-rgb), 0.025) 48%,
    transparent 72%
  );
  filter: blur(20px);
  mix-blend-mode: screen;
}

.projection-cone.emitting {
  animation: projection-emit 0.82s cubic-bezier(0.16, 0.76, 0.24, 1) both;
}

.projection-cone.suspended {
  visibility: hidden;
  opacity: 0;
}

.projection-cone.flickering {
  animation: projector-flicker 0.56s steps(2, end) forwards;
}

.hologram {
  position: fixed;
  z-index: 3;
  color: var(--cyan);
  pointer-events: none;
  filter: drop-shadow(0 0 10px rgba(var(--cyan-rgb), 0.24));
  transform: translate(-50%, -50%);
  transition: opacity 0.35s ease, visibility 0.35s ease;
}

.hologram.suspended {
  visibility: hidden;
  opacity: 0;
}

.hologram-copy {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 104px;
  padding: 18px 34px;
  text-align: center;
  transition:
    opacity 0.35s ease,
    filter 0.35s ease,
    transform 0.35s ease;
}

.hologram.dissolving .hologram-copy {
  opacity: 0;
  filter: blur(8px);
  transform: translateY(-8px);
  transition-duration: 0.85s;
}

.hologram.emitting .hologram-copy,
.hologram.stabilizing .hologram-copy {
  opacity: 0;
  filter: blur(5px);
  transform: translateY(5px);
}

.hologram.emitting .hologram-caret,
.hologram.stabilizing .hologram-caret {
  opacity: 0;
  animation: none;
}

.hologram-text {
  display: block;
  max-width: 100%;
  color: var(--cyan);
  font-family: var(--mono);
  font-size: 27px;
  font-weight: 600;
  line-height: 1.6;
  letter-spacing: 0;
  text-shadow:
    0 0 8px rgba(var(--cyan-rgb), 0.42),
    0 0 22px rgba(var(--cyan-rgb), 0.16);
}

.hologram-caret {
  flex-shrink: 0;
  width: 7px;
  height: 1.2em;
  margin-left: 6px;
  background: rgba(var(--cyan-rgb), 0.82);
  box-shadow: 0 0 8px rgba(var(--cyan-rgb), 0.5);
  animation: hologram-caret 0.9s steps(1) infinite;
}

.hologram.dissolving .hologram-caret {
  animation: none;
  opacity: 0;
}

.hologram.flickering .hologram-copy {
  animation: projector-text-flicker 0.56s steps(2, end) forwards;
}

.terminal-build {
  position: fixed;
  z-index: 4;
  pointer-events: none;
}

.terminal-build::before {
  content: '';
  position: absolute;
  inset: 0;
  border: 1px solid rgba(var(--cyan-rgb), 0.2);
  background: rgba(var(--cyan-rgb), 0.055);
  opacity: 0;
  transition: opacity 0.45s ease 0.35s;
}

.terminal-build.opening::before {
  opacity: 0.36;
}

.terminal-build.open::before {
  opacity: 0.62;
}

.terminal-rail {
  position: absolute;
  top: 50%;
  left: 50%;
  z-index: 2;
  width: var(--terminal-line-width);
  height: 1px;
  background: rgba(var(--cyan-rgb), 0.86);
  box-shadow:
    0 0 8px rgba(var(--cyan-rgb), 0.75),
    0 0 24px rgba(var(--cyan-rgb), 0.32);
  transform: translateX(-50%);
  transition:
    top 0.8s cubic-bezier(0.2, 0.8, 0.2, 1),
    left 0.8s cubic-bezier(0.2, 0.8, 0.2, 1),
    width 0.8s cubic-bezier(0.2, 0.8, 0.2, 1),
    transform 0.8s cubic-bezier(0.2, 0.8, 0.2, 1),
    opacity 0.25s ease;
}

.terminal-build.opening .terminal-rail,
.terminal-build.open .terminal-rail {
  left: 0;
  width: 100%;
  transform: none;
}

.terminal-build.closing .terminal-rail {
  opacity: 0;
  transition: opacity 0.12s ease;
}

.terminal-build.closing::before,
.terminal-build.closing .terminal-edge,
.terminal-build.closing .terminal-content {
  opacity: 0;
  transition-duration: 0.16s;
  transition-delay: 0s;
}

.terminal-build.opening .rail-top,
.terminal-build.open .rail-top {
  top: 0;
}

.terminal-build.opening .rail-bottom,
.terminal-build.open .rail-bottom {
  top: calc(100% - 1px);
}

.terminal-edge {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1px;
  background: rgba(var(--cyan-rgb), 0.42);
  opacity: 0;
  transition: opacity 0.4s ease 0.45s;
}

.terminal-edge.edge-left {
  left: 0;
}

.terminal-edge.edge-right {
  right: 0;
}

.terminal-build.opening .terminal-edge,
.terminal-build.open .terminal-edge {
  opacity: 1;
}

.terminal-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 24px 28px;
  color: rgba(var(--cyan-rgb), 0.82);
  font-family: var(--mono);
  opacity: 0;
  transform: translateY(8px);
  transition:
    opacity 0.4s ease,
    transform 0.4s ease;
}

.terminal-build.open .terminal-content {
  opacity: 1;
  transform: translateY(0);
}

.terminal-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(var(--cyan-rgb), 0.16);
  color: rgba(var(--cyan-rgb), 0.68);
  font-size: 10px;
  letter-spacing: 1.2px;
}

.terminal-online {
  color: var(--green);
}

.terminal-log {
  display: flex;
  flex: 1;
  flex-direction: column;
  justify-content: center;
  gap: 7px;
  font-size: 12px;
  line-height: 1.7;
}

.terminal-log p {
  margin: 0;
}

.terminal-prompt {
  color: var(--green);
}

.terminal-input {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: 8px !important;
}

.terminal-block {
  display: inline-block;
  width: 7px;
  height: 1.1em;
  background: rgba(var(--cyan-rgb), 0.78);
  animation: hologram-caret 0.9s steps(1) infinite;
}

@keyframes hologram-caret {
  0%, 48% { opacity: 1; }
  49%, 100% { opacity: 0; }
}

@keyframes projection-breathe {
  0%, 100% { opacity: 0.58; }
  50% { opacity: 0.86; }
}

@keyframes projection-emit {
  0% {
    opacity: 0;
    transform: scaleX(0.015) scaleY(0.4);
    filter: blur(18px);
  }
  38% {
    opacity: 0.52;
  }
  100% {
    opacity: 1;
    transform: scaleX(1) scaleY(1);
    filter: blur(0);
  }
}

@keyframes projector-flicker {
  0%, 100% { opacity: 0.62; }
  10% { opacity: 0.1; }
  22% { opacity: 0.78; }
  38% { opacity: 0.04; }
  55% { opacity: 0.54; }
  72% { opacity: 0.02; }
  86% { opacity: 0.24; }
  100% { opacity: 0; }
}

@keyframes projector-text-flicker {
  0%, 18%, 48%, 100% { opacity: 1; }
  10%, 36%, 70% { opacity: 0.18; }
  82% { opacity: 0; }
}

.scene-error {
  position: absolute;
  top: 96px;
  left: 50%;
  color: var(--muted);
  font-family: var(--mono);
  font-size: 12px;
  transform: translateX(-50%);
}

.sphere-hit {
  position: fixed;
  z-index: 2;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  pointer-events: auto;
  touch-action: manipulation;
}

.sphere-hit:focus-visible {
  outline: 2px solid var(--cyan);
  outline-offset: 4px;
}

@media (max-width: 959px) {
  .hologram-text {
    font-size: 22px;
  }
}

@media (max-width: 820px) {
  .scene-canvas {
    filter: drop-shadow(0 0 5px rgba(var(--cyan-rgb), 0.18));
  }

  .hologram-text {
    font-size: 18px;
  }

  .hologram-copy {
    min-height: 68px;
    padding: 12px 16px;
  }
}
</style>
