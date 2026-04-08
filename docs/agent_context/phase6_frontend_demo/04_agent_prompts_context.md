# Phase 6 - Agent 執行 Prompt

**階段**: `phase6_frontend_demo`

---

## 💬 Agent Prompt 範例

### **@INFRA Prompt**
```
作為 @INFRA，請為「公司簡介生成前端 Demo」初始化前端專案。

參考文件：
- docs/agent_context/phase6_frontend_demo/01_dev_goal_context.md
- docs/agent_context/phase6_frontend_demo/02_dev_flow_context.md

任務包括：
1. 建立 frontend/ 目錄結構
2. 初始化 Vue 3 + Vite 專案（npm init vue@latest）
3. 安裝依賴：axios, tailwindcss
4. 配置 vite.config.js 的 API 代理：
   - proxy: http://127.0.0.1:5000/v1
5. 建立基本的 index.html 和 main.js

報告完成狀態。
```

---

### **@ARCH Prompt**
```
作為 @ARCH，請為「公司簡介生成前端 Demo」設計架構。

參考文件：
- docs/agent_context/phase6_frontend_demo/01_dev_goal_context.md
- docs/agent_context/phase6_frontend_demo/02_dev_flow_context.md
- docs/schedule_context/04_agent_prompts_context.md

現有 Input Schema：
- organNo (必填)
- organ (必填)
- mode (必填) - GENERATE / OPTIMIZE
- brief (OPTIMIZE 必填)
- companyUrl (GENERATE 必填)
- word_limit (選填, 50-2000)
- optimization_mode (選填, STANDARD/CONCISE/DETAILED)

新增欄位需求：
- brand_names (string[]) - 品牌名稱
- tax_id (string) - 統一編號
- capital (number) - 資本額
- employees (number) - 員工人數
- founded_year (number) - 成立年份
- address (string) - 公司地址
- industry (string) - 產業類別
- industry_desc (string) - 產業說明
- banned_words (string[]) - 違法/競品字眼

任務包括：
1. 更新 request_validator.py 支援新欄位
2. 設計前端表單結構（哪些欄位放在哪個區塊）
3. 定義 API 回傳格式（應包含哪些欄位）
4. 報告架構設計。
```

---

### **@CODER Prompt**
```
作為 @CODER，請根據 @ARCH 的設計，實作「公司簡介生成前端 Demo」。

參考文件：
- docs/agent_context/phase6_frontend_demo/01_dev_goal_context.md
- docs/agent_context/phase6_frontend_demo/02_dev_flow_context.md
- docs/api_schema_v2.md（由 @ARCH 產出）

任務包括：
1. 實作 BriefForm.vue：
   - 公司名稱（必填）
   - 機構編號（必填）
   - 模式選擇（GENERATE / OPTIMIZE）
   - 公司網址（GENERATE 時必填）
   - 現有簡介（OPTIMIZE 時必填）
   - 產業類別、資本額等新欄位
   
2. 實作 ResultPanel.vue：
   - 顯示 Title, Summary, Body
   - 支援 HTML 渲染
   
3. 實作 RiskAlert.vue：
   - 高風險字眼警示
   
4. 實作 api.js：
   - 呼叫 /v1/company/profile/process
   - 處理錯誤
   
5. 使用 Tailwind CSS 做樣式
6. 支援 RWD

報告完成的檔案清單。
```

---

### **@ANALYST Prompt**
```
作為 @ANALYST，請為「公司簡介生成前端 Demo」進行測試。

參考文件：
- docs/agent_context/phase6_frontend_demo/01_dev_goal_context.md
- docs/agent_context/phase6_frontend_demo/02_dev_flow_context.md

任務包括：
1. 功能測試：
   - GENERATE 模式：輸入公司名稱和網址，生成簡介
   - OPTIMIZE 模式：輸入公司名稱和現有簡介，優化簡介
   - 高風險字眼警示測試
   
2. 整合測試：
   - 前端與後端 API 整合
   - 錯誤處理測試
   
3. RWD 測試：
   - 桌面版 (1920x1080)
   - 平板版 (768x1024)
   - 手機版 (375x667)
   
4. 報告測試結果。
```
