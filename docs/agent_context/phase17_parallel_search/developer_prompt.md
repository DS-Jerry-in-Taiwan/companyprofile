# Phase 17：平行查詢模組開發 - Developer Prompt

> **⚠️ 重要：請依序完成每個步驟，完成後更新本文檔標記進度，再開始下一個步驟。**

---

## 🎯 開發目標

實現真正的平行 LLM API 呼叫，讓每個面向使用獨立的 Prompt 進行搜尋，提升搜尋效能 40-50%。

### 預期效益

| 指標 | 當前 | 目標 | 改善 |
|------|------|------|------|
| 搜尋時間 | 10-12s | 6-8s | **40-50%** |
| API 呼叫 | 1次 | 4次 | 可控 |

---

## 📋 開發進度追蹤

| Step | 項目 | 狀態 | 完成日期 | 負責人 |
|------|------|------|----------|--------|
| 0 | 環境準備 | ✅ | 2026-04-17 | Developer |
| 1 | 步驟 1：平行查詢工具 | 🔄 | - | Developer |
| 2 | 步驟 2：工具工廠 | 🔄 | - | Developer |
| 3 | 步驟 3：配置驅動層 | 🔄 | - | Developer |
| 4 | 步驟 4：配置文件 | 🔄 | - | Developer |
| 5 | 步驟 5：主流程 | 🔄 | - | Developer |
| 6 | 步驟 6：整合測試 | 🔄 | - | Developer |
| 7 | 步驟 7：文件更新 | 🔄 | - | Developer |

---

## 📚 參考文件

| 文件 | 位置 | 說明 |
|------|------|------|
| 開發規劃 | `docs/agent_context/phase17_parallel_search/phase17-development-plan.md` | 總規劃 |
| 架構設計 | `docs/agent_context/phase17_parallel_search/02_architecture_design.md` | 技術設計 |
| 步驟 1 | `docs/agent_context/phase17_parallel_search/03_step1_parallel_tool.md` | 平行工具實作 |
| 步驟 2 | `docs/agent_context/phase17_parallel_search/04_step2_factory_cache.md` | 工廠實作 |
| 步驟 3-5 | `docs/agent_context/phase17_parallel_search/05_step3_config_mainflow.md` | 配置與主流程 |
| 步驟 6 | `docs/agent_context/phase17_parallel_search/06_step6_integration_test.md` | 整合測試 |
| 驗收標準 | `docs/agent_context/phase17_parallel_search/09_acceptance_criteria.md` | 驗收標準 |

---

## 🚀 開始開發

### Step 0：環境準備

**任務**：
1. 建立開發分支
2. 確保環境正常

**執行**：
```bash
# 1. 建立分支
git checkout -b feature/phase17-parallel-search

# 2. 確認 Python 環境
python --version  # 應該是 3.14+

# 3. 確認依賴
pip list | grep -E "pytest|google-genai"
```

**完成標準**：
- [ ] 分支建立成功
- [ ] Python 環境正常
- [ ] 依賴已安裝

**更新文件**：完成後更新本文件的 Step 0 狀態

---

### Step 1：實作 ParallelAspectSearchTool

**任務邊界**：
- ✅ 新增 `ParallelAspectSearchTool` 類別到 `src/services/search_tools.py`
- ✅ 定義 4 面向的獨立 Prompt（`ASPECT_PROMPTS`）
- ✅ 使用 `ThreadPoolExecutor` 實現平行執行
- ✅ 實現 `_search_single_aspect()` 方法
- ✅ 實現結果彙整邏輯

**不需要做的**：
- ❌ 不修改主流程
- ❌ 不修改配置文件
- ❌ 不實現工廠類

**實作位置**：`src/services/search_tools.py`

**執行測試**：
```bash
# 測試 1.1：Prompt 生成
python -c "
from src.services.search_tools import ParallelAspectSearchTool
tool = ParallelAspectSearchTool()
assert 'foundation' in tool.ASPECT_PROMPTS
print('✅ 測試 1.1 通過')
"

# 測試 1.2：平行執行（需要網路）
python -c "
import time
from src.services.search_tools import ParallelAspectSearchTool
tool = ParallelAspectSearchTool()
result = tool.search('台積電')
print(f'API 呼叫: {result.api_calls}')
assert result.api_calls == 4
print('✅ 測試 1.2 通過')
"
```

**完成標準**：
- [ ] ParallelAspectSearchTool 類別存在
- [ ] 4 個面向的 Prompt 定義正確
- [ ] ThreadPoolExecutor 平行執行正常
- [ ] 結果正確彙整

