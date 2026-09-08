/**
 * Análisis view — under-construction checks (reorganisation).
 *
 * After the Home/Inicio reorganisation, the Análisis view is the reserved
 * space for the future CNN image analysis:
 *  - EN CONSTRUCCIÓN badge with an inline construction-helmet icon
 *  - The camera/upload interface stays (CNN not connected)
 *  - NO Brain3D, NO Grad-CAM / Activation Map, NO Image Analysis Result here
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setLanguage } from '@/store.js'
import { translations } from '@/i18n/translations.js'
import Analysis from '@/views/Analysis.vue'
import ImageAnalysis from '@/components/ImageAnalysis.vue'
import Brain3D from '@/components/Brain3D.vue'

describe('Analysis view (EN CONSTRUCCIÓN)', () => {
  beforeEach(() => {
    setLanguage('es')
  })

  it('is headed by the "Análisis multimodal" title inside the construction page', () => {
    const wrapper = mount(Analysis)
    expect(wrapper.text()).toContain(translations.es.analysis.title)
    expect(wrapper.text()).toContain(translations.es.construction.badge)
  })

  it('shows the construction helmet icon inside the badge (inline SVG, no library)', () => {
    const wrapper = mount(Analysis)
    expect(wrapper.find('.analyse__badge-helmet').exists()).toBe(true)
  })

  it('keeps the camera/upload image analysis interface (CNN not connected)', () => {
    const wrapper = mount(Analysis)
    expect(wrapper.findComponent(ImageAnalysis).exists()).toBe(true)
    expect(wrapper.text()).toContain(translations.es.imageAnalysis.useCamera)
    expect(wrapper.text()).toContain(translations.es.imageAnalysis.uploadImage)
  })

  it('never renders Brain3D, Grad-CAM / Activation Map or Image Analysis Result', () => {
    const wrapper = mount(Analysis)
    expect(wrapper.findComponent(Brain3D).exists()).toBe(false)
    expect(wrapper.find('.analyse__panel-note').exists()).toBe(false)
    expect(wrapper.text()).not.toContain(translations.es.imageAnalysis.gradCamTitle)
    expect(wrapper.text()).not.toContain(translations.es.imageResult.notConnected)
    expect(wrapper.text().toLowerCase()).not.toContain('brain3d')
  })

  it('shows a semi-transparent under-construction overlay on the image analysis interface', () => {
    const wrapper = mount(Analysis)
    const overlay = wrapper.find('.analyse__overlay')
    expect(overlay.exists()).toBe(true)
    expect(overlay.attributes('aria-hidden')).toBe('true')
    expect(overlay.text()).toContain(translations.es.construction.badge)
    expect(overlay.text()).toContain(translations.es.construction.overlay)
  })
})