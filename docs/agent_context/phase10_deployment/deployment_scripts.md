# 部署腳本

## 概述

提供自動化部署腳本，簡化前後端部署流程。

---

## 前置需求

- AWS CLI 已安裝並配置
- Node.js 18+
- Docker（後端部署需要）
- Serverless Framework：`npm install -g serverless`

---

## 後端部署腳本

### deploy_backend.sh

```bash
#!/bin/bash

# 後端部署腳本
# 用法: ./deploy_backend.sh [stage]

set -e

STAGE=${1:-dev}
REGION="ap-northeast-1"
SERVICE_NAME="organ-brief-optimization"

echo "=========================================="
echo "部署後端服務"
echo "Stage: $STAGE"
echo "Region: $REGION"
echo "=========================================="

# 1. 建置 Docker 映像
echo "[1/4] 建置 Docker 映像..."
cd src/functions
docker build -f Dockerfile.$STAGE -t $SERVICE_NAME:$STAGE .

# 2. 取得 ECR 登入
echo "[2/4] 登入 ECR..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$SERVICE_NAME"
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO

# 3. 推送映像至 ECR
echo "[3/4] 推送映像至 ECR..."
docker tag $SERVICE_NAME:$STAGE $ECR_REPO:$STAGE
docker push $ECR_REPO:$STAGE

# 4. 部署 Serverless
echo "[4/4] 部署 Serverless..."
cd ..
serverless deploy --stage $STAGE

echo "=========================================="
echo "後端部署完成！"
echo "=========================================="
```

### 使腳本可執行

```bash
chmod +x deploy_backend.sh
```

---

## 前端部署腳本

### deploy_frontend.sh

```bash
#!/bin/bash

# 前端部署腳本
# 用法: ./deploy_frontend.sh [stage]

set -e

STAGE=${1:-dev}
BUCKET_NAME="organ-brief-frontend-$STAGE"
DISTRIBUTION_ID=""  # 設定你的 CloudFront Distribution ID

echo "=========================================="
echo "部署前端服務"
echo "Stage: $STAGE"
echo "Bucket: $BUCKET_NAME"
echo "=========================================="

# 1. 建置前端
echo "[1/4] 建置前端..."
cd frontend
npm install
npm run build

# 2. 建立 S3 Bucket（如果不存在）
echo "[2/4] 檢查 S3 Bucket..."
if ! aws s3 ls "s3://$BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Bucket 已存在"
else
    echo "建立 Bucket..."
    aws s3 mb "s3://$BUCKET_NAME" --region ap-northeast-1
fi

# 3. 同步檔案至 S3
echo "[3/4] 同步檔案至 S3..."
# 同步靜態資源（帶快取）
aws s3 sync dist/ "s3://$BUCKET_NAME" --delete \
  --cache-control "public, max-age=31536000" \
  --exclude "index.html"

# 同步 index.html（不快取）
aws s3 cp dist/index.html "s3://$BUCKET_NAME/index.html" \
  --cache-control "no-cache, no-store, must-revalidate"

# 4. 清除 CloudFront 快取
if [ -n "$DISTRIBUTION_ID" ]; then
    echo "[4/4] 清除 CloudFront 快取..."
    aws cloudfront create-invalidation \
      --distribution-id $DISTRIBUTION_ID \
      --paths "/*"
else
    echo "[4/4] 跳過 CloudFront Invalidation（未設定 DISTRIBUTION_ID）"
fi

echo "=========================================="
echo "前端部署完成！"
echo "=========================================="
```

### 使腳本可執行

```bash
chmod +x deploy_frontend.sh
```

---

## 一鍵部署腳本

### deploy_all.sh

```bash
#!/bin/bash

# 一鍵部署腳本
# 用法: ./deploy_all.sh [stage]

set -e

STAGE=${1:-dev}

echo "=========================================="
echo "開始部署 Organ Brief Optimization"
echo "Stage: $STAGE"
echo "=========================================="

# 部署後端
echo ""
echo ">>> 開始部署後端..."
./deploy_backend.sh $STAGE

# 部署前端
echo ""
echo ">>> 開始部署前端..."
./deploy_frontend.sh $STAGE

echo ""
echo "=========================================="
echo "全部部署完成！"
echo "=========================================="
```

---

## 回滾腳本

### rollback.sh

```bash
#!/bin/bash

# 回滾腳本
# 用法: ./rollback.sh [stage] [version]

set -e

STAGE=${1:-dev}
VERSION=${2:-previous}
SERVICE_NAME="organ-brief-optimization"

echo "=========================================="
echo "回滾部署"
echo "Stage: $STAGE"
echo "Version: $VERSION"
echo "=========================================="

# 回滾 Serverless 部署
serverless rollback --stage $STAGE --timestamp $VERSION

echo "=========================================="
echo "回滾完成！"
echo "=========================================="
```

---

## 環境變數配置

### 建立 .env.deploy

```env
# 部署腳本環境變數
AWS_REGION=ap-northeast-1
BUCKET_NAME=organ-brief-frontend
DISTRIBUTION_ID=YOUR_DISTRIBUTION_ID
ECR_REPO=organ-brief-optimization
```

---

## CI/CD 整合（GitHub Actions）

### .github/workflows/deploy.yml

```yaml
name: Deploy

on:
  push:
    branches:
      - main
      - develop

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS Credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ap-northeast-1
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install Dependencies
      run: |
        npm install -g serverless
        cd frontend && npm install
    
    - name: Determine Stage
      id: stage
      run: |
        if [ "${{ github.ref }}" = "refs/heads/main" ]; then
          echo "stage=prod" >> $GITHUB_OUTPUT
        else
          echo "stage=dev" >> $GITHUB_OUTPUT
        fi
    
    - name: Deploy Backend
      run: ./deploy_backend.sh ${{ steps.stage.outputs.stage }}
    
    - name: Deploy Frontend
      run: ./deploy_frontend.sh ${{ steps.stage.outputs.stage }}
```

---

## 測試部署

### 部署後驗證

```bash
# 1. 檢查後端健康
curl https://your-api-url/health

# 2. 測試 API
curl -X POST https://your-api-url/v1/company/profile/process \
  -H "Content-Type: application/json" \
  -d '{"organNo":"69188618","organ":"測試機構","mode":"GENERATE"}'

# 3. 檢查前端
curl -I https://your-cloudfront-url
```

---

## 常見問題

### 1. Docker 建置失敗

確保 Dockerfile 路徑正確，且有適當權限：

```bash
chmod +r src/functions/*
```

### 2. ECR 推送失敗

確認已建立 ECR Repository：

```bash
aws ecr create-repository --repository-name organ-brief-optimization
```

### 3. CloudFront 快取未更新

執行 Invalidation：

```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_ID \
  --paths "/*"
```

### 4. CORS 錯誤

確認後端 CORS_ORIGINS 環境變數包含前端網域。
