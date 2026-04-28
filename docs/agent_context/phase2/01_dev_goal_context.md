# Phase 2 - 開發目標與需求 (Dev Goal Context)

**階段**: Phase 2 - 數據檢索與前處理模組 (RAG Foundation)
**目的**: 建立穩定的外部資料來源，為 AI 提供高品質的公司資訊背景。

## 🎯 開發目標
- 整合 **Serper.dev** 或 **Google Search API**，實作關鍵字搜尋與結果過濾。
- 實作 **Scraper Service** (使用 BeautifulSoup/Playwright)，自動抓取公司官網、新聞等內容。
- 開發 **Content Cleaning Pipeline**，移除 HTML 標籤、廣告文字與冗餘空白，保留核心文字。
- 實作 **Text Truncation**，確保資料量符合 LLM Token 限制 (約 2000-4000 tokens)。

## 📋 功能需求概要
1. **搜尋模組**: 根據 `company_name` 搜尋前 3-5 筆相關網頁 URL。
2. **抓取模組**: 針對 URL 提取網頁主體內容。
3. **清洗模組**: 將內容轉換為純文字，並進行格式標準化。
4. **降級機制 (Fallback)**: 若搜尋結果不佳，僅抓取廠商提供的 `reference_url`。

## ✅ 驗收標準 (Acceptance Criteria)
- 產出 `src/services/search_service.py` 且通過 Mock 測試。
- 產出 `src/services/scraper_service.py` 且成功提取指定 URL 的主體文字。
- 清洗後的資料不含 HTML 標籤與無關腳本。
- 完成搜尋到清洗的端到端 (E2E) 流程測試。
