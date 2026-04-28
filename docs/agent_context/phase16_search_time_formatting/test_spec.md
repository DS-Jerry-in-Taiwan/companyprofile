# Phase 16 效能與品質對比測試 - 開發工項

## 📌 測試目標

量化 Phase 16 新流程相較於原本流程的價值：
1. **效能測試** - 搜尋返回結構化模板的時間差異
2. **品質測試** - 生成簡介的內容品質差異

---

## 🔄 新舊流程差異（背景知識）

### 舊流程 (v0.2.0)
```
SEARCH → 拼接 raw_answer → GENERATE → QUALATE_CHECK → END
```
- **搜尋 Prompt**: 8 欄位（統一編號、資本額、地址等）
- **返回格式**: `{field: value}` 鍵值對
- **處理方式**: `"\n\n".join(contents)` 純文字拼接

### 新流程 (v0.3.0 - Phase 16)
```
SEARCH → SUMMARY（彙整）→ GENERATE（四面向內容）→ QUALITY_CHECK → END
```
- **搜尋 Prompt**: 4 面向（foundation/core/vibe/future）
- **返回格式**: `{aspect: content}` 結構化 JSON
- **處理方式**: 按 aspect 分組合併

---

## 📋 Test Item A: 效能測試

### A1. 搜尋耗時對比

**目標**: 測量搜尋 Tool 返回指定模板的時間差異

**比較對象**:
- 舊版: `backups/v0.2.0/search_tools.py` - 8 欄位 Prompt
- 新版: `src/services/search_tools.py` - 4 面向 Prompt

**評估指標**:
```python
{
    "company": str,                    # 公司名稱
    "old_flow_search_time": float,     # 舊版搜尋耗時（秒）
    "new_flow_search_time": float,    # 新版搜尋耗時（秒）
    "time_delta": float,               # 時間差異（秒）
    "time_delta_percent": float,       # 時間差異百分比
    "success": bool,                  # 是否成功
}
```

### A2. Summary Node 耗時對比

**目標**: 測量 Summary Node 的處理時間（新增環節）

**評估指標**:
```python
{
    "company": str,
    "summary_time": float,            # Summary 處理耗時（秒）
    "result_count": int,              # 處理的結果數量
    "aspect_count": int,              # 成功彙整的面向數量
}
```

### A3. 端到端耗時對比

**目標**: 測量完整流程的總時間差異

**評估指標**:
```python
{
    "company": str,
    "old_total_time": float,          # 舊流程總耗時（秒）
    "new_total_time": float,          # 新流程總耗時（秒）
    "breakdown": {
        "search_time": float,
        "summary_time": float,       # 新流程才有
        "generate_time": float,
    },
    "delta": float,
}
```

---

## 📋 Test Item B: 品質測試

### B1. 四面向覆蓋度

**目標**: 檢查每個面向的內容完整性

**評估標準**:
```python
coverage_result = {
    "company": str,
    "coverage": {
        "foundation": 0-1,            # 0=無內容, 1=有內容
        "core": 0-1,
        "vibe": 0-1,
        "future": 0-1,
    },
    "total_coverage_score": float,    # 平均覆蓋度 (0-1)
    "content_lengths": {
        "foundation": int,            # 字數
        "core": int,
        "vibe": int,
        "future": int,
    },
}
```

### B2. 內容豐富度

**目標**: 測量生成內容的字數與資訊量

**評估指標**:
```python
richness_result = {
    "company": str,
    "total_characters": int,         # 總字數
    "total_words": int,              # 總詞數
    "avg_words_per_aspect": float,   # 每面向平均詞數
    "info_density": float,           # 資訊密度（有意義內容/總字數）
    "aspect_balance": float,         # 面向平衡度（各面向字數差異）
}
```

### B3. 新舊效果對比（可選）

**目標**: 比較新舊流程生成的簡介品質

**評估方法**:
- 輸入相同公司，比較兩種流程生成的結果
- 指標：結構化程度、資訊完整性、語意相關性

---

## 📦 測試樣本（20 間公司）

```json
[
    {"name": "台積電", "industry": "半導體", "size": "large"},
    {"name": "鴻海", "industry": "電子製造", "size": "large"},
    {"name": "聯發科", "industry": "半導體", "size": "large"},
    {"name": "富邦金控", "industry": "金融", "size": "large"},
    {"name": "中華電信", "industry": "電信", "size": "large"},
    {"name": "巨大機械", "industry": "製造", "size": "medium"},
    {"name": "誠品生活", "industry": "零售服務", "size": "medium"},
    {"name": "群暉科技", "industry": "科技", "size": "medium"},
    {"name": "Gogoro", "industry": "電動車", "size": "medium"},
    {"name": "華碩", "industry": "科技", "size": "large"},
    {"name": "台灣大哥大", "industry": "電信", "size": "medium"},
    {"name": "王品餐飲", "industry": "餐飲", "size": "medium"},
    {"name": "裕隆汽車", "industry": "汽車", "size": "medium"},
    {"name": "友達光電", "industry": "面板", "size": "large"},
    {"name": "趨勢科技", "industry": "資安", "size": "medium"},
    {"name": "聯強國際", "industry": "通路", "size": "medium"},
    {"name": "信義房屋", "industry": "房仲", "size": "medium"},
    {"name": "研華", "industry": "工業電腦", "size": "medium"},
    {"name": "崇越電通", "industry": "半導體材料", "size": "small"},
    {"name": "功能性美食", "industry": "餐飲新創", "size": "small"}
]
```

