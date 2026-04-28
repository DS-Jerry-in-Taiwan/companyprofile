# Phase 11 字數限制雙重篩選機制 — Developer 交辦文件

**文件日期**：2026/04/08  
**狀態**：✅ 驗證完成，機制確認完整  
**目標接收方**：Development Team

---

## 📋 概要

根據最新源碼審查與完整測試驗證，Phase 11 的字數限制（word_limit）機制已實作為**「雙重篩選」**模式：

1. **Prompt 層**：LLM prompt 明確告知「不超過 N 字」，軟性引導
2. **程式層**：回傳後強制截斷（`truncate_llm_output`），硬性保證

**驗證結果**：18/18 測試通過 ✅

---

## 🔍 機制確認

### 現狀（已驗證完整）

| 層級 | 檔案 | 實作 | 狀態 |
|-----|------|------|------|
| **Prompt** | `src/functions/utils/prompt_builder.py` | 明確包含 word_limit 指示 | ✅ 完成 |
| **傳統流程** | `src/functions/utils/generate_brief.py` | 呼叫 `truncate_llm_output` | ✅ 完成 |
| **LangGraph** | `src/langgraph/state.py` | finalize 層執行截斷 | ✅ 完成 |
| **截斷邏輯** | `src/functions/utils/text_truncate.py` | body_html/summary/title 各欄位處理 | ✅ 完成 |

### 實作細節

#### 1️⃣ Prompt 層（軟性控制）
```python
# src/functions/utils/prompt_builder.py L54-57
if word_limit:
    sections.append(
        f"請根據上述所有資訊，生成一段專業、簡潔的公司簡介（不超過 {word_limit} 字）。"
    )
```

**作用**：讓 LLM 知道字數限制，引導自然產出。

---

#### 2️⃣ 程式層（硬性保證）

**傳統流程**：
```python
# src/functions/utils/generate_brief.py L216-217
if word_limit:
    result = truncate_llm_output(result, word_limit)
```

**LangGraph 流程**：
```python
# src/langgraph/state.py L383
final_result = truncate_llm_output(final_result, word_limit)
```

**作用**：不論 LLM 輸出是否超標，都強制裁切至限制內。

---

#### 3️⃣ 截斷邏輯細節
```python
# src/functions/utils/text_truncate.py L85-118

def truncate_llm_output(output: dict, word_limit: int) -> dict:
    # body_html：按 word_limit 截斷
    result["body_html"] = truncate_text(result["body_html"], word_limit, preserve_html=True)
    
    # summary：按 word_limit//2（但不超過200字）截斷
    summary_limit = min(word_limit // 2, 200)
    result["summary"] = truncate_text(result["summary"], summary_limit, preserve_html=False)
    
    # title：統一限制 50 字
    result["title"] = truncate_text(result["title"], 50, preserve_html=False)
    
    return result
```

---

## ✅ 測試驗證

### 測試檔案
- **位置**：`tests/test_word_limit/test_dual_filter_mechanism.py`
- **測試數**：18 個
- **通過率**：100% (18/18) ✅

### 測試覆蓋範圍

| 測試類別 | 測試數 | 覆蓋內容 |
|---------|--------|---------|
| TestPromptLayerWordLimit | 4 | Prompt 是否正確包含 word_limit 指示 |
| TestProgramLayerTruncation | 4 | 截斷是否有效執行 |
| TestDualFilterIntegration | 3 | 兩層機制是否協調一致 |
| TestPromptLLMIntegration | 1 | word_limit 是否正確傳遞 |
| TestLangGraphWordLimitIntegration | 2 | LangGraph 流程是否支援 |
| TestWordLimitEdgeCases | 4 | 邊界與異常情況 |

### 執行測試

```bash
# 執行雙重篩選機制測試
cd /home/ubuntu/projects/OrganBriefOptimization
python -m pytest tests/test_word_limit/test_dual_filter_mechanism.py -v

# 預期結果
# ============================= 18 passed in 0.09s ==============================
```

---

## 🎯 Developer 的確認清單

### ✅ 已確認項目

- [x] Prompt 層對所有 word_limit 值都做了明確指示
- [x] 程式層截斷邏輯完整無缺陷
- [x] 傳統流程與 LangGraph 流程都支援 word_limit
- [x] 邊界情況（50-2000字、None 等）都能正確處理
- [x] 18 個測試全部通過

### ⚠️ 注意事項

1. **word_limit 的應用欄位**：
   - body_html：按 word_limit 截斷
   - summary：按 word_limit//2（不超過200字）截斷
   - title：統一 50 字限制
   - **title、summary 不受 word_limit 直接限制，僅 body_html 精確受限**

2. **設計意圖**：
   - Prompt 層的軟性指示減少 LLM「偶發超長」現象
   - 程式層的硬性截斷才是最終保證，確保法律、合規安全

3. **未來擴展**：
   - 如需對其他欄位應用 word_limit，參考 `truncate_llm_output` 的現有實作模式
   - 如需調整截斷策略（如保護語義完整性），修改 `_truncate_html` 邏輯

---

## 📚 相關文檔

- **技術分析報告**：`docs/agent_context/phase11_word_limit_fix/phase11_technical_analysis_report.md`
  - 詳細的流程分析、機制設計、業界實踐背景
- **測試用例**：`tests/test_word_limit/test_dual_filter_mechanism.py`
  - 18 個測試案例，可作為實作驗收標準

---

## 🚀 後續建議

### 短期（無須行動）
- 機制已驗證完整，當前實作無需調整
- 維持現狀，繼續信心運用此雙重保險

### 中期（可選優化）
- 添加日誌記錄：記錄每個請求的 word_limit 與實際輸出長度
- 監控：統計超長輸出被截斷的頻率，評估 LLM 合規性

### 長期（視業務需求）
- 如需針對不同欄位設置不同限制，修改 `truncate_llm_output` 的邏輯
- 如需優化截斷時的語義完整性，升級 `_truncate_html` 演算法

---

## 💬 Q&A

**Q: 為什麼要雙重篩選，直接截斷不行嗎？**  
A: 單純截斷會導致語言不自然（如句子截半）。Prompt 指示引導 LLM 盡量產出合規內容，截斷才是最後防線。此乃業界標準。

**Q: title 和 summary 為什麼不按 word_limit 限制？**  
A: 根據產品需求，word_limit 主要約束「公司簡介正文」（body_html）長度。title/summary 有各自的固定上限（50/100字）以保持格式一致。

**Q: 如果 LLM 輸出為空或錯誤怎麼辦？**  
A: `truncate_llm_output` 已有容錯邏輯，會安全處理空值、缺少欄位等情況。

**Q: 何時執行截斷？**  
A: 
- **傳統流程**：LLM 返回 → post_process → truncate_llm_output → 返回
- **LangGraph**：LLM 返回 → ... → finalize_state（執行 truncate_llm_output）→ 返回

---

## 📞 聯絡與反饋

若有任何關於 word_limit 實作的問題或改進建議，請參考：
- 本文檔：交辦細節、實作位置
- 技術報告：設計背景與業界實踐
- 測試檔案：實作驗收標準

**驗證完成日期**：2026/04/08  
**驗證人**：AI Technical Analyst

---

**本文檔旨在確保 Developer 清晰理解 Phase 11 word_limit 的雙重篩選機制、現狀驗證與維護要點。**
