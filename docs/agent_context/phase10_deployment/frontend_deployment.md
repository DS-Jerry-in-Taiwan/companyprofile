# 前端部署規劃

## 概述

前端使用 **S3** 靜態網站託管 + **CloudFront** CDN 分發，提供全球加速訪問。

---

## 架構組件

### 1. S3 Bucket

| 項目 | 設定 |
|------|------|
| 類型 | 靜態網站託管 |
| 索引文件 | index.html |
| 錯誤文件 | index.html（SPA 路由支援） |
| 存取權限 | 僅 CloudFront 可存取（OAC） |

### 2. CloudFront Distribution

| 項目 | 設定 |
|------|------|
| 原點 | S3 Bucket |
| HTTPS | 強制重導向 |
| 快取 | 靜態資源長期快取 |
| 自訂網域 | 可選 |

---

## 前端配置調整

### 1. API 基礎路徑

修改 `src/api.js`，使用環境變數或動態判斷：

```javascript
// API 基礎路徑
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

export async function processProfile(formData) {
  const response = await fetch(`${API_BASE_URL}/v1/company/profile/process`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(formData)
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw { response: { data: error, status: response.status } }
  }
  
  return response.json()
}
```

### 2. 環境變數

建立 `.env.production`：

```env
VITE_API_BASE_URL=https://your-api-gateway-url.execute-api.ap-northeast-1.amazonaws.com/prod
```

### 3. Vite 配置

```javascript
// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api/, ''),
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue']
        }
      }
    }
  }
})
```

---

## S3 配置

### Bucket Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipal",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-bucket-name/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::ACCOUNT_ID:distribution/DISTRIBUTION_ID"
        }
      }
    }
  ]
}
```

### 靜態網站託管設定

```bash
aws s3 website s3://your-bucket-name \
  --index-document index.html \
  --error-document index.html
```

---

## CloudFront 配置

### Origin Access Control (OAC)

```bash
aws cloudfront create-origin-access-control \
  --origin-access-control-config '{
    "Name": "organ-brief-oac",
    "Description": "OAC for Organ Brief S3",
    "SigningProtocol": "sigv4",
    "SigningBehavior": "always",
    "OriginAccessControlOriginType": "s3"
  }'
```

### Distribution 配置

```json
{
  "Origins": {
    "Items": [
      {
        "DomainName": "your-bucket-name.s3.ap-northeast-1.amazonaws.com",
        "Id": "S3Origin",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        },
        "OriginAccessControlId": "OAC_ID"
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3Origin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": ["GET", "HEAD", "OPTIONS"],
    "CachedMethods": ["GET", "HEAD"],
    "Compress": true,
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": { "Forward": "none" }
    },
    "DefaultTTL": 86400,
    "MaxTTL": 31536000,
    "MinTTL": 0
  },
  "CustomErrorResponses": {
    "Quantity": 1,
    "Items": [
      {
        "ErrorCode": 403,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 10
      }
    ]
  },
  "DefaultRootObject": "index.html",
  "Enabled": true,
  "PriceClass": "PriceClass_100"
}
```

---

## 部署步驟

### 1. 建置前端

```bash
cd frontend
npm install
npm run build
```

### 2. 建立 S3 Bucket

```bash
aws s3 mb s3://organ-brief-frontend --region ap-northeast-1
```

### 3. 同步檔案至 S3

```bash
aws s3 sync dist/ s3://organ-brief-frontend --delete \
  --cache-control "public, max-age=31536000" \
  --exclude "index.html"

aws s3 cp dist/index.html s3://organ-brief-frontend/index.html \
  --cache-control "no-cache, no-store, must-revalidate"
```

### 4. 建立 CloudFront Distribution

```bash
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json
```

### 5. 更新 DNS（可選）

```bash
# 如果有自訂網域
aws route53 change-resource-record-sets \
  --hosted-zone-id ZONE_ID \
  --change-batch file://dns-change.json
```

---

## 快取策略

### 靜態資源（JS/CSS/圖片）

- 快取時間：1 年
- 使用檔案雜湊作為檔名（Vite 自動處理）

### index.html

- 快取時間：0（每次驗證）
- 確保用戶獲得最新版本

### CloudFront Invalidation

部署後清除快取：

```bash
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*"
```

---

## 監控

### CloudWatch Metrics

- Requests
- Bytes Downloaded
- Bytes Uploaded
- 4xx Error Rate
- 5xx Error Rate

### CloudFront Access Logs

```bash
aws s3api put-bucket-logging \
  --bucket your-bucket-name \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "your-logs-bucket",
      "TargetPrefix": "cloudfront/"
    }
  }'
```

---

## 自訂網域設定（可選）

### 1. 設定 SSL 憑證

```bash
aws acm request-certificate \
  --domain-name your-domain.com \
  --validation-method DNS \
  --region us-east-1
```

### 2. CloudFront Alias

在 Distribution 配置中加入：

```json
{
  "Aliases": {
    "Quantity": 1,
    "Items": ["your-domain.com"]
  },
  "ViewerCertificate": {
    "ACMCertificateArn": "arn:aws:acm:us-east-1:ACCOUNT_ID:certificate/CERT_ID",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2021"
  }
}
```

---

## 注意事項

1. **SPA 路由**：設定 403/404 錯誤重導向至 index.html
2. **CORS**：確保 API 端允許 CloudFront 網域
3. **HTTPS**：強制使用 HTTPS
4. **快取**：部署後記得執行 Invalidation
5. **成本**：CloudFront 流量費用依使用量計費
