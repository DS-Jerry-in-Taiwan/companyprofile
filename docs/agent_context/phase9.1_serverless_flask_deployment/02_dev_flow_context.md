# Phase 9.1 開發流程與時程

## 一、開發流程

### 1.1 流程總覽

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  準備階段   │ -> │  實作階段   │ -> │  測試階段   │ -> │  部署階段   │
│   (Task 1)  │    │  (Task 2-5) │    │  (Task 6)   │    │  (Task 7)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 1.2 階段說明

| 階段 | 主要工作 | 預估工時 |
|------|----------|----------|
| 準備階段 | 現況分析、依賴盤點 | 2 小時 |
| 實作階段 | Flask 包裝、Dockerfile、Serverless 配置 | 8 小時 |
| 測試階段 | 本地測試、部署測試 | 4 小時 |
| 部署階段 | 正式部署、驗證 | 2 小時 |

---

## 二、工項拆解

### 2.1 任務總覽

| 任務編號 | 任務名稱 | 預估工時 | 依賴關係 | 狀態 |
|----------|----------|----------|----------|------|
| T9.1.0 | 現況分析與差異評估 | 2 小時 | Phase 10 完成 | ⬜ 待開發 |
| T9.1.1 | 更新 requirements.txt | 1 小時 | T9.1.0 完成 | ⬜ 待開發 |
| T9.1.2 | 建立 Lambda 入口適配器 | 2 小時 | T9.1.1 完成 | ⬜ 待開發 |
| T9.1.3 | 建立 Dockerfile.prod | 2 小時 | T9.1.2 完成 | ⬜ 待開發 |
| T9.1.4 | 更新 serverless.yml | 1 小時 | T9.1.3 完成 | ⬜ 待開發 |
| T9.1.5 | 本地測試驗證 | 2 小時 | T9.1.4 完成 | ⬜ 待開發 |
| T9.1.6 | 部署至測試環境 | 2 小時 | T9.1.5 完成 | ⬜ 待開發 |

---

### 2.2 任務 T9.1.0：現況分析與差異評估

#### 2.2.1 現有架構分析

| 項目 | Lambda 原生 | Flask + Mangum | 差異說明 |
|------|-------------|----------------|----------|
| 入口函數 | `optimize_handler.py` | 需要新建立 | 需建立 Mangum 適配器 |
| 端點數量 | 1 個 | 4+ 個 | Flask 路由能力 |
| 事件解析 | 手動解析 ALB event | Mangum 自動處理 | Mangum 提供轉換 |
| 回應格式 | 手動組合 | Flask jsonify | Flask 自動處理 |
| 依賴套件 | boto3, botocore | + Flask, Mangum | 需要更新 |

#### 2.2.2 需要修改的檔案

| 檔案 | 動作 | 說明 |
|------|------|------|
| `src/functions/requirements.txt` | 修改 | 加入 Flask + Mangum |
| `src/functions/lambda_handler.py` | 新建 | Lambda 入口點（Mangum 適配） |
| `src/functions/Dockerfile.prod` | 新建 | 生產環境 Dockerfile |
| `serverless.yml` | 修改 | 更新函數配置 |

---

### 2.3 任務 T9.1.1：更新 requirements.txt

#### 2.3.1 子任務拆解

| 子任務 | 說明 | 輸入 | 輸出 |
|--------|------|------|------|
| T9.1.1.1 | 備份現有 requirements.txt | 現有檔案 | backup |
| T9.1.1.2 | 加入 Flask 相關依賴 | - | 更新後的 requirements.txt |
| T9.1.1.3 | 加入 Mangum 適配器 | - | 更新後的 requirements.txt |
| T9.1.1.4 | 加入驗證與日誌相關 | - | 更新後的 requirements.txt |

#### 2.3.2 新增依賴說明

```txt
# Lambda 部署依賴
boto3>=1.37.11
botocore>=1.37.11

# Flask API 依賴
flask>=3.1.0
flask-cors>=5.0.0

# Lambda 適配器
mangum>=0.17.0

# 驗證與錯誤處理
pydantic>=2.10.0

# 結構化日誌
python-dotenv>=1.0.1
```

---

### 2.4 任務 T9.1.2：建立 Lambda 入口適配器

#### 2.4.1 子任務拆解

| 子任務 | 說明 | 輸入 | 輸出 |
|--------|------|------|------|
| T9.1.2.1 | 建立 lambda_handler.py | Mangum 文件 | `src/functions/lambda_handler.py` |
| T9.1.2.2 | 匯入 Flask app | api_controller.py | 整合程式碼 |
| T9.1.2.3 | 配置 Mangum 適配器 | Flask app | 整合程式碼 |
| T9.1.2.4 | 設定環境變數處理 | - | 整合程式碼 |

#### 2.4.2 程式碼範例

```python
# lambda_handler.py
from mangum import Mangum
from api_controller import app as flask_app

# 建立 Lambda 適配器
handler = Mangum(flask_app, debug=False)
```

