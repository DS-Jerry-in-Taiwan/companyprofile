<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const hasResult = computed(() => props.result && props.result.success)
const hasError = computed(() => props.result && !props.result.success)
const hasRiskAlerts = computed(() => props.result?.risk_alerts && props.result.risk_alerts.length > 0)
</script>

<template>
  <!-- 結果方框 -->
  <div class="bg-white rounded-lg border border-gray-200 min-h-[200px] p-4">
    
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center h-full min-h-[180px]">
      <span class="text-gray-400">處理中...</span>
    </div>
    
    <!-- No Result State (空白) -->
    <div v-else-if="!result" class="h-full min-h-[180px]">
      <!-- 空白，不顯示任何內容 -->
    </div>
    
    <!-- Error State -->
    <div v-else-if="hasError" class="text-red-600">
      <p>處理失敗：{{ result.error || result.message || '發生未知錯誤' }}</p>
    </div>
    
    <!-- Success Result -->
    <div v-else-if="hasResult">
      
      <!-- Risk Alerts -->
      <div v-if="hasRiskAlerts" class="mb-4 p-3 bg-orange-50 border border-orange-200 rounded">
        <h3 class="text-sm font-medium text-orange-800 mb-2">高風險字眼警示</h3>
        <ul class="text-sm text-orange-700 list-disc list-inside">
          <li v-for="alert in result.risk_alerts" :key="alert">{{ alert }}</li>
        </ul>
      </div>
      
      <!-- Title -->
      <div v-if="result.title" class="mb-4">
        <h3 class="text-sm text-gray-500 mb-1">標題</h3>
        <div class="text-lg font-semibold text-gray-900">{{ result.title }}</div>
      </div>
      
      <!-- Summary -->
      <div v-if="result.summary" class="mb-4">
        <h3 class="text-sm text-gray-500 mb-1">摘要</h3>
        <div class="text-gray-700 bg-gray-50 p-3 rounded border border-gray-100">
          {{ result.summary }}
        </div>
      </div>
      
      <!-- Body HTML -->
      <div v-if="result.body_html" class="mb-4">
        <h3 class="text-sm text-gray-500 mb-1">公司簡介</h3>
        <div 
          class="prose prose-blue max-w-none p-3 rounded border border-gray-100"
          v-html="result.body_html"
        ></div>
      </div>
      
      <!-- Tags -->
      <div v-if="result.tags && result.tags.length > 0" class="mb-4">
        <h3 class="text-sm text-gray-500 mb-1">標籤</h3>
        <div class="flex flex-wrap gap-2">
          <span 
            v-for="tag in result.tags" 
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
            <span class="text-gray-900">{{ result.organNo }}</span>
          </div>
          <div>
            <span class="text-gray-500">機構名稱：</span>
            <span class="text-gray-900">{{ result.organ }}</span>
          </div>
          <div>
            <span class="text-gray-500">模式：</span>
            <span class="text-gray-900">{{ result.mode }}</span>
          </div>
          <div v-if="result.success !== undefined">
            <span class="text-gray-500">狀態：</span>
            <span class="text-green-600">成功</span>
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
