# 公司簡介生成與優化 API

這是一個採用 Serverless 架構的公司簡介生成與優化服務，部署於 AWS Lambda + API Gateway，提供 RESTful API 介面，支援從無到有生成公司簡介，以及優化現有的公司簡介內容。

---

## 功能特色

### 作業模式

| 模式 | 說明 |
|------|------|
| **GENERATE** | 根據輸入的公司名稱與統一編號，從網路搜取相關資訊，並由 LLM 生成專業的公司簡介 |

### 核心能力

- **自動化資料蒐集**：支援多種搜尋策略（Tavily、Gemini）
- **LLM 整合**：採用 Google Gemini 生成高品質內容
- **三模板差異化**：支援 CONCISE / STANDARD / DETAILED 三種輸出模式
- **風險控制**：內建敏感詞過濾與內容安全檢核
- **Token 成本管理**：記錄並追蹤 API 呼叫費用
- **台灣用語轉換**：自動將中國用語轉換為台灣用語（300+ 詞彙）

---

## 技術架構

### 技術堆疊

| 類別 | 技術 |
|------|------|
| Web Framework | Flask |
| LLM | Google Gemini (generativeai) |
| **搜尋策略** | **Tavily / Gemini（可配置切換）** |
| 流程控制 | LangGraph |
| Data Validation | Pydantic |
| 繁體中文處理 | OpenCC |
| Deployment | Serverless Framework (AWS Lambda + API Gateway) |
| Testing | Pytest |

### 系統架構圖

```mermaid
graph TB
    subgraph Presentation["呈現層 Presentation"]
        API[API Gateway]
        FLASK[Flask Controller<br/>api_controller.py]
    end

    subgraph Application["應用層 Application"]
        CD[Core Dispatcher<br/>core_dispatcher.py]
        GB[generate_brief.py]
        LG[LangGraph<br/>company_brief_graph.py]
    end

    subgraph Domain["領域層 Domain"]
        SN[search_node]
        GN[generate_node]
        FN[finalize_node]
        PP[Post-Processing<br/>post_processing.py]
    end

    subgraph Infrastructure["基礎設施層 Infrastructure"]
        subgraph Search["搜尋服務"]
            CDS[ConfigDrivenSearchTool]
            STF[SearchToolFactory]
            TV[TavilyBatchSearchTool]
            GF[GeminiFewShotSearchTool]
            GP[GeminiPlannerTavilyTool]
        end
        
        LLM[LLM Service<br/>llm_service.py]
        TAIWAN[TaiwanTermsConverter<br/>taiwan_terms]
        WC[WordCountValidator]
    end

    subgraph Config["配置層"]
        CFG[search_config.json]
    end

    API --> FLASK
    FLASK --> CD
    CD --> GB
    GB --> LG
    LG --> SN
    LG --> GN
    LG --> FN
    GN --> PP
    FN --> PP
    
    SN --> CDS
    CDS --> STF
    STF --> TV
    STF --> GF
    STF --> GP
    STF --> CFG
    
    GN --> LLM
    GN --> WC
    PP --> TAIWAN

    style API fill:#e3f2fd
    style FLASK fill:#e3f2fd
    style Application fill:#fff3e0
    style Search fill:#e8f5e8
    style Infrastructure fill:#fce4ec
```

### 模組依賴關係圖（單一流程）

```mermaid
graph LR
    subgraph Layer1["第一層 - API"]
        API[API Gateway]
    end

    subgraph Layer2["第二層 - 控制器"]
        CTRL[Flask Controller<br/>api_controller.py]
        CD[Core Dispatcher<br/>core_dispatcher.py]
    end

    subgraph Layer3["第三層 - 流程整合"]
        GB[generate_brief.py]
        LG[LangGraph<br/>company_brief_graph.py]
    end

    subgraph Layer4["第四層 - 領域節點"]
        SN[search_node]
        GN[generate_node]
        FN[finalize_node]
        PP[post_processing]
    end

    subgraph Layer5["第五層 - 基礎服務"]
        CDS[config_driven_search]
        LLM[llm_service]
        TAIWAN[taiwan_terms]
        WC[word_count_validator]
    end

    subgraph Layer6["第六層 - 外部服務"]
        TAVILY[Tavily API]
        GEMINI[Gemini API]
        OPENCC[OpenCC]
    end

    API --> CTRL
    CTRL --> CD
    CD --> GB
    GB --> LG
    LG --> SN
    LG --> GN
    LG --> FN
    GN --> PP
    SN --> CDS
    GN --> LLM
    GN --> WC
    PP --> TAIWAN
    CDS --> TAVILY
    CDS --> GEMINI
    LLM --> GEMINI
    TAIWAN --> OPENCC

    style Layer1 fill:#e3f2fd
    style Layer2 fill:#e3f2fd
    style Layer3 fill:#fff3e0
    style Layer4 fill:#e8f5e8
    style Layer5 fill:#f3e5f5
    style Layer6 fill:#fce4ec
```

    style Layer1 fill:#e1f5fe
    style Layer2 fill:#e1f5fe
    style Layer3 fill:#fff3e0
    style Layer4 fill:#e8f5e8
    style Layer5 fill:#f3e5f5
    style Layer6 fill:#fce4ec
