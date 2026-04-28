# Phase 9.1 啟動指令

---

**專案根目錄**: `/home/ubuntu/projects/OrganBriefOptimization`

**當前階段**: Phase 9.1 - Serverless Flask 部署

**執行模式**: 混合模式

---

## 📁 請閱讀 Phase 9.1 的7份 Context 文件

```
1. docs/agent_context/phase9.1_serverless_flask_deployment/01_dev_goal_context.md
2. docs/agent_context/phase9.1_serverless_flask_deployment/02_dev_flow_context.md
3. docs/agent_context/phase9.1_serverless_flask_deployment/03_tech_spec_context.md
4. docs/agent_context/phase9.1_serverless_flask_deployment/04_agent_prompts_context.md
5. docs/agent_context/phase9.1_serverless_flask_deployment/05_validation_checklist.md
6. docs/agent_context/phase9.1_serverless_flask_deployment/06_delivery_record.md
7. docs/agent_context/phase9.1_serverless_flask_deployment/07_checkpoint_protocol.md
```

---

## 🚀 執行順序

### Phase 1: 環境準備（@INFRA）
- 更新 `src/functions/requirements.txt`（加入 Flask + Mangum）
- 自動驗證

### Phase 2: Lambda 入口建立（@CODER）
- 建立 `src/functions/lambda_handler.py`
- 建立 `src/functions/Dockerfile.prod`
- 更新 `serverless.yml`
- **【Checkpoint 1】人工確認**

### Phase 3: 測試驗證（@ANALYST）
- 本地 Docker 測試
- 部署至 AWS
- **【Checkpoint 2】人工確認**

### Phase 4: 驗證與交付（@ANALYST）
- 執行最終驗證
- 更新交付記錄

---

## 🎯 任務清單

### T9.1.1: 更新 requirements.txt
```
將 src/functions/requirements.txt 替換為：
- boto3>=1.37.11
- botocore>=1.37.11
- flask>=3.1.0
- flask-cors>=5.0.0
- mangum>=0.17.0
- pydantic>=2.10.0
- python-dotenv>=1.0.1
```

### T9.1.2: 建立 lambda_handler.py
```
建立 src/functions/lambda_handler.py：
- 匯入 Mangum
- 匯入 api_controller.app
- 建立 handler = Mangum(flask_app, debug=False)
```

### T9.1.3: 建立 Dockerfile.prod
```
建立 src/functions/Dockerfile.prod：
- 基礎映像: public.ecr.aws/lambda/python:3.11
- 複製 requirements.txt, api_controller.py, lambda_handler.py, utils/
- CMD: lambda_handler.handler
```

### T9.1.4: 更新 serverless.yml
```
更新 functions 區段：
- 設定 image, memorySize, timeout
- 設定 CORS
- 設定環境變數
```

### T9.1.5: 本地測試驗證
```
執行 Docker 本地測試：
- docker build -f Dockerfile.prod -t organ-brief:test .
- docker run -p 9000:8080 organ-brief:test
- 測試 /health 端點
- 測試 /v1/company/profile/process 端點
```

### T9.1.6: 部署至 AWS
```
部署至 AWS：
- 登入 AWS ECR
- 推送 Docker 映像
- serverless deploy --stage prod
- 驗證上線
```

---

## 📋 Checkpoint 說明

### Checkpoint 1: Lambda 入口確認
在 T9.1.4 完成後觸發：
- 確認 lambda_handler.py 可正確匯入
- 確認 Dockerfile.prod 可建置
- 確認 serverless.yml 配置正確

### Checkpoint 2: 部署確認
在 T9.1.6 完成後觸發：
- 確認 Lambda 函數部署成功
- 確認 API 端點可訪問
- 確認 CloudWatch 日誌正常

---

## ✅ 驗證與交付

### 自動驗證（參考 05_validation_checklist.md）
```bash
# 本地測試
cd src/functions
docker build -f Dockerfile.prod -t organ-brief:test .
docker run -d -p 9000:8080 organ-brief:test
curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -d '{"resource":"/health","httpMethod":"GET"}'
```

### 更新交付記錄（參考 06_delivery_record.md）
- 填入實際完成時間
- 更新驗證結果
- 標記交付物狀態

---

## 🎬 立即啟動

```
✅ 啟動 Phase 9.1
執行模式：混合模式
從 T9.1.1 開始
```

---

*啟動指令完成*
- 建立日期：2026-04-01
- 專案階段：Phase 9.1 Serverless Flask 部署
- 執行模式：混合模式
