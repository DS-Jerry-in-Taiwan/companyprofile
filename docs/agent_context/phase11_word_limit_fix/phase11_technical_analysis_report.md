# Phase11 字數限制修復 - 技術深度分析報告

## 一、技術架構分析

### 1.1 數據流程全景圖

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    用戶輸入                                          │
│                              word_limit: 50-2000                                    │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              前端表單層 (BriefForm.vue)                              │
│  - 輸入驗證 (50-2000)                                                               │
│  - 錯誤提示                                                                        │
│  - 通過 API 請求傳遞                                                               │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            API 驗證層 (request_validator.py)                         │
│  - 類型檢查 (int)                                                                  │
│  - 範圍檢查 (50-2000)                                                              │
│  - 返回錯誤 response                                                               │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          業務邏輯層 (generate_brief.py)                              │
│  - 提取 word_limit                                                                │
│  - 傳遞給下游模組                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
        ┌───────────────────┐                   ┌───────────────────┐
        │   LangGraph 流程   │                   │   傳統流程        │
        │ (未完成 - 待修復)  │                   │   (已完成)        │
        └───────────────────┘                   └───────────────────┘
                    │                               │
                    ▼                               ▼
        ┌───────────────────┐                   ┌───────────────────┐
        │ 需要添加           │                   │ Prompt Builder   │
        │ word_limit 支持   │                   │ (已完成)          │
        └───────────────────┘                   └───────────────────┘
                                                    │
                                                    ▼
                                        ┌───────────────────┐
                                        │   LLM 調用        │
                                        │ (call_llm)        │
                                        │ ⚠️ 未傳遞         │
                                        └───────────────────┘
                                                    │
                                                    ▼
                                        ┌───────────────────┐
                                        │ LLM Service       │
                                        │ (已完成)          │
                                        │ max_tokens 動態    │
                                        └───────────────────┘
                                                    │
                                                    ▼
                                        ┌───────────────────┐
                                        │   後處理截斷      │
                                        │ (text_truncate)   │
                                        │ (已完成)          │
                                        └───────────────────┘
                                                    │
                                                    ▼
                                        ┌───────────────────┐
                                        │   返回結果        │
                                        │ body_html ≤ limit│
                                        │ summary ≤ limit/2│
                                        │ title ≤ 50       │
                                        └───────────────────┘
