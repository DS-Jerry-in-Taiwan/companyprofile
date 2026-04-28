# Phase 9.1 驗證檢查清單

## 一、功能驗證

### 1.1 依賴套件驗證

- [ ] **T9.1.1.1** requirements.txt 包含 Flask >= 3.1.0
- [ ] **T9.1.1.2** requirements.txt 包含 flask-cors >= 5.0.0
- [ ] **T9.1.1.3** requirements.txt 包含 mangum >= 0.17.0
- [ ] **T9.1.1.4** requirements.txt 包含 pydantic >= 2.10.0
- [ ] **T9.1.1.5** requirements.txt 包含 python-dotenv >= 1.0.1
- [ ] **T9.1.1.6** 本地 `pip install -r requirements.txt` 成功

### 1.2 Lambda 入口驗證

- [ ] **T9.1.2.1** lambda_handler.py 成功匯入 Mangum
- [ ] **T9.1.2.2** lambda_handler.py 成功匯入 api_controller.app
- [ ] **T9.1.2.3** lambda_handler.handler 函數存在
- [ ] **T9.1.2.4** lambda_handler.py 可被 Python 執行

### 1.3 Docker 驗證

- [ ] **T9.1.3.1** Dockerfile.prod 基礎映像正確（public.ecr.aws/lambda/python:3.11）
- [ ] **T9.1.3.2** Dockerfile.prod 複製所有必要檔案
- [ ] **T9.1.3.3** Dockerfile.prod 正確設定 CMD
- [ ] **T9.1.3.4** Docker 映像可成功建置
- [ ] **T9.1.3.5** Docker 映像可本地運行

### 1.4 Serverless 配置驗證

- [ ] **T9.1.4.1** serverless.yml 函數映像名稱正確
- [ ] **T9.1.4.2** serverless.yml 設定 CORS
- [ ] **T9.1.4.3** serverless.yml 環境變數正確
- [ ] **T9.1.4.4** serverless deploy --stage dev 成功

---

## 二、API 端點驗證

### 2.1 健康檢查端點

- [ ] **E2.1.1** GET /health 回應 200
- [ ] **E2.1.2** 回應包含 status: healthy
- [ ] **E2.1.3** 回應包含 timestamp

### 2.2 公司簡介處理端點

- [ ] **E2.2.1** POST /v1/company/profile/process 回應 200（正常請求）
- [ ] **E2.2.2** POST /v1/company/profile/process 回應 400（缺少必要欄位）
- [ ] **E2.2.3** POST /v1/company/profile/process 回應 500（伺服器錯誤）
- [ ] **E2.2.4** 回應格式正確（包含 success/data/error）

### 2.3 日誌查詢端點

- [ ] **E2.3.1** GET /v1/monitoring/logs 回應 200
- [ ] **E2.3.2** 支援 query 參數篩選
- [ ] **E2.3.3** 回應包含日誌列表

### 2.4 異常統計端點

- [ ] **E2.4.1** GET /v1/monitoring/anomalies 回應 200
- [ ] **E2.4.2** 回應包含異常統計資料

---

## 三、CORS 驗證

### 3.1 跨域請求測試

- [ ] **C3.1.1** OPTIONS /v1/company/profile/process 回應 200
- [ ] **C3.1.2** 回應包含 Access-Control-Allow-Origin
- [ ] **C3.1.3** 回應包含 Access-Control-Allow-Methods
- [ ] **C3.1.4** 回應包含 Access-Control-Allow-Headers
- [ ] **C3.1.5** 前端可成功呼叫 API（從不同網域）

---

## 四、部署驗證

### 4.1 AWS 部署

- [ ] **D4.1.1** ECR 映像推送成功
- [ ] **D4.1.2** Lambda 函數部署成功
- [ ] **D4.1.3** API Gateway 路由設定正確
- [ ] **D4.1.4** ALB 目標群組綁定正確

### 4.2 功能測試

- [ ] **D4.2.1** Lambda 可被 API Gateway 觸發
- [ ] **D4.2.2** 所有端點可透過網際網路訪問
- [ ] **D4.2.3** 回應時間合理（< 30 秒）

### 4.3 監控驗證

- [ ] **D4.3.1** CloudWatch Logs 正確寫入
- [ ] **D4.3.2** 日誌包含 request_id
- [ ] **D4.3.3** 錯誤日誌正確記錄
- [ ] **D4.3.4** CloudWatch Metrics 正常顯示

---

## 五、整合驗證

### 5.1 Flask 與 Lambda 整合

- [ ] **I5.1.1** Flask app 可正確處理 Lambda 事件
- [ ] **I5.1.2** Mangum 正確轉換請求格式
- [ ] **I5.1.3** Mangum 正確轉換回應格式

### 5.2 與現有系統整合

- [ ] **I5.2.1** 現有 api_controller.py 功能正常
- [ ] **I5.2.2** 結構化日誌正常運作
- [ ] **I5.2.3** 異常偵測正常運作

---

## 六、驗證命令參考

### 6.1 本地測試

```bash
# 建置 Docker
cd src/functions
docker build -f Dockerfile.prod -t organ-brief:test .

# 運行容器
docker run -p 9000:8080 organ-brief:test

# 測試健康檢查
curl -X GET http://localhost:9000/2015-03-31/functions/function/invocations \
  -d '{"resource":"/health","httpMethod":"GET"}'

# 測試 API 端點
curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -d '{"resource":"/v1/company/profile/process","httpMethod":"POST","body":"{\"organNo\":\"123\"}"}'
```

### 6.2 部署後測試

```bash
# 取得 API URL
API_URL=$(aws apigatewayv2 get-apis --region ap-northeast-1 | jq -r '.Items[0].ApiEndpoint')

# 測試健康檢查
curl ${API_URL}/health

# 測試 API 端點
curl -X POST ${API_URL}/v1/company/profile/process \
  -H "Content-Type: application/json" \
  -d '{"organNo":"123","organ":"Test Company","mode":"GENERATE"}'
```

---

*文件資訊*
- 建立日期：2026-04-01
- 專案階段：Phase 9.1 Serverless Flask 部署
- 文檔類型：驗證檢查清單
