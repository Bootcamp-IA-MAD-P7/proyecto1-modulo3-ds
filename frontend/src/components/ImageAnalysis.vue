<script setup>
/**
 * ImageAnalysis — "Análisis de imagen cerebral" (frontend-only).
 *
 * Prepares the interface for a future CNN. Two input sources:
 *   - Camera (UI + getUserMedia wiring prepared, no model)
 *   - Upload an image (file input + preview via FileReader)
 *
 * States handled here (never invents results):
 *   idle      -> no image yet
 *   camera    -> camera view active
 *   preview   -> image selected with preview
 *   analyzing -> UI animation only (no real CNN call)
 *   result    -> external `result` prop provided by the parent (prepared)
 *   error     -> file read failed
 *
 * Emits:
 *   @analyze (imageDataUrl) — parent decides to later call the real model
 */
import { ref, computed, watch } from 'vue'
import { t } from '@/store.js'
import Brain3D from './Brain3D.vue'
import ImageResult from './ImageResult.vue'
import AnalysisStatus from './AnalysisStatus.vue'

const emit = defineEmits(['analyze'])

const props = defineProps({
  /* Future CNN probability result (null by default). */
  result: {
    type: Object,
    default: null,
  },
})

const source = ref('idle') // idle | camera | preview
const mode = ref('upload') // upload | camera (last chosen panel)
const previewUrl = ref('')
const fileName = ref('')
const analyzing = ref(false)
const readError = ref('')

const fileInput = ref(null)

const statusTone = computed(() => {
  if (readError.value) return 'error'
  if (analyzing.value) return 'active'
  if (source.value === 'camera' || source.value === 'preview') return 'success'
  return 'neutral'
})

const statusLabel = computed(() => {
  if (readError.value) return t('imageAnalysis.stateError')
  if (analyzing.value) return t('imageAnalysis.stateAnalyzing')
  if (source.value === 'camera') return t('imageAnalysis.stateCamera')
  if (source.value === 'preview') return t('imageAnalysis.statePreview')
  return t('imageAnalysis.stateReady')
})

watch(
  () => props.result,
  () => {
    if (props.result) analyzing.value = false
  },
)

function chooseCamera() {
  mode.value = 'camera'
  // Camera view is prepared at interface level; getUserMedia is only requested
  // when the user presses "Iniciar cámara". No model processing.
  source.value = 'idle'
}

function chooseUpload() {
  mode.value = 'upload'
  source.value = previewUrl.value ? 'preview' : 'idle'
}

function startCamera() {
  source.value = 'camera'
}

function stopCamera() {
  source.value = 'idle'
}

function onFileSelected(event) {
  const file = event.target.files && event.target.files[0]
  readError.value = ''
  analyzing.value = false
  if (!file) return

  const reader = new FileReader()
  reader.onload = () => {
    previewUrl.value = String(reader.result || '')
    fileName.value = file.name
    source.value = 'preview'
  }
  reader.onerror = () => {
    readError.value = t('imageAnalysis.invalidFile')
    source.value = 'idle'
  }
  try {
    reader.readAsDataURL(file)
  } catch {
    readError.value = t('imageAnalysis.invalidFile')
  }
}

function pickFile() {
  if (fileInput.value) fileInput.value.click()
}

function clearImage() {
  previewUrl.value = ''
  fileName.value = ''
  source.value = 'idle'
  analyzing.value = false
  if (fileInput.value) fileInput.value.value = ''
}

function runAnalysis() {
  if (source.value !== 'preview') return
  // UI-only analysis animation. The real CNN is NOT called yet.
  analyzing.value = true
  emit('analyze', previewUrl.value)
}
</script>

