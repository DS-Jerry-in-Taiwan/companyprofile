# Phase 25 開發計劃

## 版本
- **文件版本**: v0.2.0
- **建立日期**: 2026-04-27
- **目標版本**: v0.4.2

---

## 概述

### 目標
- 搜尋前清理：Prompt 要求 LLM 輸出不要帶千位逗號
- 後處理清理：post_processing 加上數字格式清理與簡化

### 背景
- 問題：搜尋結果中的數字帶有千位逗號（如 `2,582,526,570`），且格式不自然
- 直接輸出會造成「實收資本額高達新台幣 2，582，526，570 元」
- 期望輸出：「實收資本額高達 25.8 億元」

---

## 問題案例

```
修改前: 新台幣 2,582,526,570 元
清理後: 新台幣 2582526570 元    (Phase 25 — 移除逗號)
簡化後: 新台幣 25.8億元          (Phase 25 — 數字簡化)
```

---

## 解決方案

### 方案一：搜尋前清理（Prompt 要求）

在 `prompt_builder.py` 中加入數字格式要求：

```python
# 在 prompt 中加入
sections.append("### 數字格式規範")
sections.append("- 所有數字請勿使用千位逗號分隔")
sections.append("- 例如：請寫「2582526570」而非「2,582,526,570」")
sections.append("- 貨幣金額格式為：新台幣 2582526570 元（無逗號）")
```

### 方案二：後處理清理（post_processing）

#### 2a. 移除千位逗號

在 `post_processing.py` 中加入數字清理：

```python
def clean_number_format(text: str) -> str:
    """移除數字中的千位逗號（含全形逗號）"""
    while re.search(r'\d,\d{3}', text):
        text = re.sub(r'(\d),(\d{3})', r'\1\2', text)
    while re.search(r'\d，\d{3}', text):
        text = re.sub(r'(\d)，(\d{3})', r'\1\2', text)
    return text
```

#### 2b. 數字簡化（億/萬單位）

```python
def simplify_number(text: str) -> str:
    """將大數字簡化為自然單位（億/萬）
    
    規則:
        >= 1億 → X億 / X.X億元
        >= 1萬 → X萬 / X.X萬元
        <  1萬 → 不變
    
    安全機制: 只處理後綴為「元」的數字，避免誤轉統一編號
    """
    _SIMPLIFY_PATTERN = re.compile(r'(\d{5,})\s*元')
    return _SIMPLIFY_PATTERN.sub(_simplify_number_match, text)
```

---

## Pipeline 順序

```
... → clean_number_format(移除逗號) → simplify_number(簡化單位) → ...
```

---

## 開發步驟

### Step 1: Prompt 加入數字格式要求
- [x] 修改 `prompt_builder.py`
- [x] 在 sections 中加入數字格式提醒

### Step 2: 後處理加入數字清理（移除逗號 + 簡化）
- [x] 修改 `post_processing.py`
- [x] 新增 `clean_number_format()` 函數
- [x] 新增 `simplify_number()` 函數
- [x] 在 body_html 處理後調用
- [x] 在 summary 處理後調用

### Step 3: 測試驗證
- [x] 測試數字格式清理
- [x] 測試數字簡化
- [x] 端到端測試

---

## 修改檔案

| 檔案 | 變更 |
|------|------|
| `src/functions/utils/prompt_builder.py` | 加入數字格式要求 |
| `src/functions/utils/post_processing.py` | 加入數字清理與簡化函數 |
| `scripts/test_phase25_number_format.py` | 加入數字簡化測試 (34 tests) |
| `scripts/test_phase25_real_data.py` | 1111 實際案例測試 (19 tests) |
| `scripts/test_phase25_api_integration.py` | API mock 整合測試 (34 tests) |
| `scripts/test_phase25_live_api.py` | 真實 API 測試 (21 tests, port 5000) |

---

## 測試總表

| 套件 | 檔案 | 測試數 | 結果 |
|------|------|--------|------|
| 單元 + 整合測試 | `test_phase25_number_format.py` | 34 | ✅ |
| 1111 實際案例 | `test_phase25_real_data.py` | 19 | ✅ |
| API mock 測試 | `test_phase25_api_integration.py` | 34 | ✅ |
| 真實 API 測試 | `test_phase25_live_api.py` | 21 | ✅ |
| **總計** | | **108** | **✅** |

---

## 驗收標準

| 標準 | 說明 |
|------|------|
| 數字千位逗號移除 (半形) | `2,582,526,570` → `2582526570` |
| 數字千位逗號移除 (全形) | `2，582，526，570` → `2582526570` |
| 貨幣金額簡化 | `2582526570元` → `25.8億元` |
| 萬元金額簡化 | `8000000元` → `800萬元` |
| 不誤轉統一編號 | `12345678`（無後綴元）→ 不處理 |
| 不誤轉年份 | `1987`（< 10000）→ 不處理 |
| 不誤轉日期 | `19620825`（無後綴元）→ 不處理 ⚠️ |

---

## 邊界案例（真實 API 測試發現）

### 8 位數日期格式

```
成立於 19620825 的資深企業
```

`19620825` 是 8 位數但不後綴「元」，`simplify_number` 正確不處理。但輸出可讀性差 (應為 `1962年8月25日` 或 `1962年`)，此為 LLM 輸出品質問題，非 Phase 25 範圍。

### 多個空格格式

```
資本額達新台幣 27000000    元     （多個空格）
```

`_SIMPLIFY_PATTERN = re.compile(r'(\d{5,})\s*元')` 使用 `\s*` 可正常匹配。✅

---

## 預期輸出

| 項目 | 修改前 | 清理後 | 簡化後 |
|------|--------|--------|--------|
| 資本額 | `新台幣 2,582,526,570 元` | `新台幣 2582526570 元` | `新台幣 25.8億元` |
| 營收 | `營收 50,000,000,000 元` | `營收 50000000000 元` | `營收 500.0億元` |
| 員工人數 | `員工人數 1,200 人` | `員工人數 1200 人` | `員工人數 1200 人`（不變） |

---

## 版本

| 版本 | 日期 | 變更 |
|------|------|------|
| v0.2.0 | 2026-04-27 | 加入數字簡化規則 |
| v0.1.0 | 2026-04-27 | 初始版本 |
