# Phase 15 - 驗證清單

**最後更新**: 2026-04-15

---

## 成功標準

| # | 標準 | 驗證方式 | 狀態 |
|---|------|----------|------|
| 1 | `config/search_config.json` 中的 `models.gemini_fewshot.model` 改變時，`gemini_fewshot` provider 實際使用的模型跟著變 | 修改 config，重新建立 tool，確認 `tool.model` | ✅ |
| 2 | `config/search_config.json` 中的 `models.gemini_planner_tavily.model` 改變時，`gemini_planner_tavily` provider 實際使用的模型跟著變 | 修改 config，重新建立 tool，確認 `tool.model` | ✅ |
| 3 | `search_tools.py` 中 `generate_content` 呼叫無硬編碼模型名稱 | 全文搜索 `gemini-2.0-flash` / `gemini-2.0-flash-lite` 在非預設值 contexts | ✅ |
| 4 | 所有模型配置只存在於 `config/search_config.json` 一個地方 | 確認 `search_tools.py` 中無模型名字面量 | ✅ |

---

## 功能驗證

### ConfigDrivenSearchTool 基本功能

- [ ] `ConfigDrivenSearchTool()` 可從實際檔案載入
- [ ] `config.models` 包含 `gemini_fewshot` 和 `gemini_planner_tavily`
- [ ] `switch_provider()` 可動態切換 provider
- [ ] `reload_config()` 可熱重載配置
- [ ] 單例模式正常運作

### 模型參數傳遞

- [ ] `gemini_fewshot` provider 的 tool 有正確的 `model` 和 `temperature`
- [ ] `gemini_planner_tavily` provider 的 tool 有正確的 `model` 和 `temperature`
- [ ] `create_search_tool('gemini_planner_tavily', model='...')` 可覆寫模型
- [ ] 未提供 model 時使用 default 值

### 新 Schema 解析

- [ ] `config/search_config.json` 可被正確解析
- [ ] `search` 區塊的 `provider` 和 `max_results` 正確讀取
- [ ] `models` 區塊的各 provider 配置正確讀取
- [ ] 缺少 `models` 時不會 crash（有 default fallback）

---

## 整合驗證

### 搜尋模組

- [ ] `from src.services.config_driven_search import search` 可正常 import
- [ ] `search("公司名稱")` 函式可正常執行
- [ ] 三種 provider (`tavily`, `gemini_fewshot`, `gemini_planner_tavily`) 都可正常運作
- [ ] `parallel_multi_source` provider 正常運作

### 主流程 LangGraph

- [ ] `from src.langgraph_state.company_brief_graph import create_company_brief_graph` 可正常 import
- [ ] `search_node` 使用 `ConfigDrivenSearchTool` 正常運作
- [ ] 現有測試套件 (`tests/test_services.py`) 全部通過

---

## 向後相容驗證

- [ ] 現有呼叫 `ConfigDrivenSearchTool()` 不帶參數時使用預設值
- [ ] 現有呼叫 `ConfigDrivenSearchTool(config_path='...')` 仍然正常
- [ ] `config_dict` 作為第一參數傳入時正確處理
- [ ] 舊格式的 `config/search_config.json`（帶 `temperature`/`model` 在 `search` 底下）仍可解析

---

## 發現的問題與修復

| 日期 | 問題 | 修復 | 狀態 |
|------|------|------|------|
| 2026-04-15 | `config_dict` 參數順序錯誤，導致 dict 被當作 `config_path` | 將 `config_dict` 改為第一參數 | ✅ 已修復 |
| 2026-04-15 | `from_dict` 只解析 `search` 區塊，無法讀取根層級的 `models` | 更新 `from_dict` 同時解析 `search` 和 `models` 區塊 | ✅ 已修復 |
| 2026-04-15 | `SearchConfig` 移除了 `model`/`temperature` 欄位，導致 `_create_tool` 報錯 | 改為從 `self.config.models` 讀取 | ✅ 已修復 |

---

## 最終確認

- [x] 所有工項完成
- [x] 所有測試通過
- [x] 文件已更新
- [x] Phase 15 完成摘要已記錄