---

### 2.5 任務 T9.1.3：建立 Dockerfile.prod

#### 2.5.1 子任務拆解

| 子任務 | 說明 | 輸入 | 輸出 |
|--------|------|------|------|
| T9.1.3.1 | 參考 Dockerfile.dev | 現有 Dockerfile | 基礎結構 |
| T9.1.3.2 | 修改基礎映像 | Python 3.11 | 更新後的 Dockerfile |
| T9.1.3.3 | 加入所有依賴 | requirements.txt | 更新後的 Dockerfile |
| T9.1.3.4 | 設定 Lambda 入口 | lambda_handler | 更新後的 Dockerfile |

#### 2.5.2 Dockerfile.prod 範例

```dockerfile
FROM public.ecr.aws/lambda/python:3.11

# 複製需求檔案
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --no-cache-dir

# 複製應用程式碼
COPY api_controller.py ${LAMBDA_TASK_ROOT}
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}

# 設定入口點
CMD ["lambda_handler.handler"]
```

---

### 2.6 任務 T9.1.4：更新 serverless.yml

#### 2.6.1 子任務拆解

| 子任務 | 說明 | 輸入 | 輸出 |
|--------|------|------|------|
| T9.1.4.1 | 更新函數配置 | 現有 serverless.yml | 更新後的 serverless.yml |
| T9.1.4.2 | 配置 CORS | - | 更新後的 serverless.yml |
| T9.1.4.3 | 設定環境變數 | 現有配置 | 更新後的 serverless.yml |

#### 2.6.2 更新的 serverless.yml 範例

```yaml
functions:
  api:
    image: 
      name: optimizationImg
    memorySize: 1024
    timeout: 60
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors: true
      - http:
          path: /
          method: ANY
          cors: true
```

---

### 2.7 任務 T9.1.5：本地測試驗證

#### 2.7.1 子任務拆解

| 子任務 | 說明 | 輸入 | 輸出 |
|--------|------|------|------|
| T9.1.5.1 | 建置 Docker 映像 | Dockerfile.prod | Docker 映像 |
| T9.1.5.2 | 本地 Lambda 模擬測試 | SAM CLI / Docker | 測試結果 |
| T9.1.5.3 | 測試 API 端點 | curl | 測試結果 |
| T9.1.5.4 | 測試 CORS | - | 測試結果 |

#### 2.7.2 測試清單

```bash
# 健康檢查
curl -X GET http://localhost:9000/2015-03-31/functions/function/invocations -d '{"resource":"/health","httpMethod":"GET"}'

# API 端點測試
curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -d '{"resource":"/v1/company/profile/process","httpMethod":"POST","body":"{\"organNo\":\"123\",\"organ\":\"Test\"}"}'
```

---

### 2.8 任務 T9.1.6：部署至測試環境

#### 2.8.1 子任務拆解

| 子任務 | 說明 | 輸入 | 輸出 |
|--------|------|------|------|
| T9.1.6.1 | 部署至 AWS | serverless deploy | 部署結果 |
| T9.1.6.2 | 驗證 Lambda 函數 | AWS Console | 驗證結果 |
| T9.1.6.3 | 測試 API 端點 | curl | 測試結果 |
| T9.1.6.4 | 檢查 CloudWatch 日誌 | CloudWatch | 日誌正常 |

---

## 三、驗證檢查清單

### 3.1 功能驗證

- [ ] T9.1.1：requirements.txt 包含所有必要依賴
- [ ] T9.1.2：Lambda 入口點可正確匯入 Flask app
- [ ] T9.1.3：Dockerfile.prod 可成功建置
- [ ] T9.1.4：serverless.yml 配置正確
- [ ] T9.1.5：本地測試所有端點正常
- [ ] T9.1.6：部署後端點正常運作

### 3.2 整合驗證

- [ ] Flask app 可正確處理 Lambda 事件
- [ ] Mangum 適配器正確轉換請求/回應
- [ ] CORS 配置正確，前端可調用
- [ ] 結構化日誌正常運作

### 3.3 部署驗證

- [ ] Docker 映像可推送至 ECR
- [ ] Serverless 部署成功
- [ ] Lambda 函數可被觸發
- [ ] CloudWatch 日誌正確寫入

---

## 四、風險與緩解

| 風險 | 發生機率 | 影響程度 | 緩解措施 |
|------|----------|----------|----------|
| Mangum 版本相容性 | 低 | 中 | 鎖定版本，測試驗證 |
| Flask 與 Lambda 事件格式差異 | 中 | 高 | 充分測試各種場景 |
| Docker 建置失敗 | 低 | 高 | 本地先驗證 |
| CORS 問題 | 中 | 高 | 提前配置測試 |

---

*文件資訊*
- 建立日期：2026-04-01
- 專案階段：Phase 9.1 Serverless Flask 部署
- 文檔類型：開發流程與時程
