# Phase 10: Serverless 部署規劃

## 目標

將 Organ Brief Optimization 系統部署為 Serverless 架構，提供外部調用能力。

- **後端**：AWS Lambda + API Gateway（或現有 ALB）
- **前端**：S3 + CloudFront（靜態網站託管）

---

## 架構概覽

```
┌─────────────────────────────────────────────────────────────────┐
│                         CloudFront                               │
│                    (HTTPS, CDN, Caching)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      S3 Bucket                                  │
│                  (前端靜態檔案)                                   │
│   - index.html                                                  │
│   - assets/*.js                                                 │
│   - assets/*.css                                                │
└─────────────────────────────────────────────────────────────────┘

                              │
                              │ API 請求
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway / ALB                             │
│              (CORS, 路由, 限流)                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AWS Lambda                                   │
│               (Python 3.11 + Flask)                             │
│                                                                  │
│   - POST /v1/company/profile/process                            │
│   - GET  /v1/monitoring/logs                                    │
│   - GET  /v1/monitoring/anomalies                               │
│   - GET  /health                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Bedrock                                   │
│              (Claude 3.5 Sonnet)                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 文件目錄

| 文件 | 說明 |
|------|------|
| [後端部署規劃](./backend_deployment.md) | Lambda + API Gateway 部署詳細規劃 |
| [前端部署規劃](./frontend_deployment.md) | S3 + CloudFront 部署詳細規劃 |
| [環境變數設定](./environment_variables.md) | 前後端環境變數說明 |
| [部署腳本](./deployment_scripts.md) | 自動化部署腳本說明 |

---

## 部署流程摘要

### 1. 後端部署

```bash
# 使用 Serverless Framework
cd src/functions
serverless deploy --stage prod
```

### 2. 前端部署

```bash
# 建置並部署到 S3
cd frontend
npm run build
aws s3 sync dist/ s3://your-bucket-name --delete
aws cloudfront create-invalidation --distribution-id YOUR_ID --paths "/*"
```

---

## 前置需求

- AWS CLI 已安裝並配置
- Serverless Framework (`npm install -g serverless`)
- Docker（用於 Lambda 容器映像建置）
- Node.js 18+

---

## 成本估算

| 服務 | 預估月費（USD） |
|------|----------------|
| Lambda（1000 次/月） | ~$0.20 |
| API Gateway | ~$3.50 |
| S3 | ~$0.50 |
| CloudFront | ~$1.00 |
| **總計** | **~$5.20** |

*註：實際費用依使用量而定*
