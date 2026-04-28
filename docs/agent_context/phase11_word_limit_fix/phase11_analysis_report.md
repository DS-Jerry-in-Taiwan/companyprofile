# Phase11 字數限制修復 - 現況分析報告

## 一、執行摘要

本報告旨在盤點 Phase11「字數限制全鏈路修復」任務的當前進展情況。經過程式碼實際檢視,發現部分功能已在早期實作,但仍有關鍵模組尚未完成動態字數限制的完整實現。本報告將詳細說明各模組的現況、待完成事項,以及後續的測試驗證方案。

## 二、程式碼現況盤點

### 2.1 已完成模組

#### 2.1.1 後端 API 驗證 (request_validator.py)

**檔案位置**：`src/functions/utils/request_validator.py`

**程式碼現況**：
```python
word_limit = data.get("word_limit")
if word_limit is not None:
    if not isinstance(word_limit, int) or word_limit < 50 or word_limit > 2000:
        return False, "word_limit must be an integer between 50 and 2000",
            details=[{"field": "word_limit", "reason": "out of range"}],
```

**狀態**：✅ 已完成
- 驗證邏輯正確：檢查是否為整數、範圍是否在 50-2000 之間
- 錯誤訊息清晰

#### 2.1.2 優化模式 Prompt 建構 (llm_handler.py)

**檔案位置**：`src/functions/utils/llm_handler.py`

**程式碼現況**：
```python
def _build_optimization_prompt(self, organ, brief, products, mode, trade=None, word_limit=None):
    # ...
    if word_limit:
        prompt += f"5. 字數限制: 不超過{word_limit}字\n"
```

**狀態**：✅ 已完成
- optimize 模式下已動態帶入 word_limit

### 2.2 未完成模組

#### 2.2.1 生成模式 Prompt 建構 (prompt_builder.py)

**檔案位置**：`src/functions/utils/prompt_builder.py`

**問題**：generate 模式（首次生成公司簡介）尚未將 word_limit 動態帶入 prompt

**預期行為**：prompt 中應包含類似「請生成不超過 {word_limit} 字」的字樣

**狀態**：❌ 待完成

#### 2.2.2 LLM 服務 max_output_tokens 設定 (llm_service.py)

**檔案位置**：`src/services/llm_service.py`

**程式碼現況**：
```python
config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=4096)
```

**問題**：max_output_tokens 固定為 4096，未根據 word_limit 動態計算

**預期行為**：max_output_tokens = min(word_limit * 2, 4096)

**狀態**：❌ 待完成

#### 2.2.3 結果後處理截斷 (generate_brief.py)

**檔案位置**：`src/functions/utils/generate_brief.py`

**問題**：LLM 回傳後，無後處理邏輯對過長內容進行截斷

**預期行為**：對 body_html、summary 等欄位進行中文字數檢查，超過 word_limit 時自動截斷

**狀態**：❌ 待完成

## 三、待完成事項清單

| 序號 | 模組 | 檔案 | 具體任務 | 優先級 |
|------|------|------|----------|--------|
| 1 | Prompt 建構 | prompt_builder.py | generate 模式加入 word_limit 動態帶入 | P0 |
| 2 | LLM 服務 | llm_service.py | 根據 word_limit 計算 max_output_tokens | P0 |
| 3 | 結果後處理 | generate_brief.py | 新增字數截斷函數並在回傳前調用 | P0 |
| 4 | 前端傳遞 | BriefForm.vue | 確認 word_limit 正確傳遞給 API | P1 |
| 5 | 測試編寫 | tests/ | 單元測試 + E2E 測試 | P1 |

## 四、測試方案

### 4.1 單元測試（pytest）

#### 4.1.1 API 驗證測試

測試 request_validator.py 的 word_limit 驗證邏輯：
- 合法邊界值：50、2000
- 非法邊界值：49、2001、0、負數
- 非法類型：字串、浮點數、null、陣列

```python
def test_word_limit_validation():
    # 合法範圍內
    assert validate_word_limit(50) == True
    assert validate_word_limit(2000) == True
    
    # 非法範圍
    assert validate_word_limit(49) == False
    assert validate_word_limit(2001) == False
    
    # 非法類型
    assert validate_word_limit("100") == False
    assert validate_word_limit(100.5) == False
```

#### 4.1.2 max_output_tokens 計算測試

測試公式：max_output_tokens = min(word_limit * 2, 4096)

```python
def test_max_output_tokens_calculation():
    assert calculate_max_tokens(50) == 100      # 50 * 2 = 100
    assert calculate_max_tokens(500) == 1000    # 500 * 2 = 1000
    assert calculate_max_tokens(2000) == 4000   # 2000 * 2 = 4000 < 4096
    assert calculate_max_tokens(3000) == 4096   # 3000 * 2 = 6000 > 4096
```

#### 4.1.3 字數截斷測試

測試中文字數截斷函數：
- 正常截斷場景
- 邊界情況（剛好等於限制）
- HTML 標籤處理

```python
def test_chinese_text_truncation():
    text = "這是一段很長的文字，需要被截斷"
    result = truncate_chinese_text(text, 10)
    assert len(result) <= 10
    
    # 含 HTML 標籤的情況
    html_text = "<p>這是一段很長的文字，需要被截斷</p>"
    result = truncate_chinese_text(html_text, 10)
    assert len(remove_tags(result)) <= 10
```

### 4.2 整合測試

#### 4.2.1 API 端到端測試

使用 requests 或 curl 進行測試：

```bash
# 測試案例 1：word_limit = 100
curl -X POST http://localhost:5000/v1/company/profile/process \
  -H "Content-Type: application/json" \
  -d '{"organ":"測試公司","word_limit":100}'

# 驗證回傳內容長度不超過 100 字
```

### 4.3 測試資料夾建議

```
tests/
├── test_word_limit/
│   ├── __init__.py
│   ├── test_validator.py          # API 驗證測試
│   ├── test_max_tokens.py         # max_output_tokens 計算測試
│   ├── test_truncation.py         # 字數截斷測試
│   └── test_integration.py        # 整合測試
```

## 五、風險與建議

### 5.1 潛在風險

1. **LLM 回傳格式不穩定**：若 LLM 回傳的 HTML 格式不規則,可能影響截斷邏輯
2. **中文字數計算誤差**：需確保使用正確的中文字數計算方式（len() vs 正則表達式）
3. **HTML 標籤誤截**：截斷時需考慮標籤的完整性,避免截斷到標籤中間

### 5.2 建議事項

1. 先完成核心程式碼修改,再進行測試編寫
2. 建立獨立的截斷函數模組,便於單獨測試
3. 在 QA 環境進行完整的 E2E 測試驗證

## 六、後續行動

1. **立即開始**：修改 prompt_builder.py,加入 word_limit 動態帶入
2. **短期目標**：完成 llm_service.py 的 max_output_tokens 動態計算
3. **短期目標**：實作 generate_brief.py 的字數截斷邏輯
4. **中期目標**：編寫完整測試,並在 QA 環境驗證

---

**報告日期**：2024-04-10  
**報告人**：Project Analyst  
**版本**：v1.1