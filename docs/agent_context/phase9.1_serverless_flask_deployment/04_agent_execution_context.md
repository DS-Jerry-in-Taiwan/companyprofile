# Phase 9.1 Developer Agent 執行指令

## 一、任務概述

### 1.1 目標

將現有的 Flask API 應用程式（api_controller.py）整合至 AWS Lambda 環境，實現 Serverless 部署。

### 1.2 成功標準

| 標準 | 說明 |
|------|------|
| Flask Lambda 化 | Mangum 適配器正確運作 |
| 多端點部署 | 4 個 API 端點都可訪問 |
| CORS 配置 | 前端可正常調用 API |
| Docker 部署 | 容器映像可成功建置 |

---

## 二、執行指令

### 2.1 任務 T9.1.1：更新 requirements.txt

**指令**：
```
更新 src/functions/requirements.txt，加入以下依賴：

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

**驗證**：
```bash
cd src/functions
pip install -r requirements.txt
python -c "from flask import Flask; from mangum import Mangum; print('OK')"
```

---

### 2.2 任務 T9.1.2：建立 Lambda 入口適配器

**指令**：
```
在 src/functions/lambda_handler.py 建立以下程式碼：

```python
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
```

**驗證**：
```bash
python -c "from lambda_handler import handler; print('Handler loaded:', type(handler))"
```

---

### 2.3 任務 T9.1.3：建立 Dockerfile.prod

**指令**：
```
在 src/functions/Dockerfile.prod 建立以下內容：

```dockerfile
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
```

**驗證**：
```bash
cd src/functions
docker build -f Dockerfile.prod -t organ-brief:test .
docker run -p 9000:8080 organ-brief:test &
sleep 3
curl http://localhost:9000/2015-03-31/functions/function/invocations -d '{"resource":"/health","httpMethod":"GET"}'
```

---

### 2.4 任務 T9.1.4：更新 serverless.yml

**指令**：
```
更新 serverless.yml 的 functions 區段：

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

確保 provider 區段包含環境變數：
```yaml
provider:
  environment:
    STAGE: ${self:provider.stage}
    BEDROCK_REGION: ap-northeast-1
    CLAUDE_MODEL_ID: anthropic.claude-3-5-sonnet-20240620-v1:0
    CORS_ORIGINS: ${env:CORS_ORIGINS, '*'}
```
```

**驗證**：
```bash
cd src/functions
serverless print --stage dev 2>&1 | head -50
```

---

### 2.5 任務 T9.1.5：本地測試驗證

**指令**：
```
執行以下測試：

1. Docker 本地測試：
```bash
cd src/functions
docker build -f Dockerfile.prod -t organ-brief:test .
docker run -p 9000:8080 organ-brief:test &
sleep 5

# 測試健康檢查
curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -d '{"resource":"/health","httpMethod":"GET"}'

# 測試 API 端點
curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -d '{"resource":"/v1/company/profile/process","httpMethod":"POST","body":"{\"organNo\":\"123\"}"'
```

2. 預期結果：
- /health 回應：{"status": "healthy", ...}
- /v1/company/profile/process 回應：包含 success 或 error 的 JSON
```

---

### 2.6 任務 T9.1.6：部署至 AWS

**指令**：
```
1. 登入 AWS：
```bash
aws sso login --profile your-profile
```

2. 推送 Docker 映像至 ECR：
```bash
cd src/functions
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.ap-northeast-1.amazonaws.com

docker tag organ-brief:test $ACCOUNT_ID.dkr.ecr.ap-northeast-1.amazonaws.com/organ-brief-optimization:prod
docker push $ACCOUNT_ID.dkr.ecr.ap-northeast-1.amazonaws.com/organ-brief-optimization:prod
```

3. 部署 Serverless：
```bash
cd src/functions
serverless deploy --stage prod
```

4. 取得 API URL 並測試：
```bash
API_URL=$(aws apigatewayv2 get-apis --region ap-northeast-1 --query 'Items[0].ApiEndpoint' --output text)
echo "API URL: $API_URL"

# 健康檢查
curl $API_URL/health

# API 測試
curl -X POST $API_URL/v1/company/profile/process \
  -H "Content-Type: application/json" \
  -d '{"organNo":"123","organ":"Test","mode":"GENERATE"}'
```

5. 檢查 CloudWatch 日誌：
```bash
aws logs tail /aws/lambda/organ-brief-optimization-prod-api --follow
```
```

---

## 三、錯誤處理指引

### 3.1 常見問題與解決方案

| 問題 | 可能原因 | 解決方案 |
|------|----------|----------|
| ImportError: No module named 'flask' | requirements.txt 未更新 | 確認 requirements.txt 包含 Flask |
| Mangum 初始化失敗 | Flask app 匯入錯誤 | 檢查 api_controller.py 是否正確 |
| Docker 建置失敗 | 基礎映像或 CMD 錯誤 | 確認 Dockerfile.prod 語法正確 |
| CORS 錯誤 | CORS_ORIGINS 未設定 | 在 serverless.yml 設定環境變數 |
| Lambda 超時 | 函數執行時間過長 | 增加 timeout 或優化程式碼 |

### 3.2 除錯命令

```bash
# 本地除錯
cd src/functions
python -c "from api_controller import app; app.run()"

# Docker 日誌
docker logs <container_id>

# Lambda 日誌
aws logs filter-log-events --log-group-name /aws/lambda/your-function --filter-pattern ERROR
```

---

## 四、驗證檢查清單

### 4.1 功能檢查

- [ ] requirements.txt 包含所有必要依賴
- [ ] lambda_handler.py 可正確匯入
- [ ] Dockerfile.prod 可成功建置
- [ ] serverless.yml 配置正確

### 4.2 API 端點檢查

- [ ] GET /health 回應 200
- [ ] POST /v1/company/profile/process 可處理請求
- [ ] GET /v1/monitoring/logs 可訪問
- [ ] GET /v1/monitoring/anomalies 可訪問

### 4.3 CORS 檢查

- [ ] OPTIONS 請求正確處理
- [ ] 回應包含 Access-Control-Allow-Origin

---

## 五、交付產出

完成所有任務後，請交付以下檔案：

| 檔案 | 說明 |
|------|------|
| `src/functions/requirements.txt` | 更新的依賴檔案 |
| `src/functions/lambda_handler.py` | Lambda 入口適配器 |
| `src/functions/Dockerfile.prod` | 生產環境 Docker 映像 |
| `serverless.yml` | 更新後的配置 |

請完成每個任務後，在 [06_delivery_record.md](./06_delivery_record.md) 中記錄狀態。
