import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PredictionResult from '@/components/PredictionResult.vue'

describe('PredictionResult', () => {
  it('shows Negative label and probability as a percentage for prediction=0', () => {
    const wrapper = mount(PredictionResult, {
      props: { prediction: 0, probability: 0.018580961296622237 },
    })
    expect(wrapper.text()).toContain('Negativo')
    expect(wrapper.text()).toContain('1.86%')
  })

  it('shows Positive label for prediction=1', () => {
    const wrapper = mount(PredictionResult, {
      props: { prediction: 1, probability: 0.85 },
    })
    expect(wrapper.text()).toContain('Positivo')
    expect(wrapper.text()).toContain('85.00%')
  })

  it('always includes the non-medical disclaimer', () => {
    const wrapper = mount(PredictionResult, {
      props: { prediction: 0, probability: 0.1 },
    })
    expect(wrapper.text()).toContain('No sustituye la evaluación de un profesional sanitario')
    expect(wrapper.text()).toContain('no un diagnóstico')
  })

  it('emits open-analysis from the "Ver análisis" button', async () => {
    const wrapper = mount(PredictionResult, {
      props: { prediction: 0, probability: 0.1 },
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('open-analysis')).toBeTruthy()
  })
})