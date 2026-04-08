# Phase 9.1 檢查點協議

## 一、檢查點概述

### 1.1 目的

確保 Developer Agent 在 Phase 9.1 開發過程中，按照正確的順序完成任務，並在每個關鍵點進行驗證。

### 1.2 檢查點數量

本階段共設有 **7 個檢查點**。

---

## 二、檢查點清單

### 2.1 檢查點 1：現況分析（Checkpoint 1）

**任務**：T9.1.0 - 現況分析與差異評估

**完成條件**：
- [ ] 分析現有 Lambda 原生架構
- [ ] 分析 Flask + Mangum 架構差異
- [ ] 列出需要修改的檔案清單

**交付物**：
- 差異分析文件（可記錄在 README 或 Notion）

**驗證方式**：
```bash
# 確認現有檔案存在
ls -la src/functions/
ls -la src/functions/utils/
```

---

### 2.2 檢查點 2：依賴更新（Checkpoint 2）

**任務**：T9.1.1 - 更新 requirements.txt

**完成條件**：
- [ ] requirements.txt 包含 Flask
- [ ] requirements.txt 包含 flask-cors
- [ ] requirements.txt 包含 mangum
- [ ] 本地 pip install 成功

**交付物**：
- `src/functions/requirements.txt`

**驗證方式**：
```bash
cd src/functions
pip install -r requirements.txt
python -c "from flask import Flask; from mangum import Mangum; print('OK')"
# 預期輸出：OK
```

---

### 2.3 檢查點 3：Lambda 入口（Checkpoint 3）

**任務**：T9.1.2 - 建立 Lambda 入口適配器

**完成條件**：
- [ ] lambda_handler.py 建立完成
- [ ] 可正確匯入 api_controller.app
- [ ] Mangum 適配器正確初始化

**交付物**：
- `src/functions/lambda_handler.py`

**驗證方式**：
```bash
python -c "from lambda_handler import handler; print('Type:', type(handler).__name__)"
# 預期輸出：Type: Mangum
```

---

### 2.4 檢查點 4：Docker 映像（Checkpoint 4）

**任務**：T9.1.3 - 建立 Dockerfile.prod

**完成條件**：
- [ ] Dockerfile.prod 建立完成
- [ ] Docker 映像可成功建置
- [ ] 映像可本地運行

**交付物**：
- `src/functions/Dockerfile.prod`

**驗證方式**：
```bash
cd src/functions
docker build -f Dockerfile.prod -t organ-brief:test .
docker run -d -p 9000:8080 organ-brief:test
curl http://localhost:9000/2015-03-31/functions/function/invocations \
  -d '{"resource":"/health","httpMethod":"GET"}'
# 預期回應：包含 "healthy"
```

---

### 2.5 檢查點 5：Serverless 配置（Checkpoint 5）

**任務**：T9.1.4 - 更新 serverless.yml

**完成條件**：
- [ ] serverless.yml 更新完成
- [ ] CORS 配置正確
- [ ] serverless print 執行成功

**交付物**：
- `serverless.yml`（更新後）

**驗證方式**：
```bash
cd src/functions
serverless print --stage dev
# 確認輸出包含函數定義
```

---

### 2.6 檢查點 6：本地測試（Checkpoint 6）

**任務**：T9.1.5 - 本地測試驗證

**完成條件**：
- [ ] Docker 容器運行正常
- [ ] /health 端點回應正確
- [ ] /v1/company/profile/process 端點回應正確
- [ ] CORS 測試通過

**交付物**：
- 測試結果記錄

**驗證方式**：
```bash
# 測試所有端點
curl -X GET http://localhost:9000/2015-03-31/functions/function/invocations \
  -d '{"resource":"/health","httpMethod":"GET"}'

curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -d '{"resource":"/v1/company/profile/process","httpMethod":"POST","body":"{\"organNo\":\"123\"}"'
```

---

### 2.7 檢查點 7：部署驗證（Checkpoint 7）

**任務**：T9.1.6 - 部署至 AWS

**完成條件**：
- [ ] ECR 映像推送成功
- [ ] Lambda 函數部署成功
- [ ] API Gateway 路由正確
- [ ] 所有端點可透過網際網路訪問
- [ ] CloudWatch 日誌正常

**交付物**：
- 部署後的 API URL
- CloudWatch 日誌截圖

**驗證方式**：
```bash
# 取得 API URL
API_URL=$(aws apigatewayv2 get-apis --region ap-northeast-1 \
  --query 'Items[0].ApiEndpoint' --output text)

# 測試各端點
curl $API_URL/health
curl -X POST $API_URL/v1/company/profile/process \
  -H "Content-Type: application/json" \
  -d '{"organNo":"123","organ":"Test","mode":"GENERATE"}'

# 檢查日誌
aws logs tail /aws/lambda/organ-brief-optimization-prod-api --follow
```

---

## 三、檢查點流程

```
Checkpoint 1 ──► Checkpoint 2 ──► Checkpoint 3 ──► Checkpoint 4 ──► Checkpoint 5 ──► Checkpoint 6 ──► Checkpoint 7
   (分析)        (依賴)         (入口)         (Docker)        (配置)         (測試)          (部署)
```

---

## 四、驗證失敗處理

### 4.1 驗證失敗時的處理流程

```
驗證失敗
    │
    ▼
記錄錯誤訊息
    │
    ▼
分析原因
    │
    ├──► 環境問題 → 檢查環境配置
    │
    ├──► 程式碼問題 → 修正程式碼
    │
    └──► 依賴問題 → 更新依賴
    │
    ▼
重新執行驗證
    │
    ▼
仍然失敗 → 尋求協助
```

### 4.2 常見驗證失敗原因

| 檢查點 | 常見問題 | 解決方案 |
|--------|----------|----------|
| C2 | pip install 失敗 | 檢查網路連線，嘗試使用 virtualenv |
| C3 | ImportError | 確認 api_controller.py 路徑正確 |
| C4 | Docker 建置失敗 | 檢查 Dockerfile 語法，確認網路 |
| C5 | serverless print 失敗 | 檢查 YAML 語法 |
| C6 | 端點無回應 | 檢查容器是否正常運行 |
| C7 | 部署失敗 | 檢查 AWS 權限 |

---

## 五、檢查點記錄表

| 檢查點 | 任務 | 完成日期 | 狀態 | 驗證人 |
|--------|------|----------|------|--------|
| C1 | T9.1.0 | - | ⬜ | - |
| C2 | T9.1.1 | - | ⬜ | - |
| C3 | T9.1.2 | - | ⬜ | - |
| C4 | T9.1.3 | - | ⬜ | - |
| C5 | T9.1.4 | - | ⬜ | - |
| C6 | T9.1.5 | - | ⬜ | - |
| C7 | T9.1.6 | - | ⬜ | - |

---

*文件資訊*
- 建立日期：2026-04-01
- 專案階段：Phase 9.1 Serverless Flask 部署
- 文檔類型：檢查點協議
