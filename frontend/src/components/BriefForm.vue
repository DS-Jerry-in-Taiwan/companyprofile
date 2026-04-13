<script setup>
import { ref } from 'vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['submit'])

const form = ref({
  // Required fields
  organNo: '',
  organ: '',
  
  // Brief field
  brief: '',
  
  // New optional fields
  brand_names: '',
  tax_id: '',
  capital: '',
  employees: '',
  founded_year: '',
  address: '',
  industry: '',
  industry_desc: '',
  
  // Optional settings
  optimization_mode: 'STANDARD'
})

const errors = ref([])

function validateForm() {
  errors.value = []
  
  if (!form.value.organNo?.trim()) {
    errors.value.push('機構編號為必填')
  }
  if (!form.value.organ?.trim()) {
    errors.value.push('機構名稱為必填')
  }
  
  // Validate numeric optional fields
  if (form.value.capital) {
    const capitalStr = String(form.value.capital).trim()
    if (capitalStr) {
      const val = parseInt(capitalStr)
      if (isNaN(val) || val <= 0) {
        errors.value.push('資本額必須為正數')
      }
    }
  }
  
  if (form.value.employees) {
    const employeesStr = String(form.value.employees).trim()
    if (employeesStr) {
      const val = parseInt(employeesStr)
      if (isNaN(val) || val <= 0) {
        errors.value.push('員工人數必須為正數')
      }
    }
  }
  
  if (form.value.founded_year) {
    const foundedYearStr = String(form.value.founded_year).trim()
    if (foundedYearStr) {
      const val = parseInt(foundedYearStr)
      if (isNaN(val) || val < 1900 || val > 2100) {
        errors.value.push('成立年份必須在 1900-2100 之間')
      }
    }
  }
  
  return errors.value.length === 0
}

function handleSubmit() {
  if (!validateForm()) {
    return
  }
  
  // Prepare data for API
  const submitData = {
    organNo: form.value.organNo.trim(),
    organ: form.value.organ.trim(),
    mode: 'GENERATE',
    optimization_mode: form.value.optimization_mode
  }
  
  // Brief (optional)
  if (form.value.brief?.trim()) {
    submitData.brief = form.value.brief.trim()
  }
  
  // Optional fields (only include if filled)
  if (form.value.brand_names?.trim()) {
    submitData.brand_names = form.value.brand_names.split(',').map(s => s.trim()).filter(s => s)
  }
  if (form.value.tax_id?.trim()) {
    submitData.tax_id = form.value.tax_id.trim()
  }
  
  // Numeric fields - convert to string first before trim
  if (form.value.capital) {
    const capitalStr = String(form.value.capital).trim()
    if (capitalStr) {
      const capitalValue = parseInt(capitalStr)
      if (!isNaN(capitalValue) && capitalValue > 0) {
        submitData.capital = capitalValue
      }
    }
  }
  
  if (form.value.employees) {
    const employeesStr = String(form.value.employees).trim()
    if (employeesStr) {
      const employeesValue = parseInt(employeesStr)
      if (!isNaN(employeesValue) && employeesValue > 0) {
        submitData.employees = employeesValue
      }
    }
  }
  
  if (form.value.founded_year) {
    const foundedYearStr = String(form.value.founded_year).trim()
    if (foundedYearStr) {
      const foundedYearValue = parseInt(foundedYearStr)
      if (!isNaN(foundedYearValue) && foundedYearValue >= 1900 && foundedYearValue <= 2100) {
        submitData.founded_year = foundedYearValue
      }
    }
  }
  
  if (form.value.address?.trim()) {
    submitData.address = form.value.address.trim()
  }
  if (form.value.industry?.trim()) {
    submitData.industry = form.value.industry.trim()
  }
  if (form.value.industry_desc?.trim()) {
    submitData.industry_desc = form.value.industry_desc.trim()
  }
  
  emit('submit', submitData)
}
</script>

