# Phase 9 Agent 角色定義

## 一、角色概述

### 1.1 角色矩陣

| 角色 | 主要職責 | 協作對象 |
|------|----------|----------|
| 錯誤處理 Agent | 統一管理重試與 Fallback 策略 | 所有 Service Agent |
| 路由 Agent | 根據執行結果動態選擇下一步 | 狀態圖相關 Agent |
| 工具 Agent | 將現有模組包裝為 LangChain Tool | 各模組 Owner |
| 品質檢查 Agent | 驗證輸出內容是否符合標準 | LLM Agent |

### 1.2 角色關係圖

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 9 Agent 角色圖                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────┐                                       │
│   │ Error Handler  │◀── 接收所有錯誤事件                    │
│   │    Agent       │                                       │
│   └────────┬────────┘                                       │
│            │                                                │
│            ▼                                                │
│   ┌─────────────────┐         ┌─────────────────┐        │
│   │   Router Agent  │◀────────▶│  Tool Agent     │        │
│   │ (條件邊決策)     │         │ (Tool 包裝)     │        │
│   └────────┬────────┘         └────────┬────────┘        │
│            │                            │                   │
│            ▼                            ▼                   │
│   ┌─────────────────┐         ┌─────────────────┐        │
│   │ Quality Check   │         │   LLM Agent    │        │
│   │    Agent         │         │ (生成簡介內容)  │        │
│   └─────────────────┘         └─────────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、錯誤處理 Agent

### 2.1 職責

1. **重試策略管理**：定義統一的重試參數（次數、間隔、退避因子）
2. **Fallback 鏈管理**：維護多級 Fallback 服務列表
3. **錯誤分類**：將錯誤分類為可重試與不可重試

### 2.2 介面規範

```python
# 輸入
error_event: ErrorEvent  # 錯誤事件（類型、訊息、上下文）

# 輸出
retry_decision: RetryDecision  # 重試决策（是否重試、次數、間隔）
fallback_decision: FallbackDecision  # Fallback 决策（目標服務）
```

### 2.3 配置範例

```python
RETRY_CONFIG = {
    "max_attempts": 3,
    "initial_interval": 1.0,  # 秒
    "max_interval": 10.0,     # 秒
    "exponential_base": 2,
    "retryable_errors": [
        "TimeoutError",
        "ConnectionError",
        "HTTPError(503)",
        "HTTPError(429)",
    ],
}

FALLBACK_CHAIN = [
    {"service": "tavily", "priority": 1},
    {"service": "serper", "priority": 2},
    {"service": "web_search", "priority": 3},
    {"service": "mock", "priority": 4},
]
```

---

## 三、路由 Agent

### 3.1 職責

1. **條件邊評估**：根據節點輸出決定下一步
2. **分支選擇**：在多個可能的分支中選擇正確的路徑
3. **循環控制**：管理重試迴圈與最大次數

### 3.2 介面規範

```python
# 輸入
node_output: NodeOutput  # 當前節點的輸出
state: GraphState       # 圖形狀態

# 輸出
next_node: str          # 下一個節點名稱
route_decision: str     # 路由决策說明
```

### 3.3 路由邏輯範例

```python
def decide_next_step(state: GraphState) -> str:
    """根據狀態決定下一步"""
    
    # 檢查是否有錯誤
    if state.get("error"):
        error_type = state["error"].get("type")
        if error_type in RETRYABLE_ERRORS:
            return "retry_node"
        elif error_type in FALLBACK_ERRORS:
            return "fallback_node"
        else:
            return "error_handler"
    
    # 檢查搜尋結果
    search_result = state.get("search_result")
    if not search_result or not search_result.get("success"):
        return "fallback_search"
    
    # 檢查品質
    quality_check = state.get("quality_check")
    if quality_check and not quality_check.get("passed"):
        return "retry_generate"
    
    return "end_node"
```

---

## 四、工具 Agent

### 4.1 職責

1. **Tool 包裝**：將現有模組包裝為 LangChain Tool
2. **Tool 註冊**：管理 Tool 註冊表
3. **Tool 選擇**：根據需求選擇合適的 Tool

### 4.2 支援的 Tool

| Tool 名稱 | 功能 | 輸入 | 輸出 |
|-----------|------|------|------|
| TavilySearchTool | 網路搜尋與內容提取 | query, max_results | 搜尋結果與內容 |
| WebSearchTool | 傳統網路搜尋 | query, max_results | URL 列表 |
| LLMGenerateTool | LLM 生成簡介 | prompt, context | 生成結果 |
| QualityCheckTool | 品質檢驗 | content, criteria | 檢查結果 |

### 4.3 Tool 範例

```python
from langchain.tools import tool

@tool
def tavily_search(query: str, max_results: int = 3) -> dict:
    """
    使用 Tavily API 進行網路搜尋並提取內容
    
    Args:
        query: 搜尋查詢（例如：公司名稱 + "官網"）
        max_results: 最大結果數量
    
    Returns:
        包含 answer, results, success 的字典
    """
    client = get_tavily_client()
    result = client.search_and_extract(query, max_results)
    return result
```

---

## 五、品質檢查 Agent

### 5.1 職責

1. **標準定義**：定義品質檢查標準
2. **內容驗證**：驗證生成內容是否符合標準
3. **建議生成**：對不符合標準的內容提供改善建議

### 5.2 介面規範

```python
# 輸入
content: str              # 待檢驗內容
criteria: List[str]      # 檢查標準列表
context: dict            # 上下文資訊

# 輸出
check_result: dict        # 檢查結果（passed, issues, suggestions）
```

### 5.3 檢查標準

```python
QUALITY_CRITERIA = {
    "min_length": 100,           # 最小長度
    "max_length": 5000,         # 最大長度
    "required_fields": [        # 必要欄位
        "company_name",
        "products_services",
        "contact_info",
    ],
    "forbidden_patterns": [     # 禁止模式
        "error occurred",
        "failed to",
        "not available",
    ],
}
```

---

*文件資訊*
- 建立日期：2026-04-01
- 專案階段：Phase 9 LangChain 整合
- 文档类型：Agent 角色定义