**更新文件**：
1. 更新 `docs/agent_context/phase17_parallel_search/03_step1_parallel_tool.md` 的「開發紀錄」
2. 更新本文件的 Step 1 狀態為 ✅

---

### Step 2：實作 SearchToolFactory

**任務邊界**：
- ✅ 新增 `src/services/tool_factory.py` 檔案
- ✅ 實現 `_tools` 緩存字典
- ✅ 實現 `get_tool()` 方法（帶緩存）
- ✅ 實現 `reset()` 方法

**不需要做的**：
- ❌ 不修改現有工具類別
- ❌ 不修改主流程
- ❌ 不修改配置文件

**實作位置**：`src/services/tool_factory.py`（新檔案）

**執行測試**：
```bash
# 測試 2.1：工具緩存
python -c "
from src.services.tool_factory import SearchToolFactory
SearchToolFactory.reset()
tool1 = SearchToolFactory.get_tool('parallel_aspect_search')
tool2 = SearchToolFactory.get_tool('parallel_aspect_search')
assert tool1 is tool2
print('✅ 測試 2.1 通過')
"

# 測試 2.2：reset 功能
python -c "
from src.services.tool_factory import SearchToolFactory
SearchToolFactory.reset()
tool1 = SearchToolFactory.get_tool('parallel_aspect_search')
SearchToolFactory.reset()
tool2 = SearchToolFactory.get_tool('parallel_aspect_search')
assert tool1 is not tool2
print('✅ 測試 2.2 通過')
"
```

**完成標準**：
- [ ] SearchToolFactory 類別存在
- [ ] 工具緩存正確
- [ ] reset 功能正確

**更新文件**：
1. 更新 `docs/agent_context/phase17_parallel_search/04_step2_factory_cache.md` 的「開發紀錄」
2. 更新本文件的 Step 2 狀態為 ✅

---

### Step 3：增強 ConfigDrivenSearchTool

**任務邊界**：
- ✅ 修改 `src/services/config_driven_search.py`
- ✅ 新增 `parallel` 和 `max_workers` 欄位到 `SearchConfig`
- ✅ 修改 `_create_tool()` 使用工廠
- ✅ 新增 `search_with_strategy()` 方法

**不需要做的**：
- ❌ 不修改 search_node
- ❌ 不修改配置文件

**實作位置**：`src/services/config_driven_search.py`

**執行測試**：
```bash
# 測試 3.1：配置解析
python -c "
from src.services.config_driven_search import ConfigDrivenSearchTool
tool = ConfigDrivenSearchTool()
assert hasattr(tool, 'search_with_strategy')
print('✅ 測試 3.1 通過')
"
```

**完成標準**：
- [ ] SearchConfig dataclass 修改正確
- [ ] search_with_strategy 方法存在
- [ ] 配置驅動正常

**更新文件**：
1. 更新 `docs/agent_context/phase17_parallel_search/05_step3_config_mainflow.md` 的「開發紀錄」
2. 更新本文件的 Step 3 狀態為 ✅

---

### Step 4：更新配置文件

**任務邊界**：
- ✅ 修改 `config/search_config.json`
- ✅ 新增 `parallel_aspect_search` provider
- ✅ 新增 `strategies` 區塊
- ✅ 新增 `parallel` 和 `max_workers` 參數

**不需要做的**：
- ❌ 不修改其他設定檔

**實作位置**：`config/search_config.json`

**驗證**：
```bash
# 測試 4.1：配置文件
python -c "
import json
with open('config/search_config.json') as f:
    config = json.load(f)
assert 'strategies' in config
assert 'parallel_aspect_search' in str(config)
print('✅ 測試 4.1 通過')
"
```

**完成標準**：
- [ ] 配置文件格式正確
- [ ] strategies 區塊存在
- [ ] parallel_aspect_search 配置正確

**更新文件**：
1. 更新 `docs/agent_context/phase17_parallel_search/05_step3_config_mainflow.md` 的「開發紀錄」
2. 更新本文件的 Step 4 狀態為 ✅

---

### Step 5：調整主流程

**任務邊界**：
- ✅ 修改 `src/langgraph_state/company_brief_graph.py`
- ✅ 移除查詢字串中的「官網」關鍵字
- ✅ 支援 `strategy` 參數
- ✅ 保持結果處理邏輯不變

**不需要做的**：
- ❌ 不修改 Summary Node
- ❌ 不修改其他節點

**實作位置**：`src/langgraph_state/company_brief_graph.py` 的 `search_node` 函數