```

### 1.2 關鍵模組職責分析

| 模組 | 檔案 | 輸入 | 輸出 | 當前狀態 |
|------|------|------|------|----------|
| API 驗證 | `request_validator.py` | data dict | bool, error_msg | ✅ 完成 |
| Prompt 建構 | `prompt_builder.py` | organ, word_limit等 | prompt string | ✅ 完成 |
| LLM Service | `llm_service.py` | prompt, word_limit | LLMOutput | ✅ 完成 |
| 字數截斷 | `text_truncate.py` | output dict, word_limit | truncated dict | ✅ 完成 |
| 中間層 | `llm_service.py` (utils) | prompt | dict | ❌ 待修復 |
| LangGraph | `company_brief_graph.py` | organ等 | result | ❌ 待修復 |

---

## 二、程式碼品質分析

### 2.1 程式碼變更清單

#### 2.1.1 新增檔案

| 檔案 | 用途 | 行數 | 依賴 |
|------|------|------|------|
| `src/functions/utils/text_truncate.py` | 字數截斷工具 | 118 | beautifulsoup4 |
| `tests/test_word_limit/test_truncation.py` | 單元測試 | 138 | pytest |

#### 2.1.2 修改檔案

| 檔案 | 修改類型 | 變更內容 |
|------|----------|----------|
| `src/functions/utils/prompt_builder.py` | 新增參數 | word_limit 參數 |
| `src/services/llm_service.py` | 新增參數 | word_limit 參數 + 動態 max_tokens |
| `src/functions/utils/generate_brief.py` | 新增邏輯 | 提取、傳遞、截斷 word_limit |
| `docs/agent_context/phase11_word_limit_fix/` | 新增文檔 | 4份開發文檔 |

### 2.2 依賴分析

#### 2.2.1 新增依賴

```python
# text_truncate.py
from bs4 import BeautifulSoup  # 現有依賴
import re                        # 標準庫
```

#### 2.2.2 函數簽名變更

**變更前**：
```python
def build_generate_prompt(
    organ, organ_no=None, company_url=None, user_brief=None, web_content=None
):
```

**變更後**：
```python
def build_generate_prompt(
    organ, organ_no=None, company_url=None, user_brief=None, web_content=None, word_limit=None
):
```

**變更前**：
```python
def generate(self, company_data: dict) -> LLMOutput:
```

**變更後**：
```python
def generate(self, company_data: dict, word_limit: int = None) -> LLMOutput:
```

### 2.3 錯誤處理分析

#### 2.3.1 已實現的錯誤處理

| 場景 | 處理方式 | 檔案 |
|------|----------|------|
| word_limit 非法類型 | 返回錯誤訊息 | request_validator.py |
| word_limit 範圍外 | 返回錯誤訊息 | request_validator.py |
| LLM 返回空回應 | 拋出 ValueError | llm_service.py |
| LLM 返回非 JSON | 拋出 ValueError | llm_service.py |
| 文本過長 | 自動截斷 | text_truncate.py |

#### 2.3.2 潛在錯誤場景

| 場景 | 風險等級 | 建議 |
|------|----------|------|
| HTML 標籤未閉合 | 中 | BeautifulSoup 可處理大部分情況 |
| LLM 生成超長內容 | 高 | 依賴後處理截斷 |
| LangGraph 流程中斷 | 高 | 需要添加 word_limit 支持 |

---

## 三、整合點分析

### 3.1 API 整合

#### 3.1.1 請求格式

```json
{
  "organ": "公司名稱",
  "word_limit": 100,
  "organNo": "12345678",
  "companyUrl": "https://example.com"
}
```

#### 3.1.2 回應格式

```json
{
  "title": "公司標題",
  "body_html": "<p>內容（不超過100字）</p>",
  "summary": "摘要（不超過50字）",
  "processing_mode": "traditional"
}
```

### 3.2 內部模組整合

#### 3.2.1 調用鏈

```
generate_brief(data)
    │
    ├─► data.get("word_limit")
    │
    ├─► _generate_brief_traditional(data)
    │       │
    │       ├─► build_generate_prompt(..., word_limit=word_limit)
    │       │
    │       ├─► call_llm(prompt) ⚠️ 需要傳遞 word_limit
    │       │
    │       └─► truncate_llm_output(result, word_limit)
    │
    └─► generate_company_brief(...) ❌ 未傳遞 word_limit
