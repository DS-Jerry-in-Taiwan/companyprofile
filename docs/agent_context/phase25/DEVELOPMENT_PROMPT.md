# Phase 25 開發 Prompt

## 角色
你是一位後端開發工程師，負責實作 Phase 25 數字格式清理功能。

---

## 目標
1. 搜尋前清理：Prompt 要求 LLM 輸出不要帶千位逗號
2. 後處理清理：post_processing 加上數字格式清理

---

## 參考文件
- `docs/agent_context/phase25/DEVELOPMENT_PLAN.md` - 開發計劃
- `docs/agent_context/phase25/DEVELOPMENT_LOG.md` - 開發日誌

---

## 開發步驟

### Step 1: Prompt 加入數字格式要求

**目標**：在 prompt_builder.py 中加入數字格式提醒

**做法**：
1. 開啟 `src/functions/utils/prompt_builder.py`
2. 在 sections 中加入數字格式提醒，例如：
```python
sections.append("### 數字格式規範")
sections.append("- 所有數字請勿使用千位逗號分隔")
sections.append("- 例如：請寫「2582526570」而非「2,582,526,570」")
```

**通過標準**：
- [ ] prompt_builder.py 包含數字格式規範
- [ ] 匯入測試通過

**完成後**：更新 `DEVELOPMENT_LOG.md` Step 1 狀態為 ✅

---

### Step 2: 後處理加入數字清理

**目標**：在 post_processing.py 中加入數字清理函數

**做法**：
1. 開啟 `src/functions/utils/post_processing.py`
2. 新增 `clean_number_format()` 函數：
```python
import re

def clean_number_format(text: str) -> str:
    """移除數字中的千位逗號"""
    if not text:
        return text
    # 移除千位逗號 (2,582,526,570 -> 2582526570)
    # 遞歸移除，直到沒有逗號為止
    while re.search(r'\d,\d{3}', text):
        text = re.sub(r'(\d),(\d{3})', r'\1\2', text)
    return text
```
3. 在 body_html 處理後調用：
```python
# 在 return 之前
body_html = clean_number_format(body_html)
```

**通過標準**：
- [ ] clean_number_format() 函數存在
- [ ] `2,582,526,570` → `2582526570` 轉換正確
- [ ] 測試通過

**完成後**：更新 `DEVELOPMENT_LOG.md` Step 2 狀態為 ✅

---

### Step 3: 測試驗證

**目標**：端到端測試數字格式清理

**做法**：
1. 單元測試 clean_number_format()：
```python
def test_clean_number_format():
    assert clean_number_format("2,582,526,570") == "2582526570"
    assert clean_number_format("1,000,000") == "1000000"
    assert clean_number_format("新台幣 2,582,526,570 元") == "新台幣 2582526570 元"
```
2. API 端到端測試

**通過標準**：
- [ ] clean_number_format() 單元測試通過
- [ ] API 輸出無千位逗號

**完成後**：更新 `DEVELOPMENT_LOG.md` Step 3 狀態為 ✅

---

## 任務邊界

### 明確的任務邊界
| 範圍 | 說明 |
|------|------|
| 主要目標 | 數字千位逗號清理 |
| 職責 | prompt + post_processing |

### 禁止事項
| 項目 | 說明 |
|------|------|
| 不修改現有 API 響應格式 | LLMOutput schema 維持不變 |
| 不修改 error handling | 維持現有錯誤處理 |
| 不修改其他功能 | 只做數字格式清理 |

---

## 通過標準

| 標準 | 說明 |
|------|------|
| prompt 加入數字格式要求 | 包含「請勿使用千位逗號」 |
| clean_number_format() 存在 | 函數正確實現 |
| 數字轉換正確 | `2,582,526,570` → `2582526570` |
| 端到端測試通過 | API 輸出無千位逗號 |

---

## 開發紀錄更新格式

每次完成一個 Step 後，在 `DEVELOPMENT_LOG.md` 更新：

```markdown
### 📅 YYYY-MM-DD

| 時間 | 事項 | 狀態 | 備註 |
|------|------|------|------|
| HH:MM | **Step X**: [事項名稱] | ✅ | [備註] |
```

---

## 開始開發

請按照上述步驟逐一實作，每個步驟完成後：
1. 驗證通過標準
2. 更新 DEVELOPMENT_LOG.md
3. 匯報進度

祝開發順利！
