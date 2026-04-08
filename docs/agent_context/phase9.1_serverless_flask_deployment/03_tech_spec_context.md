# Phase 9.1 技術角色與分工

## 一、角色定義

### 1.1 技術架構

本階段不涉及 Agent 角色，採用傳統開發方式進行實作。

| 角色 | 負責人員 | 職責 |
|------|----------|------|
| 開發工程師 | Agent-Developer | 實作 Lambda 入口適配器與相關配置 |
| 架構師 | Architect-Agent | 審核架構設計與技術決策 |
| 測試工程師 | - | 本地與部署後測試驗證 |

---

## 二、技術規格

### 2.1 技術堆疊

| 層級 | 技術 | 版本需求 |
|------|------|----------|
| 執行環境 | AWS Lambda | - |
| 基礎映像 | public.ecr.aws/lambda/python | 3.11 |
| Web 框架 | Flask | >= 3.1.0 |
| Lambda 適配器 | Mangum | >= 0.17.0 |
| 部署工具 | Serverless Framework | >= 3.0 |
| 容器化 | Docker | 最新穩定版 |

### 2.2 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway / ALB                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       AWS Lambda                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Mangum 適配器                       │   │
│  │  ┌───────────────────────────────────────────────┐   │   │
│  │  │               Flask 應用程式                   │   │   │
│  │  │  ├── /v1/company/profile/process             │   │   │
│  │  │  ├── /v1/monitoring/logs                    │   │   │
│  │  │  ├── /v1/monitoring/anomalies               │   │   │
│  │  │  └── /health                                 │   │   │
│  │  └───────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       AWS Services                           │
│  ├── Bedrock (Claude)                                       │
│  ├── CloudWatch Logs                                        │
│  └── ECR (Container Registry)                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、檔案結構

### 3.1 需修改的檔案

| 檔案路徑 | 動作 | 說明 |
|----------|------|------|
| `src/functions/requirements.txt` | 修改 | 加入 Flask + Mangum 依賴 |
| `src/functions/lambda_handler.py` | 新建 | Lambda 入口點（Mangum 適配） |
| `src/functions/Dockerfile.prod` | 新建 | 生產環境 Docker 映像 |
| `serverless.yml` | 修改 | 更新函數配置與環境變數 |

### 3.2 檔案依賴關係

```
requirements.txt
    │
    ▼
lambda_handler.py  ──►  api_controller.py
    │
    ▼
Dockerfile.prod  ──►  lambda_handler.py
    │
    ▼
serverless.yml  ──►  Dockerfile.prod
```

---

## 四、環境變數

### 4.1 Lambda 環境變數

| 變數名稱 | 說明 | 範例值 |
|----------|------|--------|
| `STAGE` | 部署階段 | `dev`, `prod` |
| `BEDROCK_REGION` | Bedrock 區域 | `ap-northeast-1` |
| `CLAUDE_MODEL_ID` | Claude 模型 ID | `anthropic.claude-3-5-sonnet-20240620-v1:0` |
| `CORS_ORIGINS` | 允許的來源 | `https://example.com` |

### 4.2 本地開發變數

```env
# .env.local
FLASK_APP=api_controller.py
FLASK_ENV=development
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

## 五、API 端點說明

### 5.1 現有端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/v1/company/profile/process` | 公司簡介生成/優化 |
| GET | `/v1/monitoring/logs` | 日誌查詢（需參數） |
| GET | `/v1/monitoring/anomalies` | 異常統計 |
| GET | `/health` | 健康檢查 |

### 5.2 回應格式

#### 成功回應

```json
{
  "status": "success",
  "data": { ... },
  "request_id": "req-xxx"
}
```

#### 錯誤回應

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "錯誤訊息"
  },
  "request_id": "req-xxx"
}
```

---

*文件資訊*
- 建立日期：2026-04-01
- 專案階段：Phase 9.1 Serverless Flask 部署
- 文檔類型：技術角色與分工