```

### 3.3 外部依賴

| 依賴 | 版本 | 用途 |
|------|------|------|
| beautifulsoup4 | 最新 | HTML 解析 |
| google-generativeai | 最新 | Gemini API |
| pytest | 最新 | 測試 |

---

## 四、性能考量

### 4.1 計算複雜度

| 操作 | 時間複雜度 | 說明 |
|------|------------|------|
| count_chinese_characters | O(n) | 遍歷文本長度 |
| truncate_text | O(n) | 取 substring |
| truncate_llm_output | O(n) | 調用 truncate_text 3次 |

### 4.2 效能優化

#### 4.2.1 已實現的優化

1. **提前返回**：如果文本長度 <= word_limit，直接返回，不進行處理
2. **智能斷句**：在合適的分隔符處截斷，保持語義完整性
3. **複製輸出**：使用 `.copy()` 避免修改原始輸出

#### 4.2.2 潛在優化點

1. **緩存計算**：如果相同 word_limit 多次調用，可以考慮緩存結果
2. **並行處理**：如果有多個欄位需要截斷，可以考慮並行處理
3. **HTML 解析優化**：BeautifulSoup 每次都重新解析，可以考慮優化

### 4.3 資源消耗

| 資源 | 消耗 | 預估 |
|------|------|------|
| 記憶體 | 低 | < 1MB |
| CPU | 低 | < 10ms/次 |
| 網路 | 中 | 取決於 LLM 調用 |

---

## 五、安全性分析

### 5.1 輸入驗證

✅ **已實現**：
- 類型檢查：確保 word_limit 為整數
- 範圍檢查：確保在 50-2000 之間

⚠️ **需要注意**：
- 負數檢查：雖然範圍檢查包含，但應更明確
- SQL 注入：目前無直接 SQL 操作，但仍需注意
- XSS：HTML 輸出有 sanitize，但仍需謹慎

### 5.2 輸出安全

| 輸出欄位 | 當前處理 | 建議 |
|----------|----------|------|
| body_html | BeautifulSoup + 截斷 | ✅ 安全 |
| summary | 純文本截斷 | ✅ 安全 |
| title | 純文本截斷 | ✅ 安全 |

### 5.3 API 安全

| 方面 | 狀態 | 說明 |
|------|------|------|
| 認證 | 取決於 API 層 | 未在 Phase11 範圍內 |
| 授權 | 取決於 API 層 | 未在 Phase11 範圍內 |
| 速率限制 | 未實現 | 建議後續添加 |
| 輸入驗證 | ✅ 已實現 | word_limit 驗證 |

---

## 六、測試覆蓋分析

### 6.1 現有測試

| 測試檔案 | 測試數 | 覆蓋範圍 |
|----------|--------|----------|
| test_truncation.py | 13 | 字數計算、文本截斷、LLM輸出截斷 |

### 6.2 缺失測試

| 測試類型 | 優先級 | 說明 |
|----------|--------|------|
| API 驗證測試 | 高 | 測試 request_validator.py |
| max_tokens 計算測試 | 高 | 測試公式正確性 |
| LangGraph 流程測試 | 中 | 測試 LangGraph 整合 |
| E2E 測試 | 高 | 完整流程測試 |
| 邊界測試 | 中 | 50, 2000, 50.5, "abc" 等 |

### 6.3 測試建議

```python
# 建議添加的測試案例

def test_word_limit_validation():
    # 合法邊界
    assert validate(50) == True
    assert validate(2000) == True
    
    # 非法邊界
    assert validate(49) == False
    assert validate(2001) == False
    
    # 非法類型
    assert validate("100") == False
    assert validate(100.5) == False
    assert validate(None) == True  # None 應該被允許（可選）

def test_max_tokens_calculation():
    assert calculate_max_tokens(50) == 100
    assert calculate_max_tokens(500) == 1000
    assert calculate_max_tokens(2000) == 4000
    assert calculate_max_tokens(3000) == 4096
```

---

## 七、建議與結論

### 7.1 短期建議（1-2天）

1. **修復中間層**：修改 `call_llm()` 函數，傳遞 word_limit
2. **修復 LangGraph**：在 `generate_company_brief()` 中傳遞 word_limit
3. **補充測試**：添加 API 驗證測試和 max_tokens 計算測試

### 7.2 中期建議（3-5天）

1. **E2E 測試**：編寫完整的端到端測試
2. **前端驗證**：確認前端正確傳遞 word_limit
3. **效能優化**：如有需要，優化截斷邏輯

### 7.3 長期建議

1. **監控**：添加 word_limit 超標監控
2. **日誌**：記錄每次請求的 word_limit 和實際輸出長度
3. **反饋**：根據實際使用數據調整參數

### 7.4 結論

Phase11 的字數限制功能已經完成了約 **70%** 的工作：

- ✅ **完成的**: Prompt 動態字數、LLM max_tokens 計算、後處理截斷、單元測試
- ⏳ **待完成**: 中間層整合、LangGraph 流程、完整 E2E 測試

剩餘工作難度不高，主要是確保數據在整個流程中正確傳遞。建議盡快完成剩餘項目，以便進入測試和驗收階段。

---

**報告人**：Technical Analyst  
**報告日期**：2024-04-10  
**版本**：v1.0
