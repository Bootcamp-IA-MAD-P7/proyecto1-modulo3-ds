/**
 * Shared fixtures for frontend tests.
 */
import { FIELD_DEFINITIONS } from '@/components/formFields.js'

/** A fully valid payload matching the backend schema. */
export const VALID_PAYLOAD = {
  gender: 'Female',
  age: 45,
  hypertension: 0,
  heart_disease: 1,
  ever_married: 'Yes',
  work_type: 'Private',
  Residence_type: 'Urban',
  avg_glucose_level: 100,
  bmi: 25,
  smoking_status: 'never smoked',
}

export const fieldKeys = () => FIELD_DEFINITIONS.map((f) => f.key)