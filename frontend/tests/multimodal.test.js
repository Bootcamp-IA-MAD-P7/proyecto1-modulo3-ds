/**
 * Multimodal analysis components — frontend evolution tests.
 *
 * Covers the Brain3D / ImageAnalysis / ImageResult components:
 *  - Brain3D renders each conceptual state (idle/analyzing/low/medium/high)
 *  - Brain3D risk copy is localized and re-translates on language switch
 *  - Brain3D never claims a medical localization (no lesion/zone assertions)
 *  - ImageAnalysis exposes camera + upload tabs and its stateflow
 *  - ImageAnalysis no longer renders Image Analysis Result / Grad-CAM / Brain3D
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setLanguage, setTheme } from '@/store.js'
import { translations } from '@/i18n/translations.js'
import Brain3D from '@/components/Brain3D.vue'
import ImageAnalysis from '@/components/ImageAnalysis.vue'
import ImageResult from '@/components/ImageResult.vue'

describe('Brain3D visual states', () => {
  beforeEach(() => {
    setTheme('light')
    setLanguage('es')
  })

  it('stays neutral before any evaluation (no NEURAL SYSTEM, no risk text)', () => {
    const wrapper = mount(Brain3D)
    // The brain itself is the message; only the disclaimer is shown.
    expect(wrapper.text()).toContain(translations.es.brain.noDiagnosis)
    expect(wrapper.text()).not.toContain(translations.es.brain.ready)
    expect(wrapper.text()).not.toContain(translations.es.risk.levelLow)
    expect(wrapper.find('.brain__chip').exists()).toBe(false)
  })

  it('shows the analyzing state with a progress bar (no definitive risk yet)', () => {
    const wrapper = mount(Brain3D, { props: { state: 'analyzing', percent: 46 } })
    expect(wrapper.text()).toContain(translations.es.brain.analyzing)
    expect(wrapper.find('[role="progressbar"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('46%')
    expect(wrapper.find('.brain__chip').exists()).toBe(false)
  })

  it('LOW risk: green-level text + probability', () => {
    const wrapper = mount(Brain3D, { props: { state: 'low', percent: 20 } })
    expect(wrapper.text()).toContain(translations.es.risk.levelLow)
    expect(wrapper.text()).toContain('20%')
    expect(wrapper.find('.brain__chip--low').exists()).toBe(true)
  })

  it('MEDIUM risk: medium-level text + probability', () => {
    const wrapper = mount(Brain3D, { props: { state: 'medium', percent: 45 } })
    expect(wrapper.text()).toContain(translations.es.risk.levelMedium)
    expect(wrapper.text()).toContain('45%')
    expect(wrapper.find('.brain__chip--medium').exists()).toBe(true)
  })

  it('HIGH risk: elevated-level text + probability', () => {
    const wrapper = mount(Brain3D, { props: { state: 'high', percent: 72 } })
    expect(wrapper.text()).toContain(translations.es.risk.levelHigh)
    expect(wrapper.text()).toContain('72%')
    expect(wrapper.find('.brain__chip--high').exists()).toBe(true)
  })

  it('supports an optional label override for the risk text', () => {
    const wrapper = mount(Brain3D, { props: { state: 'high', label: 'Custom label' } })
    expect(wrapper.text()).toContain('Custom label')
  })

  it('never claims a lesion, zone or exact location in any state', () => {
    const wrapper = mount(Brain3D, { props: { state: 'high' } })
    expect(wrapper.text()).not.toContain(translations.es.brain.zoneLabel)
    expect(wrapper.text().toLowerCase()).not.toContain('zona exacta')
    expect(wrapper.text().toLowerCase()).not.toContain('NEURAL SYSTEM'.toLowerCase())
  })

  it('re-translates risk copy when switching to English', async () => {
    const wrapper = mount(Brain3D, { props: { state: 'high', percent: 62 } })
    expect(wrapper.text()).toContain(translations.es.risk.levelHigh)
    setLanguage('en')
    await flushPromises()
    expect(wrapper.text()).toContain(translations.en.risk.levelHigh)
    expect(wrapper.text()).toContain('62%')
    setLanguage('es')
    await flushPromises()
    expect(wrapper.text()).toContain(translations.es.risk.levelHigh)
  })
})

describe('ImageResult prepared state', () => {
  beforeEach(() => {
    setLanguage('es')
  })

  it('shows a "no result" prepared state and never invents numbers', () => {
    const wrapper = mount(ImageResult)
    expect(wrapper.text()).toContain(translations.es.imageResult.noResult)
    expect(wrapper.text()).toContain(translations.es.imageResult.notConnected)
    expect(wrapper.find('.iresult__rows').exists()).toBe(false)
  })

  it('renders stroke vs no-stroke when a future result is provided', () => {
    const wrapper = mount(ImageResult, {
      props: { result: { stroke: 0.82, noStroke: 0.18, model: 'CNN' } },
    })
    expect(wrapper.text()).toContain('82%')
    expect(wrapper.text()).toContain('18%')
  })
})

describe('ImageAnalysis interface', () => {
  beforeEach(() => {
    setLanguage('es')
  })

  it('offers both camera and upload options', () => {
    const wrapper = mount(ImageAnalysis)
    const tabs = wrapper.findAll('.ian__tab')
    expect(tabs.length).toBe(2)
    expect(wrapper.text()).toContain(translations.es.imageAnalysis.useCamera)
    expect(wrapper.text()).toContain(translations.es.imageAnalysis.uploadImage)
  })

  it('switches to camera panel on click', async () => {
    const wrapper = mount(ImageAnalysis)
    const cameraTab = wrapper.findAll('.ian__tab')[0]
    await cameraTab.trigger('click')
    expect(wrapper.text()).toContain(translations.es.imageAnalysis.cameraTitle)
    expect(wrapper.text()).toContain(translations.es.imageAnalysis.cameraStart)
  })

  it('shows "no image" upload state until an image is selected', async () => {
    const wrapper = mount(ImageAnalysis)
    // Initially no preview/analyze button: user must first select an image.
    expect(wrapper.text()).toContain(translations.es.imageAnalysis.noImage)
    expect(wrapper.text()).toContain(translations.es.imageAnalysis.selectImage)
    const analyzeBtn = wrapper.findAll('.ian__primary').find((b) =>
      b.text().includes(translations.es.imageAnalysis.analyzeImage),
    )
    expect(analyzeBtn).toBeUndefined()
  })

  it('no longer renders Image Analysis Result, Grad-CAM or Brain3D (reorganization)', () => {
    const wrapper = mount(ImageAnalysis)
    // The CNS results block was removed from this view: the 3D brain with its
    // risk level lives only in Inicio (Dashboard).
    expect(wrapper.findComponent(ImageResult).exists()).toBe(false)
    expect(wrapper.findComponent(Brain3D).exists()).toBe(false)
    expect(wrapper.find('.ian__results').exists()).toBe(false)
    expect(wrapper.text()).not.toContain(translations.es.imageResult.notConnected)
    expect(wrapper.text()).not.toContain(translations.es.imageAnalysis.gradCamTitle)
  })

  it('disables the fake analysis while no real CNN exists (no emit, no animation)', async () => {
    // Stub FileReader so selecting a file yields an instant in-memory preview.
    const file = new File(['x'], 'brain.png', { type: 'image/png' })
    class FakeReader {
      readAsDataURL() {
        this.onload({ target: { result: 'data:image/png;base64,eA==' } })
      }
    }
    vi.stubGlobal('FileReader', FakeReader)

    const wrapper = mount(ImageAnalysis)
    const input = wrapper.find('.ian__input')
    Object.defineProperty(input.element, 'files', { value: [file], configurable: true })
    await input.trigger('change')
    await flushPromises()
    vi.unstubAllGlobals()

    // Preview is shown, but "Analizar imagen" stays DISABLED: the CNN model is
    // not connected, so no fake prediction/animation may run.
    expect(wrapper.text()).toContain(translations.es.imageAnalysis.imageSelected)
    const analyzeBtn = wrapper.findAll('.ian__primary').find((b) =>
      b.text().includes(translations.es.imageAnalysis.analyzeImage),
    )
    expect(analyzeBtn).toBeTruthy()
    expect(analyzeBtn.attributes('disabled')).toBeDefined()
    await analyzeBtn.trigger('click')
    expect(wrapper.emitted('analyze')).toBeUndefined()
    expect(wrapper.text()).toContain(translations.es.imageAnalysis.analyzeImage)

    // The under-construction / not-ready note is displayed.
    expect(wrapper.text()).toContain(translations.es.imageAnalysis.notReady)
  })
})