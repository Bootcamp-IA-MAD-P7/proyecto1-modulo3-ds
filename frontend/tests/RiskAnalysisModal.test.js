import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import RiskAnalysisModal from '@/components/RiskAnalysisModal.vue'

const FACTORS = {
  age: '45',
  work_type: 'Private',
  hypertension: 'No',
  avg_glucose_level: '100',
  bmi: '25',
}

describe('RiskAnalysisModal (Issue #036)', () => {
  beforeEach(() => {
    setBodyText('')
  })

  afterEach(() => {
    setBodyText('')
  })

  function setBodyText(text) {
    document.body.innerHTML = text
  }

  function mountOpen() {
    return mount(RiskAnalysisModal, {
      props: {
        open: true,
        prediction: 0,
        probability: 0.02,
        factors: FACTORS,
      },
    })
  }

  it('does not render content when closed', () => {
    const wrapper = mount(RiskAnalysisModal, {
      props: { open: false, prediction: 0, probability: 0, factors: {} },
    })
    expect(wrapper.find('[data-testid="risk-modal"]').exists()).toBe(false)
    expect(document.querySelector('[data-testid="risk-modal"]')).toBeNull()
  })

  it('opens and shows probability as percentage + relevant factors', async () => {
    const wrapper = mountOpen()
    await flushPromises()
    const modal = document.querySelector('[data-testid="risk-modal"]')
    expect(modal).toBeTruthy()
    expect(modal.textContent).toContain('2.00%')
    expect(modal.textContent).toContain('Factores relevantes introducidos')
    expect(modal.textContent).toContain('work_type')
    expect(modal.textContent).toContain('age')
    wrapper.unmount()
  })

  it('closes via the "Cerrar" button and emits close', async () => {
    const wrapper = mount(RiskAnalysisModal, {
      props: { open: true, prediction: 0, probability: 0.02, factors: FACTORS },
    })
    await flushPromises()
    const closeBtn = [...document.querySelectorAll('button')].find(
      (b) => b.textContent.trim() === 'Cerrar',
    )
    expect(closeBtn).toBeTruthy()
    closeBtn.click()
    await flushPromises()
    expect(wrapper.emitted('close')).toBeTruthy()
    wrapper.unmount()
  })

  it('closes when the backdrop is clicked', async () => {
    const wrapper = mount(RiskAnalysisModal, {
      props: { open: true, prediction: 0, probability: 0.02, factors: FACTORS },
    })
    await flushPromises()
    const backdrop = document.querySelector('[data-testid="modal-backdrop"]')
    expect(backdrop).toBeTruthy()
    // Clicking the backdrop itself (target === currentTarget) closes.
    backdrop.dispatchEvent(
      new MouseEvent('click', { bubbles: true }),
    )
    await flushPromises()
    expect(wrapper.emitted('close')).toBeTruthy()
    wrapper.unmount()
  })
})