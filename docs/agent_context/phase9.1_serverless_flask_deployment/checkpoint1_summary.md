# Phase 9.1 Checkpoint 1 - 程式碼變更總結

## 執行日期
2026-04-01

## 執行狀態
✅ **T9.1.1 - T9.1.4 已完成，等待 Checkpoint 1 確認**

---

## 已完成的任務

### ✅ T9.1.1: 更新 requirements.txt
**狀態**: 已存在，無需修改
- Flask >= 3.1.0 ✓
- Mangum >= 0.17.0 ✓
- boto3 >= 1.37.11 ✓
- 其他依賴完整 ✓

### ✅ T9.1.2: 建立 lambda_handler.py
**檔案**: `src/functions/lambda_handler.py`
**內容**:
```python
from mangum import Mangum
from api_controller import app

handler = Mangum(app, lifespan="off")
```
**說明**: Mangum 適配器將 Flask app 包裝為 Lambda 相容的處理函數

### ✅ T9.1.3: 建立 Dockerfile.prod
**檔案**: `src/functions/Dockerfile.prod`
**關鍵配置**:
- 基礎映像: `public.ecr.aws/lambda/python:3.11`
- 入口點: `CMD ["lambda_handler.handler"]`
- 複製檔案: lambda_handler.py, api_controller.py, utils/
- 環境變數: STAGE, PYTHONUNBUFFERED

### ✅ T9.1.4: 更新 serverless.yml
**主要變更**:

#### 1. Provider 配置
- 新增環境變數: `LOG_LEVEL` (dev=DEBUG, prod=INFO)
- 新增 IAM 權限: CloudWatch Logs 寫入權限
- ECR 映像重命名: `optimizationImg` → `flaskApiImg`

#### 2. Custom 配置（新增）
```yaml
custom:
  logLevel:
    dev: DEBUG
    prod: INFO
```

#### 3. Functions 配置
**變更前**:
```yaml
functions:
  optimizeOrganBrief:
    image: optimizationImg
    events:
      - alb:
          listenerArn: arn:aws:elasticloadbalancing:...
          priority: 99
          conditions:
            path: /optimize_organ_brief
```

**變更後**:
```yaml
functions:
  flaskApi:
    image: flaskApiImg
    events:
      - httpApi:
          path: /{proxy+}
          method: ANY
      - httpApi:
          path: /
          method: ANY
```

**影響**:
- ❌ 移除 ALB 事件觸發器
- ✅ 新增 HTTP API Gateway 觸發器
- ✅ 支援所有 HTTP 方法和路徑（/{proxy+}）
- ✅ 支援根路徑 (/)

---

## 架構變更總結

### 舊架構
```
ALB → Lambda (optimizeOrganBrief)
      └── optimize_handler.py
          └── 單一端點: /optimize_organ_brief
```

### 新架構
```
HTTP API Gateway → Lambda (flaskApi)
                    └── lambda_handler.py (Mangum)
                        └── api_controller.py (Flask)
                            ├── GET  /health
                            ├── POST /v1/company/profile/process
                            ├── GET  /v1/monitoring/logs
                            └── GET  /v1/monitoring/anomalies
```

---

## 驗證結果

### ✅ 自動化驗證 (validate_lambda_setup.sh)
- [x] 必要檔案存在檢查
- [x] requirements.txt 依賴檢查
- [x] Dockerfile.prod 配置檢查
- [x] serverless.yml 配置檢查
- [x] lambda_handler.py 語法檢查
- [x] API 端點定義檢查

**結果**: 所有驗證通過 ✅

---

## Checkpoint 1 確認項目

### 請確認以下事項：

#### 1. 架構變更
- [ ] **確認移除 ALB 觸發器**（改用 HTTP API Gateway）
- [ ] **確認新架構支援多端點 REST API**
- [ ] **確認 Lambda 函數名稱變更**: `optimizeOrganBrief` → `flaskApi`

#### 2. 環境變數
- [ ] **確認新增 LOG_LEVEL 環境變數**（dev=DEBUG, prod=INFO）
- [ ] **確認現有環境變數保留**（BEDROCK_REGION, CLAUDE_MODEL_ID）

#### 3. IAM 權限
- [ ] **確認新增 CloudWatch Logs 權限**（logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents）
- [ ] **確認保留 Bedrock 權限**

#### 4. Docker 映像
- [ ] **確認使用 Python 3.11 基礎映像**
- [ ] **確認 Lambda 入口點**: `lambda_handler.handler`

#### 5. API 端點
- [ ] **確認支援 4 個端點**:
  - GET /health
  - POST /v1/company/profile/process
  - GET /v1/monitoring/logs
  - GET /v1/monitoring/anomalies

---

## 後續步驟（等待確認後執行）

### T9.1.5: 本地測試驗證
```bash
# 1. 建立 Docker 映像
docker build -f src/functions/Dockerfile.prod -t flask-lambda-test src/functions/

# 2. 本地執行測試
docker run -p 9000:8080 flask-lambda-test

# 3. 測試健康檢查
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"rawPath": "/health", "requestContext": {"http": {"method": "GET"}}}'
```

### T9.1.6: 部署至 AWS
```bash
# 部署到 dev 環境
serverless deploy --stage dev

# 驗證部署
curl https://<api-id>.execute-api.ap-northeast-1.amazonaws.com/health
```

---

## 風險評估

### ⚠️ 重要注意事項
1. **ALB 移除**: 如果現有系統依賴 ALB，需要更新路由配置
2. **API 端點變更**: 前端需要更新 API URL（從 ALB URL 改為 API Gateway URL）
3. **環境變數**: 確認 Lambda 環境中 BEDROCK_REGION 和 CLAUDE_MODEL_ID 正確

### ✅ 風險緩解
1. **向後相容**: 所有端點保持相同的請求/回應格式
2. **逐步遷移**: 可以先部署 dev 環境測試，再部署 prod
3. **回滾計畫**: 保留舊的 serverless.yml 和 Dockerfile.dev

---

## 檔案清單

### 新建檔案
- `src/functions/lambda_handler.py` (313 bytes)
- `src/functions/Dockerfile.prod` (500 bytes)
- `scripts/validate_lambda_setup.sh` (2.7 KB)

### 修改檔案
- `serverless.yml` (47 行 → 49 行)

### 未修改檔案
- `src/functions/requirements.txt` (已包含所需依賴)
- `src/functions/api_controller.py` (Flask 應用程式)
- `src/functions/utils/` (工具模組)

---

## 等待確認

請確認上述所有變更後，我將繼續執行：
1. **T9.1.5**: 本地 Docker 測試
2. **T9.1.6**: 部署至 AWS dev 環境

---

**Checkpoint 1 確認**: [ ] 已確認，繼續執行