**驗證**：
```bash
# 測試 5.1：主流程整合
python -c "
from src.langgraph_state.company_brief_graph import search_node
print('✅ 測試 5.1 通過：search_node 存在')
"
```

**完成標準**：
- [ ] search_node 移除「官網」
- [ ] 支援 strategy 參數
- [ ] 結果處理正確

**更新文件**：
1. 更新 `docs/agent_context/phase17_parallel_search/05_step3_config_mainflow.md` 的「開發紀錄」
2. 更新本文件的 Step 5 狀態為 ✅

---

### Step 6：整合測試

**任務邊界**：
- ✅ 執行完整流程測試
- ✅ 執行效能對比測試
- ✅ 執行錯誤處理測試

**不需要做的**：
- ❌ 不需要撰寫新測試（使用現有測試框架）

**執行測試**：
```bash
# 完整流程測試
python -c "
import time
from src.services.config_driven_search import ConfigDrivenSearchTool

tool = ConfigDrivenSearchTool()
result = tool.search_with_strategy('台積電', strategy='complete')

print(f'搜尋成功: {result.success}')
print(f'API 呼叫: {result.api_calls}')
print(f'結果面向: {list(result.data.keys())}')

assert result.api_calls == 4
assert 'foundation' in result.data
print('✅ 完整流程測試通過')
"

# 效能對比
python -c "
import time
from src.services.config_driven_search import ConfigDrivenSearchTool

tool = ConfigDrivenSearchTool()

# 測試不同策略
for strategy in ['fast', 'basic', 'complete']:
    start = time.time()
    result = tool.search_with_strategy('台積電', strategy=strategy)
    elapsed = time.time() - start
    print(f'{strategy}: {elapsed:.2f}s ({result.api_calls} API calls)')
"
```

**完成標準**：
- [ ] 完整流程測試通過
- [ ] 4 個面向正確執行
- [ ] 效能符合預期（< 10s）

**更新文件**：
1. 更新 `docs/agent_context/phase17_parallel_search/10_test_records.md` 的「測試紀錄」
2. 更新本文件的 Step 6 狀態為 ✅

---

### Step 7：文件更新

**任務邊界**：
- ✅ 更新 `docs/agent_context/phase17_parallel_search/11_development_log.md`
- ✅ 填寫所有開發紀錄
- ✅ 確認所有文件狀態

**不需要做的**：
- ❌ 不需要撰寫新的設計文件

**完成標準**：
- [ ] 開發日誌完整
- [ ] 所有文件狀態正確
- [ ] README.md 更新

**更新文件**：
1. 更新 `docs/agent_context/phase17_parallel_search/11_development_log.md`
2. 更新本文件的 Step 7 狀態為 ✅

---

## ✅ 驗收確認

完成所有步驟後，確認以下標準：

### 功能驗收
- [ ] ParallelAspectSearchTool 平行執行正確
- [ ] SearchToolFactory 緩存正確
- [ ] ConfigDrivenSearchTool 策略選擇正確
- [ ] 配置文件格式正確
- [ ] search_node 整合正確

### 效能驗收
- [ ] 搜尋時間 < 10s（目標 6-8s）
- [ ] API 呼叫 = 4 次
- [ ] 結果正確彙整

### 文件驗收
- [ ] 所有開發紀錄已填寫
- [ ] 所有文件狀態已更新
- [ ] README.md 已更新

---

## 📞 遇到問題？

如果遇到問題：
1. 查看 `docs/agent_context/phase17_parallel_search/` 下的詳細文件
2. 查看 Phase 16 的現有實現：`src/services/search_tools.py`
3. 查看當前配置：`config/search_config.json`

---

## 🎯 任務邊界總結

| 步驟 | 實作位置 | 職責範圍 |
|------|----------|----------|
| Step 1 | `src/services/search_tools.py` | 只實作 ParallelAspectSearchTool |
| Step 2 | `src/services/tool_factory.py`（新） | 只實作 SearchToolFactory |
| Step 3 | `src/services/config_driven_search.py` | 只增強配置驅動 |
| Step 4 | `config/search_config.json` | 只更新配置 |
| Step 5 | `src/langgraph_state/company_brief_graph.py` | 只調整 search_node |
| Step 6 | - | 執行測試 |
| Step 7 | `docs/agent_context/phase17_parallel_search/` | 更新文件 |

**重要**：每完成一步，**立即更新文件**，再開始下一步。

---

*Developer Prompt 版本：v1.0.0*  
*建立日期：2026-04-17*  
*開始開發：待 Developer 確認*