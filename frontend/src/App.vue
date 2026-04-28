<script setup>
import { ref } from 'vue'
import BriefForm from './components/BriefForm.vue'
import ResultPanel from './components/ResultPanel.vue'
import { processProfile } from './api'

const loading = ref(false)
const results = ref([])

async function handleSubmit(formData) {
  loading.value = true
  
  try {
    const response = await processProfile(formData)
    // 新增結果到陣列頂部（最新的在上面）
    results.value.unshift({
      id: Date.now(),
      success: true,
      data: response,
      timestamp: new Date().toLocaleString('zh-TW')
    })
  } catch (err) {
    // 錯誤也加入結果陣列
    let errorData
    if (err.response) {
      const resp = err.response.data
      // 解析 ErrorResponse 結構 { success: false, error: { code, message, details, trace_id } }
      const errorObj = resp?.error || {}
      errorData = {
        success: false,
        code: errorObj.code || resp?.error_code || 'API_ERROR',
        message: errorObj.message || resp?.message || `伺服器錯誤 (${err.response.status})`,
        details: errorObj.details || resp?.details || null,
        trace_id: errorObj.trace_id || null
      }
    } else if (err.request) {
      errorData = {
        success: false,
        code: 'NETWORK_ERROR',
        message: '無法連線到伺服器，請檢查網路連線',
        details: null
      }
    } else {
      errorData = {
        success: false,
        code: 'UNKNOWN_ERROR',
        message: err.message || '發生未知錯誤',
        details: null
      }
    }
    
    results.value.unshift({
      id: Date.now(),
      success: false,
      data: errorData,
      timestamp: new Date().toLocaleString('zh-TW')
    })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto py-3 px-4 sm:px-6 lg:px-8">
        <h1 class="text-xl font-bold text-gray-900">
          1111 人力銀行 - 公司簡介生成工具
        </h1>
      </div>
    </header>
    
    <!-- Main Content -->
    <main class="max-w-7xl mx-auto py-4 sm:px-6 lg:px-8">
      <div class="flex flex-col lg:flex-row gap-4">
        
        <!-- Left Panel: Form -->
        <div class="w-full lg:w-1/3 flex-shrink-0">
          <BriefForm :loading="loading" @submit="handleSubmit" />
        </div>

        <!-- Right Panel: Results History -->
        <div class="flex-1">
          <ResultPanel :results="results" :loading="loading" />
        </div>
        
      </div>
    </main>
    
    <!-- Footer -->
    <footer class="bg-white border-t border-gray-200 mt-auto">
      <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
        <p class="text-center text-sm text-gray-500">
          Organ Brief Optimization Tool &copy; 2026
        </p>
      </div>
    </footer>
  </div>
</template>
