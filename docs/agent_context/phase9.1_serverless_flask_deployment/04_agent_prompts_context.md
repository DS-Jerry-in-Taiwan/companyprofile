# Phase 9.1 Developer Agent Prompt

## 系統提示

你是一個專業的 AWS Lambda 部署工程師，負責將 Flask 應用程式部署至 AWS Lambda 環境。

---

## 任務目標

將現有的 Flask API（`src/functions/api_controller.py`）整合至 AWS Lambda，實現 Serverless 部署。

---

## 技術背景

### 現有架構（Lambda 原生）
```
ALB → optimize_handler.py → Bedrock
```
- 只能處理單一端點
- 沒有監控、日誌端點

### 目標架構（Flask + Mangum）
```
ALB → Mangum → Flask App → Bedrock
        └── /v1/company/profile/process
        └── /v1/monitoring/logs
        └── /v1/monitoring/anomalies
        └── /health
```
- 多端點支援
- 完整 REST API
- 結構化日誌

---

## 你的任務

### 任務 1：更新 requirements.txt

**目標**：在 `src/functions/requirements.txt` 加入 Flask + Mangum 依賴

**操作**：
```
將 src/functions/requirements.txt 的內容替換為：

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

**驗證命令**：
```bash
cd src/functions
pip install -r requirements.txt
python -c "from flask import Flask; from mangum import Mangum; print('OK')"
```

---

### 任務 2：建立 Lambda 入口適配器

**目標**：建立 `src/functions/lambda_handler.py`

**操作**：
```
在 src/functions/lambda_handler.py 建立以下程式碼：

"""
Lambda 入口點 - 使用 Mangum 將 Flask 應用程式轉換為 Lambda 相容
"""
import os
from mangum import Mangum
from api_controller import app as flask_app

# 設定 Flask 環境
os.environ.setdefault('FLASK_ENV', 'production')

# 建立 Lambda 處理函數
handler = Mangum(flask_app, debug=False, lifespan=False)
```

**驗證命令**：
```bash
python -c "from lambda_handler import handler; print('Handler loaded:', type(handler).__name__)"
```

---

### 任務 3：建立 Dockerfile.prod

**目標**：建立 `src/functions/Dockerfile.prod`

**操作**：
```
在 src/functions/Dockerfile.prod 建立以下內容：

FROM public.ecr.aws/lambda/python:3.11

# 複製需求檔案
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --no-cache-dir

# 複製應用程式碼
COPY api_controller.py ${LAMBDA_TASK_ROOT}
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/

# 設定環境變數
ENV PYTHONUNBUFFERED=1

# 設定 Lambda 入口點
CMD ["lambda_handler.handler"]
```

**驗證命令**：
```bash
cd src/functions
docker build -f Dockerfile.prod -t organ-brief:test .
docker run -d -p 9000:8080 organ-brief:test
sleep 5
curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -d '{"resource":"/health","httpMethod":"GET"}'
```

---

### 任務 4：更新 serverless.yml

**目標**：更新根目錄的 `serverless.yml`

**操作**：
```
確保 functions 區段如下：

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

確保 provider 區段包含環境變數：
```yaml
provider:
  environment:
    STAGE: ${self:provider.stage}
    BEDROCK_REGION: ap-northeast-1
    CLAUDE_MODEL_ID: anthropic.claude-3-5-sonnet-20240620-v1:0
    CORS_ORIGINS: ${env:CORS_ORIGINS, '*'}
```

**驗證命令**：
```bash
serverless print --stage dev
```

---

### 任務 5：本地測試驗證

**目標**：確保所有端點正常運作

**操作**：
```bash
# 測試健康檢查
curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -d '{"resource":"/health","httpMethod":"GET"}'

# 測試 API 端點
curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -d '{"resource":"/v1/company/profile/process","httpMethod":"POST","body":"{\"organNo\":\"123\",\"organ\":\"Test\"}"'
```

**預期結果**：
- /health 回應：{"status": "healthy", ...}
- /v1/company/profile/process 回應：JSON 格式（success 或 error）

---

### 任務 6：部署至 AWS

**目標**：將服務部署至 AWS

**操作**：
```bash
# 1. 登入 AWS
aws sso login --profile your-profile

# 2. 推送 Docker 映像至 ECR
cd src/functions
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.ap-northeast-1.amazonaws.com

docker tag organ-brief:test $ACCOUNT_ID.dkr.ecr.ap-northeast-1.amazonaws.com/organ-brief-optimization:prod
docker push $ACCOUNT_ID.dkr.ecr.ap-northeast-1.amazonaws.com/organ-brief-optimization:prod

# 3. 部署 Serverless
serverless deploy --stage prod

# 4. 測試
API_URL=$(aws apigatewayv2 get-apis --region ap-northeast-1 --query 'Items[0].ApiEndpoint' --output text)
curl $API_URL/health
curl -X POST $API_URL/v1/company/profile/process \
  -H "Content-Type: application/json" \
  -d '{"organNo":"123","organ":"Test","mode":"GENERATE"}'
```

---

## 錯誤處理指引

### 常見問題與解決方案

| 問題 | 可能原因 | 解決方案 |
|------|----------|----------|
| ImportError: No module named 'flask' | requirements.txt 未更新 | 確認 requirements.txt 包含 Flask |
| Mangum 初始化失敗 | Flask app 匯入錯誤 | 檢查 api_controller.py 是否正確 |
| Docker 建置失敗 | 基礎映像或 CMD 錯誤 | 確認 Dockerfile.prod 語法正確 |
| CORS 錯誤 | CORS_ORIGINS 未設定 | 在 serverless.yml 設定環境變數 |
| Lambda 超時 | 函數執行時間過長 | 增加 timeout 或優化程式碼 |

---

## 交付要求

完成每個任務後，請更新 `docs/agent_context/phase9.1_serverless_flask_deployment/06_delivery_record.md` 中的狀態。

### 需交付的檔案

| 檔案 | 說明 |
|------|------|
| `src/functions/requirements.txt` | 更新的依賴檔案 |
| `src/functions/lambda_handler.py` | Lambda 入口適配器 |
| `src/functions/Dockerfile.prod` | 生產環境 Docker 映像 |
| `serverless.yml` | 更新後的配置 |

---

## 執行順序

請按照以下順序執行任務：

1. **任務 1**：更新 requirements.txt
2. **任務 2**：建立 lambda_handler.py
3. **任務 3**：建立 Dockerfile.prod
4. **任務 4**：更新 serverless.yml
5. **任務 5**：本地測試驗證
6. **任務 6**：部署至 AWS

每個任務完成後，請執行驗證命令確認成功，再進行下一個任務。

---

*Prompt 完成*
- 建立日期：2026-04-01
- 專案階段：Phase 9.1 Serverless Flask 部署
- Agent 類型：Developer Agent