<template>
  <section class="ian" aria-label="Análisis de imagen cerebral">
    <div class="ian__head">
      <div class="ian__tabs" role="tablist">
        <button
          type="button"
          class="ian__tab"
          :class="{ 'is-active': mode === 'camera' }"
          role="tab"
          :aria-selected="mode === 'camera'"
          @click="chooseCamera"
        >
          {{ t('imageAnalysis.useCamera') }}
        </button>
        <button
          type="button"
          class="ian__tab"
          :class="{ 'is-active': mode === 'upload' }"
          role="tab"
          :aria-selected="mode === 'upload'"
          @click="chooseUpload"
        >
          {{ t('imageAnalysis.uploadImage') }}
        </button>
      </div>
      <AnalysisStatus :tone="statusTone" :label="statusLabel" />
    </div>

    <!-- CAMERA PANEL -->
    <div v-if="mode === 'camera'" class="ian__panel">
      <div class="ian__stage">
        <div v-if="source === 'idle'" class="ian__empty">
          <svg class="ian__cam" viewBox="0 0 24 24" aria-hidden="true">
            <path
              d="M4 8h3l1.5-2h7L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z"
              fill="none"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linejoin="round"
            />
            <circle cx="12" cy="13" r="3.2" fill="none" stroke="currentColor" stroke-width="1.7" />
          </svg>
          <p class="ian__empty-text">{{ t('imageAnalysis.cameraTitle') }}</p>
          <p class="ian__permission">{{ t('imageAnalysis.cameraPermission') }}</p>
          <button type="button" class="ian__primary" @click="startCamera">
            {{ t('imageAnalysis.cameraStart') }}
          </button>
        </div>

        <div v-else class="ian__feed">
          <div class="ian__live"></div>
          <span class="ian__live-chip">{{ t('imageAnalysis.cameraActive') }}</span>
          <button type="button" class="ian__ghost" @click="stopCamera">
            {{ t('imageAnalysis.cameraStop') }}
          </button>
        </div>
      </div>
    </div>

    <!-- UPLOAD PANEL -->
    <div v-else class="ian__panel">
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        class="ian__input"
        aria-label="Seleccionar imagen"
        @change="onFileSelected"
      />

      <div v-if="source !== 'preview'" class="ian__stage">
        <div class="ian__empty">
          <svg class="ian__cam" viewBox="0 0 24 24" aria-hidden="true">
            <path
              d="M4 6h5l2 2h9a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1Z"
              fill="none"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linejoin="round"
            />
            <path d="M8 14h0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          </svg>
          <p class="ian__empty-text">{{ t('imageAnalysis.noImage') }}</p>
          <p class="ian__permission">{{ t('imageAnalysis.twoSources') }}</p>
          <button type="button" class="ian__primary" @click="pickFile">
            {{ t('imageAnalysis.selectImage') }}
          </button>
        </div>
      </div>

      <div v-else class="ian__stage ian__stage--preview">
        <div class="ian__preview">
          <img v-if="previewUrl" :src="previewUrl" alt="Previsualización de la imagen seleccionada" />
          <span class="ian__ok">{{ t('imageAnalysis.imageSelected') }} ✓</span>
        </div>

        <div class="ian__actions">
          <button type="button" class="ian__ghost" @click="pickFile">
            {{ t('imageAnalysis.changeImage') }}
          </button>
          <button
            type="button"
            class="ian__primary"
            :disabled="analyzing"
            @click="runAnalysis"
          >
            {{ analyzing ? t('imageAnalysis.analyzingImage') : t('imageAnalysis.analyzeImage') }}
          </button>
        </div>
      </div>

      <p v-if="readError" class="ian__error" role="alert">{{ readError }}</p>
    </div>

    <!-- RESULT / HEATMAP / BRAIN 3D (prepared for future) -->
    <div class="ian__results">
      <div class="ian__result-card">
        <h4 class="ian__result-title">{{ t('imageResult.title') }}</h4>
        <ImageResult :result="result" />
      </div>

      <div class="ian__result-card">
        <h4 class="ian__result-title">{{ t('imageAnalysis.gradCamTitle') }}</h4>
        <div class="ian__grad">
          <span class="ian__grad-tag">{{ t('imageAnalysis.zoneOfInterest') }}</span>
          <p class="ian__grad-hint">{{ t('imageAnalysis.gradCamHint') }}</p>
        </div>
      </div>

      <div class="ian__result-card">
        <h4 class="ian__result-title">{{ t('brain.title') }}</h4>
        <Brain3D
          :state="analyzing ? 'analyzing' : 'idle'"
          :percent="analyzing ? 46 : 0"
        />
        <div class="ian__source">
          <span>{{ t('imageAnalysis.originalLabel') }} →</span>
          <span>{{ t('imageAnalysis.heatmapLabel') }} →</span>
          <span>Brain3D</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ian {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.ian__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.ian__tabs {
  display: inline-flex;
  gap: 6px;
  background: var(--color-canvas-soft);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  padding: 4px;
}

.ian__tab {
  font-size: 13px;
  font-weight: var(--w-600);
  color: var(--color-ink-mute);
  padding: 8px 16px;
  border-radius: var(--radius-pill);
  transition: background 180ms ease, color 180ms ease;
}

.ian__tab.is-active {
  background: var(--color-accent);
  color: var(--color-on-accent);
}

.ian__panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ian__stage {
  border: 1px dashed var(--color-hairline);
  border-radius: var(--radius-md);
  background: var(--color-canvas-soft);
  min-height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.ian__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
  max-width: 360px;
}

.ian__cam {
  width: 42px;
  height: 42px;
  color: var(--color-accent-strong);
  opacity: 0.85;
}

.ian__empty-text {
  font-size: 15px;
  font-weight: var(--w-700);
  color: var(--color-primary);
}

.ian__permission {
  font-size: 12.5px;
  color: var(--color-ink-mute);
}

.ian__input {
  display: none;
}

.ian__feed {
  position: relative;
  width: 100%;
  min-height: 220px;
  border-radius: var(--radius-md);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.ian__live {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(90% 90% at 50% 40%, rgba(244, 201, 93, 0.22), transparent 60%),
    linear-gradient(160deg, #1b2d51 0%, #0a1730 100%);
}

.ian__live::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(transparent 48%, rgba(244, 201, 93, 0.3) 50%, transparent 52%);
  animation: scan 2.4s linear infinite;
  mix-blend-mode: screen;
}

.ian__live-chip {
  position: relative;
  font-size: 11px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: #fff;
  background: rgba(7, 20, 38, 0.6);
  border: 1px solid rgba(244, 201, 93, 0.5);
  border-radius: var(--radius-pill);
  padding: 6px 14px;
}

.ian__stage--preview {
  flex-direction: column;
  gap: 14px;
}

.ian__preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.ian__preview img {
  max-width: 260px;
  max-height: 200px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-hairline);
  box-shadow: var(--shadow-sm);
}

.ian__ok {
  font-size: 13px;
  font-weight: var(--w-600);
  color: var(--color-positive);
}

.ian__actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.ian__primary {
  font-size: 13px;
  font-weight: var(--w-600);
  color: var(--color-on-accent);
  background: var(--color-accent-strong);
  border-radius: var(--radius-pill);
  padding: 10px 20px;
  transition: background 180ms ease, transform 180ms ease;
}

.ian__primary:hover:not(:disabled) {
  background: var(--color-accent-deep);
  transform: translateY(-1px);
}

.ian__primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ian__ghost {
  font-size: 13px;
  font-weight: var(--w-600);
  color: var(--color-primary);
  border: 1px solid var(--color-hairline);
  background: var(--color-card);
  border-radius: var(--radius-pill);
  padding: 10px 20px;
  transition: background 180ms ease;
}

.ian__ghost:hover {
  background: var(--color-canvas-soft);
}

.ian__error {
  font-size: 12.5px;
  color: var(--color-risk);
}

.ian__results {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 18px;
  margin-top: 6px;
}

.ian__result-card {
  background: var(--color-card);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ian__result-title {
  font-size: 13px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-accent-strong);
}

.ian__grad {
  display: flex;
  flex-direction: column;
  gap: 8px;
  border: 1px dashed var(--color-hairline);
  border-radius: var(--radius-md);
  padding: 18px;
  text-align: center;
  flex: 1;
}

.ian__grad-tag {
  align-self: center;
  font-size: 11px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-accent-strong);
  background: rgba(217, 169, 40, 0.12);
  border: 1px solid rgba(217, 169, 40, 0.28);
  border-radius: var(--radius-pill);
  padding: 5px 14px;
}

.ian__grad-hint {
  font-size: 12.5px;
  color: var(--color-ink-mute);
}

.ian__source {
  display: flex;
  justify-content: center;
  gap: 10px;
  font-size: 11px;
  color: var(--color-ink-faint);
}

@keyframes scan {
  0% {
    transform: translateY(-100%);
  }
  100% {
    transform: translateY(100%);
  }
}

@media (max-width: 980px) {
  .ian__results {
    grid-template-columns: 1fr;
  }
}
</style>