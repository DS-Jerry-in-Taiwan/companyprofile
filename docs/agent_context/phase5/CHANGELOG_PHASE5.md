# CHANGELOG - Phase 5 (最終測試、優化與交付)

## v0.1.0-phase4-mvp (2026-03-30)
- Feature: Risk control MVP (scanner, sanitizer, normalizer, audit logger, review queue)
- Tests: Added extended negative test suite and sample corpus
- Infra: Pushed to origin-private and created tag

## Phase 5 (completed items)
- Add performance & cost monitoring scripts
- Run 20+ sample batch testing and hallucination checks (30 samples, 28/30 passed)
- Harden sanitizer and integrate review queue persistence
- Finalize documentation and release

## Side Task: Real API Integration (2026-03-30)
### 背景
在 Phase 5 執行過程中，發現 `src/functions/utils/` 目錄下的模組仍使用 mock 實作，需要連接真實 API。

### 完成項目
| 項目 | 檔案 | 狀態 |
|------|------|------|
| LLM API | `src/functions/utils/llm_service.py` | ✅ 已連接 Gemini |
| Web Search API | `src/functions/utils/web_search.py` | ✅ 已連接 Serper |

### 技術細節
- LLM: 使用現有 `src/services/llm_service.py` 的 `LLMService` 類別
- Web Search: 使用現有 `src/services/serper_search.py` 的 `SerperSearchProvider`
- 支援 string 或 dict 輸入相容舊有介面

### 測試結果
- LLM API: ✅ 正常生成公司簡介
- Web Search API: ✅ 成功搜尋並返回真實 URL
- OPTIMIZE 模式測試: ✅ 成功優化公司簡介

---

## v0.1.0-phase5-mvp (2026-03-30)
- Feature: Performance monitoring scripts (perf_timer, token_cost_logger, batch_test, hallucination_checker, e2e_runner, perf_analysis)
- Feature: Real API integration (LLM + Web Search)
- Tests: 30 sample batch testing, 28/30 passed (2 demo flags)
- Docs: Release notes, final quality report, final test report
- Release: Ready for production deployment
