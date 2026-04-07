# 公司簡介生成與優化 API

這是一個採用 Serverless 架構的公司簡介生成與優化服務，部署於 AWS Lambda + API Gateway，提供 RESTful API 介面，支援從無到有生成公司簡介，以及優化現有的公司簡介內容。

## 功能特色

### 作業模式

| 模式 | 說明 |
|------|------|
| **GENERATE** | 根據輸入的公司名稱與統一編號，從網路爬取相關資訊，並由 LLM 生成專業的公司簡介 |

### 核心能力

- 自動化資料蒐集：透過 Serper API 搜尋公司相關資訊
- LLM 整合：採用 Google Gemini 生成高品質內容
- 風險控制：內建敏感詞過濾與內容安全檢核
- Token 成本管理：記錄並追蹤 API 呼叫費用

## 技術堆疊

- **Web Framework**：Flask
- **LLM**：Google Gemini (generativeai)
- **Web Search**：Serper API
- **Data Validation**：Pydantic
- **Deployment**：Serverless Framework (AWS Lambda + API Gateway)
- **Testing**：Pytest

## 本地開發

### 環境建置

```bash
# 建立虛擬環境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 安裝依賴
pip install -r requirements.txt
```

### 執行指令

```bash
# 啟動 Flask 伺服器
python run_api.py
```

伺服器預設運行於 `http://localhost:5000`

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
  "mode": "GENERATE"
}
```

### curl 範例

**GENERATE 模式**（生成新簡介）：

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

## 目錄結構

```
OrganBriefOptimization/
├── run_api.py              # 本地開發入口腳本
├── serverless.yml          # Serverless 部署配置
├── requirements.txt        # Python 依賴
├── src/
│   ├── functions/          # API 核心邏輯
│   │   ├── api_controller.py    # Flask 路由控制器
│   │   └── utils/           # 工具函式
│   │       ├── generate_brief.py
│   │       ├── optimize_brief.py
│   │       ├── llm_handler.py
│   │       └── ...
│   ├── services/           # 商業邏輯服務
│   │       ├── llm_service.py
│   │       ├── serper_search.py
│   │       ├── risk_control_service.py
│   │       └── ...
│   ├── schemas/            # Pydantic 資料模型
│   └── config.py           # 組態配置
├── scripts/                # 輔助腳本
│   ├── batch_test.py
│   ├── token_cost_logger.py
│   └── ...
└── tests/                  # 測試檔案
```

## 環境變數

請參考 `.env.example` 檔案建立 `.env`，必要變數如下：

```
GEMINI_API_KEY=your_gemini_api_key
SERPER_API_KEY=your_serper_api_key
```

## 授權

本專案僅供內部使用。
