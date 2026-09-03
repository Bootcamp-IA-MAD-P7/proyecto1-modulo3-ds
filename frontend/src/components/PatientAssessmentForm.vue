<script setup>
/**
 * Patient assessment form (visual redesign).
 * Collects the 10 model features, validates them on the frontend (required,
 * ranges, exact categories), and only emits "submit" with a valid payload.
 * The data contract / property names / categories are UNCHANGED.
 */
import { reactive } from 'vue'
import { FIELD_DEFINITIONS, NUMBER_RULES, isEmptyValue } from './formFields.js'
import { fieldLabel, optionLabel, t, state } from '@/store.js'

const emit = defineEmits(['submit'])

const model = reactive({
  gender: '',
  age: '',
  hypertension: '',
  heart_disease: '',
  ever_married: '',
  work_type: '',
  Residence_type: '',
  avg_glucose_level: '',
  bmi: '',
  smoking_status: '',
})

const touched = reactive({})
// errors[key] stores a localized message descriptor { key } so the visible text
// re-translates reactively when the user switches ES/EN (no reload needed).
const errors = reactive({})

const fieldKeys = FIELD_DEFINITIONS.map((f) => f.key)

function isNumberValid(field, value) {
  const num = Number(value)
  if (value === '' || Number.isNaN(num)) return false
  const rule = NUMBER_RULES[field.key]
  if (!rule) return true
  if (num < rule.min) return false
  if (rule.max !== Infinity && num > rule.max) return false
  return true
}

function setError(field, msgKey) {
  errors[field.key] = { key: msgKey }
}

/** Resolves the current, language-aware message for a field's error descriptor. */
function errorText(fieldKey) {
  const descriptor = errors[fieldKey]
  if (!descriptor) return ''
  return t(descriptor.key)
}

function validateField(field) {
  const value = model[field.key]

  if (isEmptyValue(field, value)) {
    setError(field, 'validation.required')
    return
  }

  if (field.type === 'number') {
    const num = Number(value)
    if (Number.isNaN(num)) {
      setError(field, 'validation.invalidNumber')
      return
    }
    const rule = NUMBER_RULES[field.key]
    if (rule) {
      const belowMin = num < rule.min
      const aboveMax = rule.max !== Infinity && num > rule.max
      if (belowMin || aboveMax) {
        // age / avg_glucose_level / bmi have purpose-written, localized messages
        // that already include the exact range from NUMBER_RULES.
        setError(field, `validation.${field.key}`)
        return
      }
    }
  }

  if (field.type === 'select' && field.options && !field.options.includes(value)) {
    setError(field, 'validation.invalidSelect')
    return
  }

  delete errors[field.key]
}

function onBlur(field) {
  touched[field.key] = true
  validateField(field)
}

function onSubmit() {
  fieldKeys.forEach((key) => {
    touched[key] = true
    const field = FIELD_DEFINITIONS.find((f) => f.key === key)
    validateField(field)
  })

  if (Object.keys(errors).length > 0) return

  const payload = {}
  for (const field of FIELD_DEFINITIONS) {
    if (field.type === 'number' || field.asNumber) {
      payload[field.key] = Number(model[field.key])
    } else {
      payload[field.key] = model[field.key]
    }
  }
  emit('submit', payload)
}
</script>

<template>
  <form class="form" novalidate @submit.prevent="onSubmit">
    <div class="form__grid">
      <div
        v-for="field in FIELD_DEFINITIONS"
        :key="field.key"
        class="form__field"
      >
        <label class="form__label" :for="`field-${field.key}`">
          {{ fieldLabel(field.key) }}
        </label>

        <select
          v-if="field.type === 'select'"
          :id="`field-${field.key}`"
          v-model="model[field.key]"
          class="form__control"
          :class="{ 'form__control--error': touched[field.key] && errors[field.key] }"
          @blur="onBlur(field)"
        >
          <option value="" disabled>{{ state.language === 'en' ? 'Select…' : 'Seleccionar…' }}</option>
          <option v-for="opt in field.options" :key="opt" :value="opt">
            {{ optionLabel(field.key, opt) }}
          </option>
        </select>

        <input
          v-else
          :id="`field-${field.key}`"
          v-model="model[field.key]"
          type="number"
          inputmode="decimal"
          :min="field.min"
          :max="field.max"
          class="form__control"
          :class="{ 'form__control--error': touched[field.key] && errors[field.key] }"
          @blur="onBlur(field)"
        />

        <p
          v-if="touched[field.key] && errors[field.key]"
          class="form__error"
          role="alert"
        >
          {{ errorText(field.key) }}
        </p>
      </div>
    </div>

    <button type="submit" class="form__submit">
      <svg
        class="form__submit-icon"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          d="M12 3a7 7 0 0 0-7 7c0 4 4 6 7 7 3-1 7-3 7-7a7 7 0 0 0-7-7Z"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <path
          d="M12 10h.01M8.5 12h.01M15.5 12h.01M10 15h4"
          fill="none"
          stroke="currentColor"
          stroke-width="2.2"
          stroke-linecap="round"
        />
      </svg>
      {{ t('analyzeRisk') }}
    </button>
  </form>
</template>

<style scoped>
.form__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form__field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.form__label {
  font-size: 12.5px;
  font-weight: var(--w-600);
  color: var(--color-ink);
}

.form__control {
  width: 100%;
  border: 1px solid var(--color-hairline);
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  background: var(--color-card);
  color: var(--color-ink);
  transition: border-color var(--dur) var(--ease), box-shadow var(--dur) var(--ease);
  appearance: none;
}

.form__control:hover {
  border-color: rgba(23, 32, 51, 0.25);
}

:root[data-theme='dark'] .form__control:hover {
  border-color: rgba(244, 201, 93, 0.35);
}

.form__control:focus {
  outline: none;
  border-color: var(--color-accent-strong);
  box-shadow: 0 0 0 3px rgba(244, 201, 93, 0.18);
}

.form__control--error {
  border-color: var(--color-risk);
}

.form__control--error:focus {
  border-color: var(--color-risk);
  box-shadow: 0 0 0 3px rgba(192, 57, 43, 0.12);
}

.form__error {
  font-size: 12px;
  color: var(--color-risk);
}

.form__submit {
  margin-top: 24px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: none;
  background: var(--color-accent-strong);
  color: var(--color-on-accent);
  border-radius: 8px;
  padding: 12px 20px;
  font-size: 15px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  box-shadow: var(--shadow-sm);
  transition: background var(--dur) var(--ease), transform var(--dur) var(--ease),
    box-shadow var(--dur) var(--ease);
}

.form__submit-icon {
  width: 21px;
  height: 21px;
  color: var(--color-on-accent);
  filter: drop-shadow(0 0 4px rgba(244, 201, 93, 0.4));
}

.form__submit:hover {
  background: var(--color-accent-deep);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.form__submit:active {
  transform: translateY(0);
}

@media (max-width: 640px) {
  .form__grid {
    grid-template-columns: 1fr;
  }
  .form__submit {
    width: 100%;
  }
}
</style>