```

### 搜尋工具層模組圖

```mermaid
graph TB
    subgraph ConfigLayer["配置層"]
        CFG[search_config.json<br/>provider: tavily]
    end

    subgraph Core["核心層"]
        CDS[ConfigDrivenSearchTool<br/>配置驅動工具]
        STF[SearchToolFactory<br/>工廠類]
        BASE[BaseSearchTool<br/>抽象基類]
    end

    subgraph Implementations["實作層"]
        TV[TavilyBatchSearchTool<br/>Tavily 批次搜尋]
        GF[GeminiFewShotSearchTool<br/>Gemini Few-shot]
        GP[GeminiPlannerTavilyTool<br/>Gemini 規劃 + Tavily]
    end

    subgraph Result["結果層"]
        SR[SearchResult<br/>統一結果格式]
    end

    subgraph External["外部服務"]
        TAVILY[Tavily API]
        GEMINI[Gemini API]
    end

    CFG -->|讀取配置| CDS
    CDS -->|創建| STF
    STF -->|註冊| BASE
    STF -->|工廠方法| TV
    STF -->|工廠方法| GF
    STF -->|工廠方法| GP
    
    TV -->|呼叫| TAVILY
    GF -->|呼叫| GEMINI
    GP -->|規劃| GEMINI
    GP -->|執行| TAVILY
    
    TV --> SR
    GF --> SR
    GP --> SR

    style ConfigLayer fill:#fff3e0
    style Core fill:#e3f2fd
    style Implementations fill:#e8f5e8
    style External fill:#fce4ec
    style Result fill:#f9f9f9
```

---

## 目錄結構

```
OrganBriefOptimization/
├── config/
│   └── search_config.json       # 搜尋策略配置（可切換 provider）
├── run_api.py                  # 本地開發入口腳本
├── serverless.yml              # Serverless 部署配置
├── requirements.txt            # Python 依賴
├── src/
│   ├── functions/              # API 核心邏輯
│   │   ├── api_controller.py   # Flask 路由控制器
│   │   └── utils/              # 工具函式
│   │       ├── generate_brief.py
│   │       ├── prompt_builder.py  # Prompt 建構（含三模板差異化）
│   │       ├── post_processing.py # 後處理（含台灣用語轉換）
│   │       └── word_count_validator.py # 字數檢核
│   ├── services/               # 商業邏輯服務
│   │   ├── llm_service.py
│   │   ├── tavily_search.py
│   │   ├── search_tools.py      # 搜尋工具層（工廠 + 工具類）⭐
│   │   └── config_driven_search.py # 配置驅動搜尋 ⭐
│   ├── langgraph_state/        # LangGraph 流程控制
│   │   ├── company_brief_graph.py  # 狀態圖定義
│   │   └── state.py            # 狀態定義
│   ├── schemas/                # Pydantic 資料模型
│   ├── plugins/                # 外掛模組
│   │   └── taiwan_terms/       # 台灣用語轉換外掛
│   └── config.py               # 組態配置
├── scripts/                    # 輔助腳本
│   └── stage3_test/           # 測試區
│       ├── search_tools.py    # 搜尋工具測試區
│       └── test_search_tools.py
└── tests/                     # 測試檔案
```

---

## 搜尋工具層

本系統支援透過配置文件切換不同的搜尋策略，實現配置驅動的搜尋體系。

### 支援的策略

| 策略 | 工具類別 | API 呼叫 | 特性 |
|------|----------|---------|------|
| `tavily` | TavilyBatchSearchTool | 1次 | 快速、自然語言 |
| `gemini_fewshot` | GeminiFewShotSearchTool | 1次 | 完整、JSON 格式 |
| `gemini_planner_tavily` | GeminiPlannerTavilyTool | 8次 | 彈性、<s tructured |

### 切換方式

修改 `config/search_config.json` 中的 `provider` 欄位：

```json
{
    "search": {
        "provider": "tavily"
    }
}
```

### 使用範例

```python
# 方式一：最簡單（推薦）- 自動根據配置執行
from src.services.config_driven_search import search
result = search("澳霸有限公司")

# 方式二：建立工具實例
from src.services.config_driven_search import ConfigDrivenSearchTool
tool = ConfigDrivenSearchTool()
result = tool.search("澳霸有限公司")

