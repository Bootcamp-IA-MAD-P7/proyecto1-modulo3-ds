import { describe, it, expect, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import PatientAssessmentForm from '@/components/PatientAssessmentForm.vue'
import { FIELD_DEFINITIONS } from '@/components/formFields.js'
import { translations } from '@/i18n/translations.js'
import { setLanguage, state } from '@/store.js'

const VALID_STRING = {
  gender: 'Female',
  age: '45',
  hypertension: '0',
  heart_disease: '1',
  ever_married: 'Yes',
  work_type: 'Private',
  Residence_type: 'Urban',
  avg_glucose_level: '100',
  bmi: '25',
  smoking_status: 'never smoked',
}

/**
 * Fill the form by mutating the reactive `model` exposed on the instance.
 * Properties are set individually (the object is a `const reactive(...)`).
 */
function fillModel(wrapper, values) {
  for (const [key, value] of Object.entries(values)) {
    wrapper.vm.model[key] = value
  }
}

describe('PatientAssessmentForm', () => {
  let wrapper

  beforeEach(() => {
    setLanguage('es')
    wrapper = mount(PatientAssessmentForm)
  })

  it('renders the 10 required fields', () => {
    const fields = FIELD_DEFINITIONS
    expect(fields).toHaveLength(10)
    for (const field of fields) {
      expect(wrapper.find(`#field-${field.key}`).exists()).toBe(true)
    }
  })

  it('has an "Analizar riesgo" submit button', () => {
    const btn = wrapper.find('button[type="submit"]')
    expect(btn.exists()).toBe(true)
    expect(btn.text()).toContain('Analizar riesgo')
  })

  it('exposes exact backend categories in select options', () => {
    const optionsFor = (key) =>
      wrapper
        .find(`#field-${key}`)
        .findAll('option')
        .map((o) => o.attributes('value'))
        .filter((v) => v !== '') // skip the disabled placeholder

    expect(optionsFor('gender')).toEqual(['Male', 'Female'])
    expect(optionsFor('ever_married')).toEqual(['Yes', 'No'])
    expect(optionsFor('work_type')).toEqual([
      'Govt_job',
      'Private',
      'Self-employed',
      'children',
    ])
    expect(optionsFor('Residence_type')).toEqual(['Rural', 'Urban'])
    expect(optionsFor('smoking_status')).toEqual([
      'never smoked',
      'formerly smoked',
      'smokes',
      'Unknown',
    ])
  })

  it('does not emit submit when form is empty/invalid', async () => {
    await wrapper.find('form').trigger('submit')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('emits submit with a numeric payload when valid', async () => {
    fillModel(wrapper, VALID_STRING)
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const events = wrapper.emitted('submit')
    expect(events).toBeDefined()
    const payload = events[0][0]
    expect(payload.age).toBe(45)
    expect(payload.hypertension).toBe(0)
    expect(payload.bmi).toBe(25)
    expect(payload.gender).toBe('Female')
    expect(payload.smoking_status).toBe('never smoked')
  })

  it('shows field errors for invalid numeric ranges and does not submit', async () => {
    fillModel(wrapper, {
      ...VALID_STRING,
      age: '200', // out of range
      bmi: '2', // < 5
    })
    await wrapper.find('#field-age').trigger('blur')
    await wrapper.find('#field-bmi').trigger('blur')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')).toBeUndefined()
    const errText = wrapper.text()
    expect(errText).toContain('Introduce una edad válida entre 0 y 130 años')
    expect(errText).toContain('Introduce un IMC válido entre 5 y 100')
  })

  it('shows required errors when fields are left empty', async () => {
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.emitted('submit')).toBeUndefined()
    expect(wrapper.text()).toContain('Este campo es obligatorio')
  })

  it('localizes validation messages reactively across ES -> EN -> ES', async () => {
    fillModel(wrapper, { ...VALID_STRING, gender: '', age: '200', bmi: '2' })
    await wrapper.find('#field-age').trigger('blur')
    await wrapper.find('#field-bmi').trigger('blur')
    // Submit marks every field touched so empty "required" errors also appear.
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    // Spanish is the default language.
    let errText = wrapper.text()
    expect(errText).toContain(translations.es.validation.age)
    expect(errText).toContain(translations.es.validation.bmi)
    expect(errText).toContain(translations.es.validation.required)

    // Switch to English without reloading: messages update immediately.
    setLanguage('en')
    await flushPromises()
    errText = wrapper.text()
    expect(errText).toContain(translations.en.validation.age)
    expect(errText).toContain(translations.en.validation.bmi)
    expect(errText).toContain(translations.en.validation.required)

    // Switch back to Spanish: messages return to Spanish.
    setLanguage('es')
    await flushPromises()
    errText = wrapper.text()
    expect(errText).toContain(translations.es.validation.age)
    expect(errText).toContain(translations.es.validation.bmi)
    expect(errText).toContain(translations.es.validation.required)
  })

  it('keeps validation rules and the API payload unchanged in both languages', async () => {
    fillModel(wrapper, VALID_STRING)
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const payloadES = wrapper.emitted('submit')[0][0]
    setLanguage('en')
    wrapper.vm.model.gender = ''
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    setLanguage('es')
    fillModel(wrapper, VALID_STRING)
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    const payloadEN = wrapper.emitted('submit')[1][0]

    // Payload is identical regardless of display language.
    expect(payloadEN).toEqual(payloadES)
    // Numeric features are sent as numbers, categories keep backend values.
    expect(payloadEN.age).toBe(45)
    expect(payloadEN.hypertension).toBe(0)
    expect(payloadEN.heart_disease).toBe(1)
    expect(payloadEN.bmi).toBe(25)
    expect(payloadEN.avg_glucose_level).toBe(100)
    expect(payloadEN.gender).toBe('Female')
    expect(payloadEN.work_type).toBe('Private')
    expect(payloadEN.Residence_type).toBe('Urban')
    expect(payloadEN.smoking_status).toBe('never smoked')
    expect(payloadEN.ever_married).toBe('Yes')
  })

  it('does not change field/category option values across languages', async () => {
    const optionsFor = (key) =>
      wrapper
        .find(`#field-${key}`)
        .findAll('option')
        .map((o) => o.attributes('value'))
        .filter((v) => v !== '')

    const before = FIELD_DEFINITIONS.map((f) => optionsFor(f.key))
    setLanguage('en')
    const after = FIELD_DEFINITIONS.map((f) => optionsFor(f.key))
    expect(after).toEqual(before)
    expect(state.language).toBe('en')
    setLanguage('es')
  })
})