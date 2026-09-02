<script setup>
/**
 * Issue #033 - patient assessment form.
 *
 * Collects the 10 model features, validates them on the frontend (required,
 * ranges, exact categories), and only emits "submit" with a valid payload.
 */
import { reactive } from 'vue'
import { FIELD_DEFINITIONS, NUMBER_RULES, isEmptyValue } from './formFields.js'

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

function validateField(field) {
  const value = model[field.key]

  if (isEmptyValue(field, value)) {
    errors[field.key] = `${field.label} is required.`
    return
  }

  if (field.type === 'number') {
    const num = Number(value)
    if (Number.isNaN(num)) {
      errors[field.key] = `${field.label} must be a number.`
      return
    }
    const rule = NUMBER_RULES[field.key]
    if (rule) {
      if (num < rule.min) {
        errors[field.key] =
          rule.max !== Infinity
            ? `${field.label} must be between ${rule.min} and ${rule.max}.`
            : `${field.label} must be ${rule.min} or greater.`
        return
      }
      if (rule.max !== Infinity && num > rule.max) {
        errors[field.key] = `${field.label} must be between ${rule.min} and ${rule.max}.`
        return
      }
    }
  }

  // Select fields: value must be one of the allowed options.
  if (field.type === 'select' && field.options && !field.options.includes(value)) {
    errors[field.key] = `${field.label} has an invalid value.`
    return
  }

  delete errors[field.key]
}

function onBlur(field) {
  touched[field.key] = true
  validateField(field)
}

function onSubmit() {
  // Touch all fields so errors surface right away.
  fieldKeys.forEach((key) => {
    touched[key] = true
    const field = FIELD_DEFINITIONS.find((f) => f.key === key)
    validateField(field)
  })

  if (Object.keys(errors).length > 0) return

  const payload = {}
  for (const field of FIELD_DEFINITIONS) {
    // The binary 0|1 toggles and all number fields are sent as numbers so the
    // backend (Literal[0,1], age/glucose/bmi floats) validates them correctly.
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
          {{ field.label }}
        </label>

        <select
          v-if="field.type === 'select'"
          :id="`field-${field.key}`"
          v-model="model[field.key]"
          class="form__control"
          :class="{ 'form__control--error': touched[field.key] && errors[field.key] }"
          @blur="onBlur(field)"
        >
          <option value="" disabled>Select…</option>
          <option v-for="opt in field.options" :key="opt" :value="opt">
            {{ opt }}
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
          {{ errors[field.key] }}
        </p>
      </div>
    </div>

    <button type="submit" class="form__submit">Analizar riesgo</button>
  </form>
</template>

<style scoped>
.form__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.form__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form__label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
}

.form__control {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  font-size: 14px;
  background: var(--color-surface);
  color: var(--color-text);
  transition: border-color 0.15s ease;
}

.form__control:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15);
}

.form__control--error {
  border-color: var(--color-risk);
}

.form__error {
  font-size: 12px;
  color: var(--color-risk);
}

.form__submit {
  margin-top: 18px;
  width: 100%;
  border: none;
  background: var(--color-accent);
  color: #fff;
  border-radius: 12px;
  padding: 13px;
  font-size: 16px;
  font-weight: 650;
  transition: background 0.15s ease;
}

.form__submit:hover {
  background: var(--color-accent-dark);
}

/* Single column on narrow screens. */
@media (max-width: 640px) {
  .form__grid {
    grid-template-columns: 1fr;
  }
}
</style>