# 方式三：動態切換
tool = ConfigDrivenSearchTool()
tool.switch_provider("tavily")
result = tool.search("澳霸有限公司")
```

---

## 台灣用語轉換功能

本系統內建台灣用語轉換外掛模組，可自動將生成內容中的中國用語轉換為台灣用語。

### 特性

- **涵蓋 300+ 商業常用詞彙**：精選自 Taiwan.md 專案的關鍵詞彙
- **智能轉換**：同時處理簡體轉繁體與用語轉換
- **高效能**：處理時間 < 1ms，對整體系統影響極小
- **支援 HTML 與純文本**：可正確處理 HTML 標籤內的文字內容

### 使用範例

```python
from src.plugins.taiwan_terms import TaiwanTermsConverter

# 建立轉換器實例
converter = TaiwanTermsConverter()

# 轉換文本
result = converter.convert("今天天氣很好，我們使用U盤來存儲數據。")
print(result.text)
# 輸出："今天天氣很好，我們使用隨身碟來存儲資料。"
```

---

## 三模板差異化

本系統支援三種不同的輸出模式，透過 `optimization_mode` 參數控制：

| 模板 | 字數範圍 | 說明 |
|------|---------|------|
| `CONCISE` | 40-120 字 | 精簡模式，1-2 句話 |
| `STANDARD` | 130-230 字 | 標準模式，3-5 句話 |
| `DETAILED` | 280-550 字 | 詳細模式，5-10 句話 |

### API 使用方式

```json
{
  "organNo": "69188618",
  "organ": "私立揚才文理短期補習班",
  "mode": "GENERATE",
  "optimization_mode": "STANDARD"
}
```

---

## 本地開發

### 環境建置

```bash
# 建立虛擬環境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

# 安裝依賴
pip install -r requirements.txt
```

### 執行指令

```bash
# 啟動 Flask 伺服器
python run_api.py
```

伺服器預設運行於 `http://localhost:5000`

---

## API 使用方式

### 端點

```
POST /v1/company/profile/process
```

### 請求格式

```json
{
  "organNo": "69188618",
  "organ": "私立揚才文理短期補習班",
  "mode": "GENERATE",
  "optimization_mode": "STANDARD"
}
```

### curl 範例

```bash
curl -X POST http://localhost:5000/v1/company/profile/process \
  -H "Content-Type: application/json" \
  -d '{
    "organNo": "69188618",
    "organ": "私立揚才文理短期補習班",
    "mode": "GENERATE"
  }'
```

### 回應格式

```json
{
  "success": true,
  "data": {
    "title": "公司簡介標題",
    "summary": "簡介摘要",
    "body_html": "<p>HTML 格式的詳細內容</p>"
  }
}
```

---

## 環境變數

請參考 `.env.example` 檔案建立 `.env`，必要變數如下：

```
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
SERPER_API_KEY=your_serper_api_key
TAIWAN_TERMS_ENABLED=true  # 啟用台灣用語轉換
```

---

## 版本變動

### v0.0.2 - Phase 14 功能修復 (當前版本)

**日期**: 2026-04-13

#### 新增功能

| 功能 | 說明 |
|------|------|
| **搜尋工具層** | 配置驅動的搜尋策略切換體系 |
| **三模板差異化** | CONCISE / STANDARD / DETAILED 三種模式 |
| **字數限制優化** | Prompt 層控制 + 字數檢核 + LLM 重寫 |
| **台灣用語轉換** | 自動將中國用語轉換為台灣用語（300+ 詞彙） |

#### 架構變更

| 變更項目 | 說明 |
|----------|------|
| 新增 `search_tools.py` | 搜尋工具層核心（工廠 + 工具類） |
| 新增 `config_driven_search.py` | 配置驅動搜尋工具 |
| 新增 `config/search_config.json` | 搜尋策略配置文件 |
| 新增 `word_count_validator.py` | 字數檢核模組 |
| 更新 `company_brief_graph.py` | 使用新搜尋工具層 |
| 更新 `prompt_builder.py` | 三模板差異化 Prompt |
| 更新 `frontend/` | 移除 word_limit UI |

#### Phase 14 完成項目

| 階段 | 狀態 | 完成度 |
|------|------|--------|
| 階段一: 緊急修復 | ✅ 完成 | 100% |
| Checkpoint 1 | ✅ 通過 | 100% |
| 階段二: 核心功能 | ✅ 完成 | 100% |
| Stage 3: 搜尋工具層 | ✅ 完成 | 100% |

---

### v0.0.1 - Phase 12/13 基礎版本

**日期**: 2026-04-08

#### 基礎功能

| 功能 | 說明 |
|------|------|
| API 基礎架構 | Flask + Serverless |
| LLM 整合 | Google Gemini |
| 搜尋服務 | Serper API |
| 風險控制 | 敏感詞過濾 |
| LangGraph | 狀態管理系統 |

#### 存在的問題

| 問題 | 說明 |
|------|------|
| 字數限制不精確 | 內容超出限制 |
| 模板無差異化 | 三種模式輸出相同 |
| 冗言過多 | LLM 生成多餘的開頭語 |
| 中國用語 | 未轉換為台灣用語 |

---