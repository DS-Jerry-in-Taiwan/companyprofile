# 後端部署規劃

## 概述

後端使用 **AWS Lambda** + **API Gateway**（或現有 ALB）部署，採用 Docker 容器映像方式。

---

## 架構組件

### 1. AWS Lambda

| 項目 | 設定 |
|------|------|
| Runtime | Python 3.11 |
| 記憶體 | 1024 MB |
| 超時 | 60 秒 |
| 部署方式 | Docker 容器映像（ECR） |

### 2. API Gateway / ALB

目前使用 ALB（Application Load Balancer），可選擇：
- **方案 A**：維持 ALB（適合已有基礎設施）
- **方案 B**：改用 API Gateway（適合 Serverless 原生）

---

## API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/v1/company/profile/process` | 公司簡介生成 |
| GET | `/v1/monitoring/logs` | 日誌查詢 |
| GET | `/v1/monitoring/anomalies` | 異常統計 |
| GET | `/health` | 健康檢查 |

---

## Serverless 配置

### serverless.yml

```yaml
service: organ-brief-optimization

provider:
  name: aws
  runtime: python3.11
  region: ap-northeast-1
  stage: ${opt:stage, 'dev'}
  environment:
    STAGE: ${self:provider.stage}
    LOG_LEVEL: ${self:custom.logLevel.${self:provider.stage}, 'INFO'}
    # CORS 設定
    CORS_ORIGINS: ${env:CORS_ORIGINS, '*'}
  
  ecr:
    images:
      flaskApiImg:
        path: ./src/functions
        file: Dockerfile.${self:provider.stage}
        buildArgs:
          STAGE: ${self:provider.stage}
  
  iamRoleStatements:
    - Effect: Allow
      Action:
        - logs:CreateLogGroup
        - logs:CreateLogStream
        - logs:PutLogEvents
      Resource: "arn:aws:logs:${self:provider.region}:*:*"

functions:
  flaskApi:
    image: 
      name: flaskApiImg
    memorySize: 1024
    timeout: 60
    events:
      - httpApi:
          path: /{proxy+}
          method: ANY
      - httpApi:
          path: /
          method: ANY
```

---

## CORS 配置

### Flask 端（api_controller.py）

需要在 Flask 應用中加入 CORS 支援：

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": os.environ.get('CORS_ORIGINS', '*').split(','),
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

### API Gateway 端

```yaml
cors:
  origin: '*'
  headers:
    - Content-Type
    - Authorization
  methods:
    - GET
    - POST
    - OPTIONS
```

---

## Dockerfile

### src/functions/Dockerfile.prod

```dockerfile
FROM public.ecr.aws/lambda/python:3.11

# 複製需求檔案
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# 複製應用程式碼
COPY . ${LAMBDA_TASK_ROOT}

# 設定入口點
CMD ["lambda_handler.handler"]
```

---

## 部署步驟
## AWS MFA 臨時金鑰

為了啟用後端部署使用 AWS MFA 臨時金鑰，請按照以下步驟操作:

1. 在您的 AWS 帳戶中設定要求 MFA 進行管理操作。
2. 獲取 MFA 設備並將其與您的 AWS IAM 使用者相關聯。
3. 更新部署腳本以使用 aws sts get-session-token 命令，傳遞您的 MFA 設備代碼以獲取臨時憑證。
4. 在部署環境中設定 AWS CLI 配置以使用臨時憑證:
      aws configure set aws_access_key_id TEMPORARY_ACCESS_KEY_ID
      aws configure set aws_secret_access_key TEMPORARY_SECRET_ACCESS_KEY
      aws configure set aws_session_token TEMPORARY_SESSION_TOKEN
   5. 使用已配置的 AWS 臨時憑證執行部署步驟:
      cd src/functions
      docker build -f Dockerfile.prod -t organ-brief-optimization:latest .
      docker push ACCOUNT_ID.dkr.ecr.ap-northeast-1.amazonaws.com/organ-brief-optimization:latest
      serverless deploy --stage prod
   6. 確保部署過程能夠使用臨時憑證成功驗證和部署。

### 1. 建置 Docker 映像

```bash
cd src/functions
docker build -f Dockerfile.prod -t organ-brief-optimization:v0.0.1 .
```

### 2. 推送至 ECR

```bash
# 登入 ECR
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.ap-northeast-1.amazonaws.com

# 標記並推送
docker tag organ-brief-optimization:v0.0.1 ACCOUNT_ID.dkr.ecr.ap-northeast-1.amazonaws.com/organ-brief-optimization:v0.0.1
docker push ACCOUNT_ID.dkr.ecr.ap-northeast-1.amazonaws.com/organ-brief-optimization:v0.0.1
```

### 3. 部署 Lambda

```bash
cd src/functions
serverless deploy --stage prod
```

---

## 監控與日誌

### CloudWatch Logs

- Lambda 日誌自動存入 CloudWatch
- 日誌群組：`/aws/lambda/organ-brief-optimization-prod-optimizeOrganBrief`

### CloudWatch Metrics

- Invocations
- Duration
- Error count
- Throttles

---

## 注意事項

1. **冷啟動**：Docker 容器映像可能有較長冷啟動時間，考慮使用 Provisioned Concurrency
2. **超時設定**：LLM 呼叫可能較慢，建議設定 60 秒超時
3. **記憶體**：確保足夠記憶體處理併發請求
4. **LLM 服務**：使用 Google Gemini API（需設定 GEMINI_API_KEY 環境變數）
