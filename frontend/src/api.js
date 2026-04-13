import axios from 'axios'

let API_BASE_URL = '/api/v1'

/**
 * Process company profile (GENERATE or OPTIMIZE)
 * @param {Object} data - Company profile data
 * @returns {Promise<Object>} - API response
 */

async function initializeApiUrl() {
  try {
    const response = await fetch('/api/config')
    const data = await response.json()
    API_BASE_URL = data.apiBaseUrl
  } catch (e) {
    console.warn('使用預設 API URL')
  }
}
initializeApiUrl()  // 頁面載入時自動執行

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
  if (data.mode === 'GENERATE') {
    // companyUrl is now optional - system will search using organ name
  }

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
