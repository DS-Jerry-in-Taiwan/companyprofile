# Phase 15 - 模型配置統一管理

## 階段概述

**階段名稱**: Phase 15 - 模型配置統一管理
**版本**: v1.0.0
**執行日期**: 2026-04-15
**預計耗時**: 1 天
**執行模式**: Development Agent 逐步執行
**當前狀態**: ✅ 已完成

---

## 目標

將散落在各處的搜尋工具模型配置統一集中到 `config/search_config.json` 的 `models` 區塊，消除所有硬編碼。

### 現有問題

| 位置 | 目前值 | 問題 |
|------|--------|------|
| `config/search_config.json` 第13行 | `"model": "gemini-2.0-flash-lite"` | 放在 `search` 底下，schema 不夠明確 |
| `search_tools.py` 第401行 `GeminiPlannerTavilyTool` | `model="gemini-2.0-flash"` | **完全寫死**，config 完全沒效 |

---

## 新 Schema：`config/search_config.json`

```json
{
  "search": {
    "provider": "gemini_fewshot",
    "max_results": 3
  },
  "models": {
    "gemini_fewshot": {
      "model": "gemini-2.0-flash-lite",
      "temperature": 0.2
    },
    "gemini_planner_tavily": {
      "model": "gemini-2.0-flash",
      "temperature": 0.1
    }
  }
}
```

---

## 工項清單

| # | 工項 | 檔案 | 狀態 |
|---|------|------|------|
| 1 | `SearchConfig` + `ModelConfig` dataclass | `config_driven_search.py` | ✅ |
| 2 | `_create_tool()` 從 `models` dict 讀取 | `config_driven_search.py` | ✅ |
| 3 | `GeminiPlannerTavilyTool` 接收 model/temp | `search_tools.py` | ✅ |
| 4 | 新 schema `config/search_config.json` | config/ | ✅ |
| 5 | `.env.example` 更新 | 專案根目錄 | ✅ |
| 6 | 最終驗證 | - | ✅ |

---

## 變更摘要

### `src/services/config_driven_search.py`
- 新增 `ModelConfig` dataclass
- `SearchConfig` 新增 `models: Dict[str, ModelConfig]` 欄位
- `from_dict()` 解析 `models` 區塊（從根層級）
- `_create_tool()` 從 `self.config.models` 讀取各 provider 的模型配置
- 修正參數順序：`config_dict` 改為第一參數

### `src/services/search_tools.py`
- `GeminiPlannerTavilyTool.__init__` 新增 `self.model` + `self.temperature`
- `search()` 方法中的 `generate_content` 改用 `self.model` / `self.temperature`

### `config/search_config.json`
- `search` 區塊：只留 `provider` + `max_results`
- 新增 `models` 區塊：各 provider 的 `model` + `temperature` 集中管理

### `.env.example`
- 新增搜尋模型說明（預留未來環境變數覆寫用）

---

## 成功標準

| 標準 | 狀態 |
|------|------|
| `models.gemini_fewshot.model` 改變時實際模型跟著變 | ✅ |
| `models.gemini_planner_tavily.model` 改變時實際模型跟著變 | ✅ |
| `generate_content` 呼叫中無硬編碼模型名稱 | ✅ |
| 所有模型配置只在 `config/search_config.json` 一處 | ✅ |

---

## 整合測試結果

| 測試 | 內容 | 結果 |
|------|------|------|
| 測試 1 | 實際檔案載入 + 模型解析 | ✅ |
| 測試 2 | `switch_provider()` 動態切換 | ✅ |
| 測試 3 | 熱重載 `reload_config()` | ✅ |
| 測試 4 | `create_search_tool()` 工廠函式 | ✅ |
| 測試 5 | `parallel_multi_source` provider | ✅ |
| 測試 6 | `config_path` 關鍵字參數 | ✅ |

**現有測試套件**: `tests/test_services.py` 9/9 passed ✅

---

## 預期影響範圍

| 範圍 | 影響 |
|------|------|
| 搜尋模組 | ✅ 完全向後相容 |
| 主流程 LangGraph | ✅ 無影響（search_node 直接受益） |
| Layer 5/6 標籤生成 | ✅ 無影響（使用 `llm_service.py` 的 Gemini） |

---

## 相關檔案

- `docs/agent_context/phase15_model_config_unification/phase15-model-config-unification.md` - 完整技術文件
- `src/services/config_driven_search.py` - 配置驅動搜尋工具
- `src/services/search_tools.py` - 搜尋工具層
- `config/search_config.json` - 搜尋策略配置
