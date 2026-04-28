# Phase 18：步驟 1 - 問題分析

**日期**: 2026-04-17
**步驟**: 1
**狀態**: ✅ 完成

---

## 🎯 步驟目標

深入分析 `ParallelAspectSearchTool` 輸出格式問題的根本原因。

---

## 📋 分析任務

### 任務 1.1：確認問題現況

**測試腳本**：

```python
from src.services.search_tools import ParallelAspectSearchTool

tool = ParallelAspectSearchTool(timeout=30)

# 測試多個公司
companies = ['澳霸有限公司', '台積電', '南晃交通器材']

for company in companies:
    result = tool.search(company)

    print(f"\n{company}:")
    print(f"  data type: {type(result.data)}")

    for aspect, content in result.data.items():
        print(f"  {aspect}: {type(content).__name__}")
        if isinstance(content, dict):
            print(f"    ⚠️  這是 dict，不是字串！")
            print(f"    內容: {str(content)[:100]}...")
```

**預期結果**：
- 所有面向都是 `str` 類型

**實際結果**：
- `foundation` 有時是 `dict`
- 其他面向是 `str`

---

### 任務 1.2：分析 Prompt 設計

**當前 Prompt**：

```
你是一個公司資訊搜尋專家。請搜尋「{company}」的品牌實力與基本資料。

請以 JSON 格式返回：
{"foundation": "品牌實力與基本資料內容"}

【要求】
- 只使用實際搜尋到的資訊
- 不超過 500 字
- 返回純 JSON，無額外說明
```

**問題**：
1. Prompt 說 "返回 JSON"，但沒有強制格式
2. Gemini 可能會在 foundation 內回傳巢狀結構
3. 依賴 Prompt 工程而非技術約束

---

### 任務 1.3：分析回應解析邏輯

**當前解析程式碼** (`_search_single_aspect`)：

```python
# 解析 JSON
json_match = re.search(
    r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}",
    response.text,
    re.DOTALL
)

content = ""
if json_match:
    try:
        data = json.loads(json_match.group(0))
        # 取得內容（可能是字串或物件）
        if isinstance(data, dict):
            content = data.get(aspect, str(data))  # ⚠️ 這裡可能返回 dict
        else:
            content = str(data)
    except:
        content = json_match.group(0)
else:
    content = response.text[:500] if response.text else ""
```

**問題**：
- 當 `data.get(aspect)` 返回 dict 時，沒有進一步處理
- `str(data)` 會產生 `"{'key': 'value'}"` 而非純文字

---

## 📊 問題案例

### 案例 1：澳霸有限公司

```python
# 實際輸出
{
    'foundation': {
        '公司名稱': '澳霸有限公司',
        '統一編號': '42965130',
        '成立時間': '2018年6月5日',
        ...
    },
    'core': '根據搜尋結果，有多家名為「澳霸」的公司...',
    'vibe': '根據搜尋結果，澳霸有限公司是一家位於高雄的庭園景觀工程公司...',
    'future': '由於我無法直接存取澳霸有限公司的內部資訊...'
}
```

**原因**：
- Gemini 在 foundation 中回傳了公司基本資料的結構化資訊
- 解析時直接將 dict 存入

---

### 案例 2：台灣荏原精密

```python
# 實際輸出
{
    'foundation': {
        '成立時間': '1997年9月',
        '統一編號': '16090317',
        '資本總額': '新台幣 690,000,000',
        ...
    },
    ...
}
```

**同樣問題**：foundation 回傳 dict

---

## 🔧 解決方案選項

| 方案 | 說明 | 優點 | 缺點 |
|------|------|------|------|
| **A. Structured Output** | 使用 Gemini response_schema | 100% 格式保證 | 需要更新 SDK 用法 |
| **B. Prompt 工程** | 強化 Prompt 說明 | 簡單 | 不夠穩定 |
| **C. 後處理解析** | 解析後轉換為字串 | 快速實作 | 複雜性增加 |

**推薦**：方案 A - Structured Output

---

## ✅ 通過標準

- [ ] 確認問題根本原因
- [ ] 分析所有失敗案例
- [ ] 選擇最適合的解決方案
- [ ] 記錄技術決策

---

## 📊 預計工時

| 任務 | 工時 |
|------|------|
| 任務 1.1 | 0.5h |
| 任務 1.2 | 0.25h |
| 任務 1.3 | 0.25h |
| **總計** | **1h** |

---

*步驟完成時間：待定*
