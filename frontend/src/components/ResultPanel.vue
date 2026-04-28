<script setup>
import { computed, nextTick, watch } from 'vue'

const props = defineProps({
  results: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

// 監聽結果變化，自動滾動到最新結果
watch(() => props.results.length, async () => {
  await nextTick()
  window.scrollTo({
    top: document.body.scrollHeight,
    behavior: 'smooth'
  })
})

const hasResults = computed(() => props.results && props.results.length > 0)
</script>

<template>
  <div class="space-y-4">
    
    <!-- Loading State -->
    <div v-if="loading" class="bg-white rounded-lg border border-gray-200 p-4">
      <div class="flex items-center justify-center h-32">
        <span class="text-gray-400">處理中...</span>
      </div>
    </div>
    
    <!-- No Results State -->
    <div v-else-if="!hasResults" class="bg-white rounded-lg border border-gray-200 p-4">
      <div class="h-32 flex items-center justify-center">
        <span class="text-gray-400">尚無結果，請輸入資料後點擊生成</span>
      </div>
    </div>
    
    <!-- Results List -->
    <div v-else>
      <div 
        v-for="result in results" 
        :key="result.id"
        class="bg-white rounded-lg border mb-4"
        :class="result.success ? 'border-green-200' : 'border-red-200'"
      >
        
        <!-- Result Header -->
        <div 
          class="px-4 py-2 rounded-t-lg flex items-center justify-between"
          :class="result.success ? 'bg-green-50' : 'bg-red-50'"
        >
          <div class="flex items-center gap-2">
            <!-- Status Icon -->
            <span v-if="result.success" class="text-green-600">✓</span>
            <span v-else class="text-red-600">✕</span>
            
            <!-- Status Text -->
            <span :class="result.success ? 'text-green-800' : 'text-red-800'" class="font-medium">
              {{ result.success ? '成功' : '失敗' }}
            </span>
            
            <!-- Result Code -->
            <span 
              class="px-2 py-0.5 rounded text-xs font-mono"
              :class="result.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
            >
              {{ result.success ? 'SUCCESS' : (result.data.code || 'ERROR') }}
            </span>
          </div>
          
          <!-- Timestamp -->
          <span class="text-xs text-gray-500">{{ result.timestamp }}</span>
        </div>
        
        <!-- Result Body -->
        <div class="p-4">
          
          <!-- Error Details -->
          <div v-if="!result.success" class="mb-4">
            <div class="p-3 bg-red-50 border border-red-100 rounded">
              <p class="text-red-700 font-medium mb-2">{{ result.data.message }}</p>
              
              <!-- Trace ID (if available) -->
              <p v-if="result.data.trace_id" class="text-xs text-red-500 mb-2">Trace ID: {{ result.data.trace_id }}</p>
              
              <!-- Error Details (if available) -->
              <div v-if="result.data.details" class="mt-2 pt-2 border-t border-red-100">
                <p class="text-sm text-red-600 mb-1">錯誤細節：</p>
                <pre class="text-xs text-red-600 bg-red-100 p-2 rounded overflow-x-auto">{{ result.data.details }}</pre>
              </div>
            </div>
          </div>
          
          <!-- Success Result -->
          <div v-else-if="result.success">
            <!-- Risk Alerts -->
            <div v-if="result.data.risk_alerts && result.data.risk_alerts.length > 0" class="mb-4 p-3 bg-orange-50 border border-orange-200 rounded">
              <h3 class="text-sm font-medium text-orange-800 mb-2">高風險字眼警示</h3>
              <ul class="text-sm text-orange-700 list-disc list-inside">
                <li v-for="alert in result.data.risk_alerts" :key="alert">{{ alert }}</li>
              </ul>
            </div>
            
            <!-- Title -->
            <div v-if="result.data.title" class="mb-4">
              <h3 class="text-sm text-gray-500 mb-1">標題</h3>
              <div class="text-lg font-semibold text-gray-900">{{ result.data.title }}</div>
            </div>
            
            <!-- Summary -->
            <div v-if="result.data.summary" class="mb-4">
              <h3 class="text-sm text-gray-500 mb-1">摘要</h3>
              <div class="text-gray-700 bg-gray-50 p-3 rounded border border-gray-100">
                {{ result.data.summary }}
              </div>
            </div>
            
            <!-- Body HTML -->
            <div v-if="result.data.body_html" class="mb-4">
              <h3 class="text-sm text-gray-500 mb-1">公司簡介</h3>
              <div 
                class="prose prose-blue max-w-none p-3 rounded border border-gray-100"
                v-html="result.data.body_html"
              ></div>
            </div>
            
            <!-- Tags -->
            <div v-if="result.data.tags && result.data.tags.length > 0" class="mb-4">
              <h3 class="text-sm text-gray-500 mb-1">標籤</h3>
              <div class="flex flex-wrap gap-2">
                <span 
                  v-for="tag in result.data.tags" 
                  :key="tag"
                  class="inline-flex items-center px-2 py-1 rounded text-sm bg-blue-100 text-blue-800"
                >
                  {{ tag }}
                </span>
              </div>
            </div>
            
            <!-- Metadata -->
            <div class="border-t border-gray-200 pt-3 mt-4">
              <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                <div>
                  <span class="text-gray-500">機構編號：</span>
                  <span class="text-gray-900">{{ result.data.organNo }}</span>
                </div>
                <div>
                  <span class="text-gray-500">機構名稱：</span>
                  <span class="text-gray-900">{{ result.data.organ }}</span>
                </div>
                <div>
                  <span class="text-gray-500">模式：</span>
                  <span class="text-gray-900">{{ result.data.mode }}</span>
                </div>
                <div>
                  <span class="text-gray-500">狀態：</span>
                  <span class="text-green-600">成功</span>
                </div>
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </div>
    
  </div>
</template>

<style scoped>
.prose :deep(h1),
.prose :deep(h2),
.prose :deep(h3),
.prose :deep(h4) {
  color: #1f2937;
  font-weight: 600;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

.prose :deep(p) {
  margin-bottom: 1em;
  line-height: 1.75;
}

.prose :deep(ul),
.prose :deep(ol) {
  margin-left: 1.5em;
  margin-bottom: 1em;
}

.prose :deep(li) {
  margin-bottom: 0.25em;
}
</style>
