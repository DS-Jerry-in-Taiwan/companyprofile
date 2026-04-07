<script setup>
import { ref } from 'vue'
import BriefForm from './components/BriefForm.vue'
import ResultPanel from './components/ResultPanel.vue'
import { processProfile } from './api'

const loading = ref(false)
const result = ref(null)
const error = ref(null)

async function handleSubmit(formData) {
  loading.value = true
  error.value = null
  result.value = null
  
  try {
    const response = await processProfile(formData)
    result.value = response
  } catch (err) {
    // Handle error response
    if (err.response) {
      result.value = {
        success: false,
        error: err.response.data?.error || err.response.data?.message || `伺服器錯誤 (${err.response.status})`
      }
    } else if (err.request) {
      result.value = {
        success: false,
        error: '無法連線到伺服器，請檢查網路連線'
      }
    } else {
      result.value = {
        success: false,
        error: err.message || '發生未知錯誤'
      }
    }
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
      <div class="flex flex-col gap-4">

        <!-- Form Panel (上方) -->
        <div>
          <BriefForm :loading="loading" @submit="handleSubmit" />
        </div>

        <!-- Result Panel (下方) -->
        <div>
          <ResultPanel :result="result" :loading="loading" />
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
