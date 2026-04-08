# Phase 9.1 開發目標與背景

## 一、階段背景

### 1.1 承接 Phase 10

Phase 10 已完成以下工作：

1. **部署規劃**：建立前後端 Serverless 部署文件
2. **後端規劃**：Lambda + API Gateway 部署架構
3. **前端規劃**：S3 + CloudFront 靜態網站託管
4. **部署腳本**：自動化部署脚本
5. **環境變數**：前後端環境變數設定說明

### 1.2 本階段動機

Phase 10 完成部署規劃，但**實際部署時**發現：

| 面向 | 問題 | 影響 |
|------|------|------|
| Lambda 入口 | 現有 `optimize_handler.py` 僅支援單一端點 | 只能處理一個 API，監控功能無法使用 |
| API 結構 | 沒有完整的 REST API | 無法提供 `/health`, `/logs`, `/anomalies` 端點 |
| 錯誤處理 | 缺少結構化日誌 | 部署後難以偵錯與監控 |
| 可擴展性 | 功能固定 | 未來新增端點困難 |

### 1.3 技術動機

Flask + Mangum 提供：

1. **多端點支援**：單一 Lambda 函數處理多個 API 端點
2. **完整路由**：RESTful 風格的路由設計
3. **中介軟體**：統一的請求/回應處理
4. **豐富生態**：Flask 擴展（CORS、登入認證等）
5. **易于測試**：標準 WSGI 應用程式

---

## 二、階段目標

### 2.1 主要目標

| 目標 | 說明 | 成功指標 |
|------|------|----------|
| Flask 整合 | 將現有 Flask API 封裝為 Lambda 相容 | Mangum 適配器正確運作 |
| 多端點部署 | 部署多個 API 端點至 Lambda | 4 個端點都可訪問 |
| CORS 配置 | 正確配置跨域請求 | 前端可正常調用 API |
| 健康檢查 | Lambda 部署後可執行健康檢查 | `/health` 端點回應正常 |

### 2.2 可選目標

| 目標 | 說明 | 成功指標 |
|------|------|----------|
| 自訂網域 | 配置 API 自訂網域 | 可使用自訂網域訪問 API |
| API Key 認證 | 添加 API Key 驗證 | 未授權請求被拒絕 |

---

## 三、成功標準

### 3.1 功能標準

- [ ] Flask 應用程式可在 Lambda 環境運行
- [ ] POST `/v1/company/profile/process` 端點正常運作
- [ ] GET `/health` 端點回應正常
- [ ] GET `/v1/monitoring/logs` 端點回應正常
- [ ] GET `/v1/monitoring/anomalies` 端點回應正常
- [ ] CORS 正確配置，前端可調用

### 3.2 整合標準

- [ ] Lambda 可正確接收 ALB/API Gateway 事件
- [ ] Flask 請求物件正確解析 Lambda 事件
- [ ] 回應格式正確（符合 API Gateway 規範）
- [ ] 結構化日誌正常運作

### 3.3 部署標準

- [ ] Docker 映像可成功建置
- [ ] Serverless Framework 部署成功
- [ ] Lambda 函數可被觸發
- [ ] CloudWatch 日誌正確寫入

---

## 四、相關文件

### 4.1 階段文件

- `docs/agent_context/phase10_deployment/README.md` - Phase 10 部署規劃總覽
- `docs/agent_context/phase10_deployment/backend_deployment.md` - 後端部署詳細規劃
- `docs/agent_context/phase10_deployment/environment_variables.md` - 環境變數說明
- `docs/agent_context/phase10_deployment/deployment_scripts.md` - 部署腳本說明

### 4.2 參考文件

- `docs/agent_context/phase9_langchain_integration/planning_summary.md` - Phase 9 規劃總結
- `serverless.yml` - Serverless 配置檔案

---

*文件資訊*
- 建立日期：2026-04-01
- 專案階段：Phase 9.1 Serverless Flask 部署
- 文檔類型：開發目標與背景
