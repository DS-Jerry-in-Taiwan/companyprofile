import axios from 'axios'

// 開發環境使用 Vite proxy (/api → Flask 5000)
// 正式環境透過 .env.production 設定 VITE_API_BASE_URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

/**
 * Process company profile (GENERATE or OPTIMIZE)
 * @param {Object} data - Company profile data
 * @returns {Promise<Object>} - API response
 */
export async function processProfile(data) {
  const response = await axios.post(`${API_BASE_URL}/company/profile/process`, data, {
    headers: {
      'Content-Type': 'application/json'
    }
  })
  return response.data
}

/**
 * Validate form data before submission
 * @param {Object} data - Form data
 * @returns {Object} - { valid: boolean, errors: string[] }
 */
export function validateFormData(data) {
  const errors = []

  // Required fields
  if (!data.organNo?.trim()) {
    errors.push('機構編號為必填欄位')
  }
  if (!data.organ?.trim()) {
    errors.push('機構名稱為必填欄位')
  }
  if (!data.mode) {
    errors.push('請選擇模式（GENERATE 或 OPTIMIZE）')
  }

  // Mode-specific validation
  if (data.mode === 'OPTIMIZE') {
    if (!data.brief?.trim()) {
      errors.push('OPTIMIZE 模式下現有簡介為必填')
    }
  }

  return {
    valid: errors.length === 0,
    errors
  }
}