<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200">
    <div class="p-4">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">公司資料輸入</h2>
      
      <!-- Error Messages -->
      <div v-if="errors.length > 0" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
        <ul class="list-disc list-inside text-red-700">
          <li v-for="error in errors" :key="error">{{ error }}</li>
        </ul>
      </div>
      
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Required Fields -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label for="organNo" class="block text-sm font-medium text-gray-700 mb-1">
              機構編號 <span class="text-red-500">*</span>
            </label>
            <input
              id="organNo"
              v-model="form.organNo"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="例如：69188618"
            />
          </div>
          
          <div>
            <label for="organ" class="block text-sm font-medium text-gray-700 mb-1">
              機構名稱 <span class="text-red-500">*</span>
            </label>
            <input
              id="organ"
              v-model="form.organ"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="例如：私立揚才文理短期補習班"
            />
          </div>
        </div>
        
        <!-- Brief Field -->
        <div>
          <label for="brief" class="block text-sm font-medium text-gray-700 mb-1">
            現有簡介
          </label>
          <textarea
            id="brief"
            v-model="form.brief"
            rows="5"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="若有現有簡介可貼上，系統將參考優化..."
          ></textarea>
          <p class="mt-1 text-xs text-gray-500">選填，提供現有簡介有助於生成更符合需求的內容</p>
        </div>
        
        <!-- New Optional Fields -->
        <div class="border-t border-gray-200 pt-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">選填資訊</h3>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Brand Names -->
            <div>
              <label for="brand_names" class="block text-sm font-medium text-gray-700 mb-1">
                品牌名稱
              </label>
              <input
                id="brand_names"
                v-model="form.brand_names"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="多筆用逗號分隔，例如：品牌A, 品牌B"
              />
              <p class="mt-1 text-xs text-gray-500">多筆用逗號分隔</p>
            </div>
            
            <!-- Tax ID -->
            <div>
              <label for="tax_id" class="block text-sm font-medium text-gray-700 mb-1">
                統一編號
              </label>
              <input
                id="tax_id"
                v-model="form.tax_id"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="例如：12345678"
              />
            </div>
            
            <!-- Capital -->
            <div>
              <label for="capital" class="block text-sm font-medium text-gray-700 mb-1">
                資本額（萬元）
              </label>
              <input
                id="capital"
                v-model="form.capital"
                type="number"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="例如：1000"
              />
            </div>
            
            <!-- Employees -->
            <div>
              <label for="employees" class="block text-sm font-medium text-gray-700 mb-1">
                員工人數
              </label>
              <input
                id="employees"
                v-model="form.employees"
                type="number"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="例如：50"
              />
            </div>
            
            <!-- Founded Year -->
            <div>
              <label for="founded_year" class="block text-sm font-medium text-gray-700 mb-1">
                成立年份
              </label>
              <input
                id="founded_year"
                v-model="form.founded_year"
                type="number"
                min="1900"
                max="2100"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="例如：2010"
              />
            </div>
            
            <!-- Industry -->
            <div>
              <label for="industry" class="block text-sm font-medium text-gray-700 mb-1">
                產業類別
              </label>
              <input
                id="industry"
                v-model="form.industry"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="例如：資訊服務業"
              />
            </div>
            
            <!-- Address -->
            <div class="md:col-span-2">
              <label for="address" class="block text-sm font-medium text-gray-700 mb-1">
                公司地址
              </label>
              <input
                id="address"
                v-model="form.address"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="例如：台北市信義區..."
              />
            </div>
            
            <!-- Industry Description -->
            <div class="md:col-span-2">
              <label for="industry_desc" class="block text-sm font-medium text-gray-700 mb-1">
                產業說明
              </label>
              <textarea
                id="industry_desc"
                v-model="form.industry_desc"
                rows="3"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="描述公司所屬產業的特點..."
              ></textarea>
            </div>
          </div>
        </div>
        
        <!-- Optional Settings -->
        <div class="border-t border-gray-200 pt-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">進階設定（選填）</h3>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Optimization Mode -->
            <div>
              <label for="optimization_mode" class="block text-sm font-medium text-gray-700 mb-1">
                優化模式
              </label>
              <select
                id="optimization_mode"
                v-model="form.optimization_mode"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="STANDARD">STANDARD（標準）</option>
                <option value="CONCISE">CONCISE（精簡）</option>
                <option value="DETAILED">DETAILED（詳細）</option>
              </select>
            </div>
          </div>
        </div>
        
        <!-- Submit Button -->
        <div class="pt-4">
          <button
            type="submit"
            :disabled="loading"
            class="w-full md:w-auto px-6 py-3 bg-blue-600 text-white font-medium rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <span v-if="loading" class="flex items-center">
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              處理中...
            </span>
            <span v-else>生成簡介</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
