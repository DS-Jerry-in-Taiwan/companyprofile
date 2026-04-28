# Phase 18：開發規劃

**日期**: 2026-04-17
**版本**: v1.0.0

---

## 🎯 目標

將 `ParallelAspectSearchTool` 的輸出改用 **Gemini Structured Output**，確保輸出格式一致，解決目前 foundation 回傳 dict 而非字串的問題。

---

## 📝 問題描述

### 現況問題

`ParallelAspectSearchTool` 目前的輸出格式不穩定：

```python
# 有時輸出
{
    'foundation': {'公司名稱': '...', '統一編號': '...'},  # ❌ dict
    'core': '字串內容...',                                   # ✅ 字串
    'vibe': '字串內容...',
    'future': '字串內容...'
}

# 預期輸出
{
    'foundation': '字串內容...',  # ✅ 全部都是字串
    'core': '字串內容...',        # ✅
    'vibe': '字串內容...',        # ✅
    'future': '字串內容...'       # ✅
}
```

### 影響

1. `summary_node` 處理失敗：`'dict' object has no attribute 'strip'`
2. 回落到錯誤訊息："由於技術問題，無法取得更詳細的資訊..."
3. 輸出內容從 ~2000 字降至 ~60 字

---

## 💡 解決方案

使用 Gemini 的 **Structured Output** 功能，強制指定輸出格式：

```python
from google.genai import types

# 定義輸出 Schema
schema = types.Schema(
    type=types.Type.OBJECT,
    properties={
        'foundation': types.Schema(type=types.Type.STRING, description='品牌實力與基本資料'),
        'core': types.Schema(type=types.Type.STRING, description='技術產品與服務核心'),
        'vibe': types.Schema(type=types.Type.STRING, description='職場環境與企業文化'),
        'future': types.Schema(type=types.Type.STRING, description='近期動態與未來展望'),
    },
    required=['foundation', 'core', 'vibe', 'future']
)

# 使用 structured output
config = types.GenerateContentConfig(
    response_schema=schema,
    response_mime_type='application/json',
)
```

---

## 📋 開發步驟

### 步驟 1：問題分析

- [ ] 確認當前輸出格式問題
- [ ] 分析 Gemini 回應格式
- [ ] 記錄問題案例

### 步驟 2：Schema 設計

- [ ] 設計四面向的輸出 Schema
- [ ] 定義每個面向的字數限制
- [ ] 驗證 Schema 正確性

### 步驟 3：程式實作

- [ ] 修改 `ParallelAspectSearchTool`
- [ ] 加入 `response_schema` 設定
- [ ] 確保 `response_mime_type='application/json'`
- [ ] 更新 `_search_single_aspect` 方法

### 步驟 4：整合測試

- [ ] 單元測試：驗證輸出格式
- [ ] 整合測試：通過 `summary_node`
- [ ] Checkpoint 1 測試

### 步驟 5：文件更新

- [ ] 更新 README
- [ ] 更新測試記錄
- [ ] 提交程式碼

---

## 📊 預計工時

| 步驟 | 任務 | 工時 | 累計 |
|------|------|------|------|
| 步驟 1 | 問題分析 | 1h | 1h |
| 步驟 2 | Schema 設計 | 1h | 2h |
| 步驟 3 | 程式實作 | 2h | 4h |
| 步驟 4 | 整合測試 | 2h | 6h |
| 步驟 5 | 文件更新 | 1h | 7h |
| **總計** | | **7h** | |

---

## 📁 相關檔案

| 檔案 | 說明 |
|------|------|
| `src/services/search_tools.py` | ParallelAspectSearchTool 實作 |
| `src/langgraph_state/company_brief_graph.py` | summary_node 彙整邏輯 |
| `config/search_config.json` | 搜尋策略配置 |

---

## 🎯 驗收標準

1. `ParallelAspectSearchTool` 所有面向輸出皆為字串
2. `summary_node` 處理不會失敗
3. Checkpoint 1 測試通過
4. 輸出內容豐富度恢復到 ~2000 字

---

## 💭 技術決策

| 決策 | 理由 | 影響 |
|------|------|------|
| 使用 Gemini Structured Output | 確保輸出格式穩定 | 需要更新 Gemini SDK 用法 |
| response_mime_type='application/json' | 強制 JSON 格式輸出 | 解析更簡單 |
| 不使用 JSON mode prompt | Structured Output 更可靠 | Prompt 可以更簡潔 |

---

*最後更新：2026-04-17*
