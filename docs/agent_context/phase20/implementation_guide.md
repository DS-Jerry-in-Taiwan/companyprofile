ㄍㄠ# Phase20 實作指南：配置驅動架構重構

## 概述

- **目標**：將字段 → 面向映射從硬編碼改為配置文件驅動
- **scope**：僅重構映射邏輯和 Prompt 生成，不改變工具的輸入/輸出介面
- **預期成果**：新增字段只需修改 `field_mapping.json` 即可

---

## 階段邊界

### ✅ 允許修改的檔案

| 檔案 | 修改內容 |
|------|----------|
| `config/field_mapping.json` | 新增配置文件 |
| `config/field_mapping_schema.json` | 新增 JSON Schema |
| `src/services/config_loader.py` | 新增配置載入器 |
| `src/services/search_tools.py` | 修改 Prompt 生成邏輯 |
| `src/services/config_driven_search.py` | 修改配置讀取邏輯 |
| `src/langgraph_state/company_brief_graph.py` | 修改映射取得邏輯 |
| `tests/test_config_driven/*.py` | 新增單元測試 |
| `tests/test_integration/*.py` | 新增整合測試 |

### 🚫 禁止修改的檔案

| 檔案 | 原因 |
|------|------|
| `src/services/search_tools.py` 中的工具本身 | 只改 Prompt 生成，不改工具邏輯 |
| `src/tools/*.py` | 工具介面保持不變 |
| `src/prompts/*.py` | Prompt 模板保持不變（除非必要） |
| `config/search_config.json` | 這是搜尋策略配置，與本階段無關 |

---

## 開發步驟與 Checklist

### Step 1: 建立配置層

**完成標準**：
- [ ] `config/field_mapping.json` 存在且格式正確
- [ ] `config/field_mapping_schema.json` 存在且通過驗證

**實作內容**：
1. 建立 `config/field_mapping.json`
2. 建立 `config/field_mapping_schema.json`
3. 驗證配置格式正確

**禁止事項**：
- 不要在這個階段修改任何 Python 代碼

---

### Step 2: 建立配置載入器

**完成標準**：
- [ ] `src/services/config_loader.py` 存在
- [ ] 能夠載入並驗證 `field_mapping.json`
- [ ] 基本的單元測試通過

**實作內容**：
1. 建立 `config_loader.py`
2. 實作 `load_field_mapping()` 函數
3. 實作 JSON Schema 驗證
4. 建立 fallback 機制

**禁止事項**：
- 不要修改 `search_tools.py` 或 `company_brief_graph.py`

---

### Step 3: 重構 search_tools.py

**完成標準**：
- [ ] Fewshot 工具的 prompt 從配置動態生成
- [ ] 輸出結果與重構前一致
- [ ] 單元測試通過

**實作內容**：
1. 修改 `search_tools.py` 引入 `config_loader.py`
2. 修改 `FewshotSearchTool._build_prompt()` 從配置讀取 fields
3. 執行現有測試確認輸出不變

**禁止事項**：
- 不要修改工具的搜尋邏輯（`_search()` 方法）
- 不要修改輸出格式

---

### Step 4: 重構 company_brief_graph.py

**完成標準**：
- [ ] 映射邏輯從配置讀取
- [ ] 輸出結果與重構前一致
- [ ] 單元測試通過

**實作內容**：
1. 修改 `company_brief_graph.py` 引入 `config_loader.py`
2. 修改 `get_aspect_mapping()` 或類似函數從配置讀取 mapping
3. 執行現有測試確認輸出不變

**禁止事項**：
- 不要修改圖的節點邏輯（只改映射取得方式）

---

### Step 5: 重構 config_driven_search.py（如有需要）

**完成標準**：
- [ ] 如果有硬編碼的映射，也改為從配置讀取
- [ ] 測試通過

**實作內容**：
1. 檢查是否有硬編碼的映射
2. 如有，修改為從配置讀取

**禁止事項**：
- 不要新增功能，只做重構

---

### Step 6: 撰寫單元測試

**完成標準**：
- [ ] `tests/test_config_driven/test_config_loader.py` 存在
- [ ] `tests/test_config_driven/test_field_mapping.py` 存在
- [ ] 所有測試通過

**實作內容**：
1. 建立 `tests/test_config_driven/` 目錄
2. 撰寫配置載入測試
3. 撰寫映射邏輯測試

**禁止事項**：
- 不要 mock 配置檔案，使用實際的 `field_mapping.json`

---

### Step 7: 撰寫整合測試

**完成標準**：
- [ ] `tests/test_integration/test_config_driven_search.py` 存在
- [ ] 端到端測試通過

**實作內容**：
1. 建立 `tests/test_integration/` 目錄
2. 撰寫端到端測試（搜尋 → 摘要流程）

**禁止事項**：
- 不要修改實際的搜尋結果驗證邏輯

---

### Step 8: 更新階段紀錄

**完成標準**：
- [ ] `docs/agent_context/phase20/phase20_summary.md` 存在
- [ ] 包含所有變更記錄

**實作內容**：
1. 撰寫階段總結文件
2. 記錄所有變更
3. 標記待辨事項（如有）

---

## 測試驗證原則

### 配置正確性驗證

```python
# 配置檔必須包含以下欄位
{
    "fields": [...],      # 7 個字段列表
    "mapping": {...}      # 字段 → 面向映射
}
```

### 輸出不變性驗證

重構前後的輸出必須一致：
- Fewshot 工具輸出：同樣的 7 字段 JSON
- Summary 結果：同樣的面向分類

### Fallback 驗證

當配置檔不存在或格式錯誤時，系統應該：
- 記錄 warning log
- 使用預設的硬編碼值（向後兼容）

---

## 預估時間

| Step | 內容 | 預估時間 |
|------|------|----------|
| Step 1 | 建立配置層 | 20 min |
| Step 2 | 建立配置載入器 | 30 min |
| Step 3 | 重構 search_tools.py | 20 min |
| Step 4 | 重構 company_brief_graph.py | 20 min |
| Step 5 | 重構 config_driven_search.py | 10 min |
| Step 6 | 撰寫單元測試 | 30 min |
| Step 7 | 撰寫整合測試 | 30 min |
| Step 8 | 更新階段紀錄 | 10 min |
| **總計** | | **~2.5 hr** |

---

## 緊急聯絡人（TODO）

如果遇到以下問題，請停下來詢問：
1. 配置檔格式無法決定
2. 重構後輸出結果變了
3. 不確定某個檔案是否應該修改

---

## 版本歷史

| 日期 | 版本 | 說明 |
|------|------|------|
| 2026-04-20 | v1.0 | 初版建立 |