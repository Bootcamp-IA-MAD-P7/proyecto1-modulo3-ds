/**
 * Shared field definitions for the patient assessment form.
 *
 * The category options MUST match EXACTLY what the FastAPI backend accepts
 * (backend/main.py PredictionRequest). Do not add/rename categories here
 * without updating the backend too.
 */

export const FIELD_DEFINITIONS = [
  { key: 'gender', label: 'Gender', type: 'select', options: ['Male', 'Female'] },
  { key: 'age', label: 'Age', type: 'number', min: 0, max: 130 },
  {
    key: 'hypertension',
    label: 'Hypertension',
    type: 'select',
    options: ['0', '1'],
    asNumber: true,
  },
  {
    key: 'heart_disease',
    label: 'Heart disease',
    type: 'select',
    options: ['0', '1'],
    asNumber: true,
  },
  { key: 'ever_married', label: 'Ever married', type: 'select', options: ['Yes', 'No'] },
  {
    key: 'work_type',
    label: 'Work type',
    type: 'select',
    options: ['Govt_job', 'Private', 'Self-employed', 'children'],
  },
  {
    key: 'Residence_type',
    label: 'Residence',
    type: 'select',
    options: ['Rural', 'Urban'],
  },
  { key: 'avg_glucose_level', label: 'Avg glucose level', type: 'number', min: 0 },
  { key: 'bmi', label: 'BMI', type: 'number', min: 5, max: 100 },
  {
    key: 'smoking_status',
    label: 'Smoking status',
    type: 'select',
    options: ['never smoked', 'formerly smoked', 'smokes', 'Unknown'],
  },
]

/** Number fields with explicit ranges (input validation rules). */
export const NUMBER_RULES = {
  age: { min: 0, max: 130 },
  avg_glucose_level: { min: 0, max: Infinity },
  bmi: { min: 5, max: 100 },
}

/** Returns true when a form model value is ready to send for a given field. */
export function isEmptyValue(field, value) {
  if (value === null || value === undefined) return true
  const trimmed = typeof value === 'string' ? value.trim() : value
  return trimmed === ''
}