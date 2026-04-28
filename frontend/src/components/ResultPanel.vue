<script setup>
import { ref, computed, nextTick, watch } from 'vue'

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

// 展開狀態: 最新的預設展開，其餘收起
const expandedIds = ref(new Set())

// 當有新結果加入時，展開最新的，收起所有舊的
watch(() => props.results.length, async (newLen, oldLen) => {
  if (newLen > oldLen) {
    const latestId = props.results[0]?.id
    if (latestId) {
      expandedIds.value = new Set([latestId])
    }
    await nextTick()
    window.scrollTo({
      top: document.body.scrollHeight,
      behavior: 'smooth'
    })
  }
})

function toggleExpand(id) {
  const next = new Set(expandedIds.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  expandedIds.value = next
}

function isExpanded(id) {
  return expandedIds.value.has(id)
}

const hasResults = computed(() => props.results && props.results.length > 0)
</script>

<template>
  <div class="space-y-3">

    <!-- Loading State -->
    <div v-if="loading && !hasResults" class="bg-white rounded-lg border border-gray-200 p-4">
      <div class="flex items-center justify-center h-16">
        <span class="text-gray-400">處理中...</span>
      </div>
    </div>

    <!-- No Results State -->
    <div v-else-if="!hasResults" class="bg-white rounded-lg border border-gray-200 p-4">
      <div class="h-16 flex items-center justify-center">
        <span class="text-gray-400">尚無結果，請輸入資料後點擊生成</span>
      </div>
    </div>

    <!-- Results List -->
    <div v-else class="space-y-2">

      <!-- Loading indicator on new submissions (在最上面) -->
      <div v-if="loading" class="bg-white rounded-lg border border-blue-200 p-3">
        <div class="flex items-center gap-2">
          <svg class="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span class="text-sm text-blue-600">處理中...</span>
        </div>
      </div>

      <div
        v-for="(result, index) in results"
        :key="result.id"
        class="bg-white rounded-lg border overflow-hidden"
        :class="[
          result.error_handled ? 'border-yellow-200' : (result.success ? 'border-green-200' : 'border-red-200'),
          index === 0 ? 'shadow-sm' : ''
        ]"
      >

        <!-- === Accordion Header (always visible) === -->
        <button
          class="w-full px-4 py-2.5 flex items-center gap-2 text-left cursor-pointer hover:opacity-80 transition-opacity"
          :class="[
            result.error_handled ? 'bg-yellow-50 hover:bg-yellow-100' : (result.success ? 'bg-green-50 hover:bg-green-100' : 'bg-red-50 hover:bg-red-100')
          ]"
          @click="toggleExpand(result.id)"
        >

          <!-- Expand/Collapse Arrow -->
          <span class="text-xs text-gray-400 w-3 flex-shrink-0 transition-transform"
            :class="isExpanded(result.id) ? 'rotate-90' : ''"
          >▶</span>

          <!-- Status Icon -->
          <span v-if="result.error_handled" class="text-yellow-600 flex-shrink-0">⚠</span>
          <span v-else-if="result.success" class="text-green-600 flex-shrink-0">✓</span>
          <span v-else class="text-red-600 flex-shrink-0">✕</span>

          <!-- Status Text -->
          <span
            class="text-sm font-medium flex-shrink-0"
            :class="result.error_handled ? 'text-yellow-800' : (result.success ? 'text-green-800' : 'text-red-800')"
          >{{ result.error_handled ? '部分成功' : (result.success ? '成功' : '失敗') }}</span>

          <!-- Result Code Badge -->
          <span
            class="px-1.5 py-0.5 rounded text-xs font-mono flex-shrink-0"
            :class="result.error_handled ? 'bg-yellow-100 text-yellow-700' : (result.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700')"
          >{{ result.error_handled ? (result.data.code || 'PARTIAL') : (result.success ? 'SUCCESS' : (result.data.code || 'ERROR')) }}</span>

          <!-- Optimization Mode Badge -->
          <span v-if="result.data.optimization_mode"
            class="px-1.5 py-0.5 rounded text-xs font-mono flex-shrink-0 bg-gray-100 text-gray-600 hidden sm:inline"
          >{{ result.data.optimization_mode }}</span>

          <!-- Organ Name -->
          <span class="text-sm text-gray-600 truncate min-w-0 flex-1 ml-1">
            {{ result.data.organ || result.data.organNo || '' }}
          </span>

          <!-- Timestamp -->
          <span class="text-xs text-gray-400 flex-shrink-0 whitespace-nowrap">{{ result.timestamp }}</span>
        </button>

        <!-- === Accordion Body (expanded only) === -->
        <div v-if="isExpanded(result.id)" class="border-t"
          :class="result.error_handled ? 'border-yellow-100' : (result.success ? 'border-green-100' : 'border-red-100')"
        >
          <div class="p-4">

            <!-- Error / Partial Error Message -->
            <div v-if="!result.success || result.error_handled" class="mb-4">
              <div
                class="p-3 rounded text-sm"
                :class="result.error_handled ? 'bg-yellow-50 border border-yellow-100 text-yellow-700' : 'bg-red-50 border border-red-100 text-red-700'"
              >
                <p class="font-medium">{{ result.data.message || result.data.error || (result.error_handled ? '部分內容可能不完整' : '處理失敗') }}</p>
                <p v-if="result.data.trace_id" class="text-xs mt-1 opacity-70">Trace ID: {{ result.data.trace_id }}</p>
                <div v-if="result.data.details" class="mt-2 pt-2 border-t"
                  :class="result.error_handled ? 'border-yellow-100' : 'border-red-100'"
                >
                  <pre class="text-xs mt-1 overflow-x-auto whitespace-pre-wrap"
                    :class="result.error_handled ? 'text-yellow-700' : 'text-red-600'"
                  >{{ result.data.details }}</pre>
                </div>
              </div>
            </div>

            <!-- Success Content -->
            <template v-if="result.success">
              <!-- Risk Alerts -->
              <div v-if="result.data.risk_alerts && result.data.risk_alerts.length > 0" class="mb-4 p-3 bg-orange-50 border border-orange-200 rounded text-sm">
                <p class="font-medium text-orange-800 mb-1">高風險字眼警示</p>
                <ul class="text-orange-700 list-disc list-inside">
                  <li v-for="alert in result.data.risk_alerts" :key="alert">{{ alert }}</li>
                </ul>
              </div>

              <!-- Title -->
              <div v-if="result.data.title" class="mb-3">
                <p class="text-xs text-gray-500 mb-0.5">標題</p>
                <p class="text-base font-semibold text-gray-900">{{ result.data.title }}</p>
              </div>

              <!-- Summary -->
              <div v-if="result.data.summary" class="mb-3">
                <p class="text-xs text-gray-500 mb-0.5">摘要</p>
                <div class="text-sm text-gray-700 bg-gray-50 p-3 rounded border border-gray-100">
                  {{ result.data.summary }}
                </div>
              </div>

              <!-- Body HTML -->
              <div v-if="result.data.body_html" class="mb-3">
                <p class="text-xs text-gray-500 mb-0.5">公司簡介</p>
                <div class="prose prose-blue max-w-none text-sm p-3 rounded border border-gray-100"
                  v-html="result.data.body_html"
                ></div>
              </div>

              <!-- Tags -->
              <div v-if="result.data.tags && result.data.tags.length > 0" class="mb-3">
                <div class="flex flex-wrap gap-1.5">
                  <span v-for="tag in result.data.tags" :key="tag"
                    class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-800"
                  >{{ tag }}</span>
                </div>
              </div>

              <!-- Metadata -->
              <div class="border-t border-gray-200 pt-3 mt-3">
                <div class="flex flex-wrap justify-between gap-x-4 gap-y-1 text-xs text-gray-500">
                  <div v-if="result.data.trace_id" class="truncate">Trace ID：{{ result.data.trace_id }}</div>
                  <div v-if="result.data.mode">模式：{{ result.data.mode }}</div>
                  <div>狀態：
                    <span :class="result.error_handled ? 'text-yellow-600' : 'text-green-600'">
                      {{ result.error_handled ? '部分成功' : '成功' }}
                    </span>
                  </div>
                </div>
              </div>
            </template>

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