---

## 🏗️ 測試實作架構

```
tests/
├── conftest.py                  # Pytest fixtures、共用 setup
├── fixtures/
│   └── companies.json           # 測試公司清單
├── performance/
│   ├── __init__.py
│   ├── conftest.py              # 效能測試 fixtures
│   ├── test_search_time.py      # A1 搜尋耗時測試
│   ├── test_summary_time.py     # A2 Summary 耗時測試
│   └── test_end_to_end_time.py  # A3 端到端測試
├── quality/
│   ├── __init__.py
│   ├── conftest.py              # 品質測試 fixtures
│   ├── test_aspect_coverage.py  # B1 覆蓋度測試
│   └── test_content_richness.py # B2 豐富度測試
└── reports/
    └── generate_report.py       # 報告生成腳本
```

---

## ⚙️ 技術實作要求

### 1. 測試隔離

- 效能測試需要能獨立運行
- 避免測試間的相互影響
- 使用 `pytest.fixture` 管理測試資料

### 2. Mock 舊流程

```python
# 實作舊版搜尋的 mock
def mock_old_search_flow(company_name: str) -> SearchResult:
    """
    模擬 v0.2.0 的搜尋流程：
    - 使用舊版 8 欄位 Prompt
    - 返回鍵值對格式
    """
    pass

# 實作舊版 Summary 的 mock
def mock_old_summary_node(search_result: SearchResult) -> dict:
    """
    模擬 v0.2.0 的處理方式：
    - 直接拼接 raw_answer
    - 不做四面向彙整
    """
    pass
```

### 3. 時間度量

```python
import time
from contextlib import contextmanager

@contextmanager
def measure_time():
    start = time.perf_counter()
    yield lambda: time.perf_counter() - start
```

### 4. 報告生成

```python
# 輸出格式
{
    "test_date": "2026-04-16",
    "test_summary": {
        "total_companies": 20,
        "successful": 18,
        "failed": 2,
    },
    "performance_results": [...],
    "quality_results": [...],
    "recommendations": [...]
}
```

---

## 📊 預期結果模型

### 效能預期

| 指標 | 舊流程 | 新流程 | 預期差異 |
|------|--------|--------|----------|
| 搜尋耗時 | T₁ | T₂ | T₂ ≈ T₁ × 1.1~1.2 |
| Summary 耗時 | 0 | T₃ | 新增 |
| 總耗時 | T_total_old | T₁+T₃ | 待觀測 |

> Prompt 複雜度增加約 10-15%，但結構化解析可省去後處理時間

### 品質預期

| 指標 | 舊流程 | 新流程 | 預期差異 |
|------|--------|--------|----------|
| 四面向覆蓋 | 不存在 | 4/4 | +100% |
| 內容結構化 | 混雜 | 分類清晰 | +結構化 |
| 資訊完整性 | 部分欄位 | 全四面向 | +覆蓋度 |

---

## 📊 實際測試結果（2026-04-16）

### 效能測試結果

| 指標 | 數值 |
|------|------|
| 測試公司數 | 10 |
| 舊流程平均搜尋時間 | 5.19s |
| 新流程平均搜尋時間 | 7.98s |
| 平均時間差異 | **+57.4%** |

> 發現：新流程比舊流程慢約 57%，高於預期的 10-15%

### 品質測試結果

| 指標 | 數值 |
|------|------|
| 完美覆蓋公司數 | 10/10 |
| 平均覆蓋率 | **100%** |
| 平均面向平衡度 | **0.90** |

> 發現：四面向覆蓋率極高，結構化效果顯著

### 結論

1. ⚠️ **效能**：新流程比舊流程慢約 57%，需優化搜尋 Prompt 或快取機制
2. ✅ **品質**：四面向覆蓋率 100%，結構化效果顯著
3. ✅ **平衡度**：面向平衡度平均 0.90，內容分布均勻

### 測試檔案

- 測試報告：`docs/operations/phase16-test-report.md`
- 測試程式碼：`tests/performance/`、`tests/quality/`

---

## 🚀 交付物

1. **測試程式碼** - `tests/` 目錄下的所有測試檔案
2. **測試資料** - `tests/fixtures/companies.json`
3. **測試報告** - JSON/Markdown 格式的測試結果
4. **文件更新** - 更新 `docs/operations/` 下的相關文件

---

## 📝 備註

- 測試需要真實 API 呼叫，請注意 API 費用
- 建議分批執行測試，避免 API 限流
- 失敗的測試需要記錄錯誤原因
