/**
 * Multimodal analysis components — frontend evolution tests.
 *
 * Covers the new Brain3D / ImageAnalysis / ImageResult components:
 *  - Brain3D renders each conceptual visual state (idle/analyzing/result/zone)
 *  - Brain3D copy is localized and re-translates on language switch
 *  - ImageAnalysis exposes camera + upload tabs and its stateflow
 *  - Brain3D never claims a medical localization (uses "zona de interés")
 */
import { describe, it, expect, beforeEach } from 'vitest'
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

  it('shows the ready/NEURAL SYSTEM state by default', () => {
    const wrapper = mount(Brain3D)
    expect(wrapper.text()).toContain(translations.es.brain.ready)
    expect(wrapper.text()).toContain(translations.es.brain.readyHint)
  })

  it('shows the analyzing state with a progress bar', () => {
    const wrapper = mount(Brain3D, { props: { state: 'analyzing', percent: 46 } })
    expect(wrapper.text()).toContain(translations.es.brain.analyzing)
    expect(wrapper.find('[role="progressbar"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('46%')
  })

  it('shows the risk visualization result state', () => {
    const wrapper = mount(Brain3D, {
      props: { state: 'result', label: translations.es.posHint },
    })
    expect(wrapper.text()).toContain(translations.es.brain.riskLabel)
    expect(wrapper.text()).toContain(translations.es.posHint)
  })

  it('uses "zona de interés" wording (no medical localization claim)', () => {
    const wrapper = mount(Brain3D, { props: { state: 'zone' } })
    expect(wrapper.text()).toContain(translations.es.brain.zoneLabel)
    const zoneText = translations.es.brain.zoneText.toLowerCase()
    const subText = translations.es.brain.zoneSubtext.toLowerCase()
    expect(zoneText.includes('zona de interés')).toBe(true)
    expect(subText.includes('no localiza')).toBe(true)
    // Never mentions an exact lesion location.
    expect(wrapper.text().toLowerCase()).not.toContain('zona exacta')
  })

  it('re-translates copy when switching to English', async () => {
    const wrapper = mount(Brain3D, { props: { state: 'zone' } })
    expect(wrapper.text()).toContain(translations.es.brain.zoneLabel)
    setLanguage('en')
    await flushPromises()
    expect(wrapper.text()).toContain(translations.en.brain.zoneLabel)
    expect(wrapper.text()).toContain(translations.en.brain.zoneText)
    setLanguage('es')
    await flushPromises()
    expect(wrapper.text()).toContain(translations.es.brain.zoneLabel)
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

  it('renders ImageResult and Brain3D prepared areas', () => {
    const wrapper = mount(ImageAnalysis)
    expect(wrapper.text()).toContain(translations.es.imageResult.notConnected)
    expect(wrapper.findComponent(ImageResult).exists()).toBe(true)
  })
})