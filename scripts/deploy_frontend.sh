#!/bin/bash

# 前端部署腳本
# 用法: ./deploy_frontend.sh [stage]
# 環境變數: AWS_PROFILE (可選), AWS_REGION (可選，預設: ap-northeast-1)

set -e

STAGE=${1:-dev}
AWS_REGION=${AWS_REGION:-"ap-northeast-1"}
BUCKET_NAME="organ-brief-frontend-$STAGE"
DISTRIBUTION_ID=""  # 設定你的 CloudFront Distribution ID

echo "=========================================="
echo "部署前端服務"
echo "Stage: $STAGE"
echo "Region: $AWS_REGION"
echo "Bucket: $BUCKET_NAME"
echo "AWS Profile: ${AWS_PROFILE:-使用默認憑證}"
echo "=========================================="

# 設定 AWS CLI 參數（如果指定了 profile）
AWS_CLI_PROFILE=""
if [ -n "$AWS_PROFILE" ]; then
    AWS_CLI_PROFILE="--profile $AWS_PROFILE"
fi

# 1. 建置前端
echo "[1/4] 建置前端..."
cd frontend
npm install
npm run build

# 2. 建立 S3 Bucket（如果不存在）
echo "[2/4] 檢查 S3 Bucket..."
if aws $AWS_CLI_PROFILE s3 ls "s3://$BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "建立 Bucket..."
    aws $AWS_CLI_PROFILE s3 mb "s3://$BUCKET_NAME" --region $AWS_REGION
else
    echo "Bucket 已存在"
fi

# 3. 同步檔案至 S3
echo "[3/4] 同步檔案至 S3..."
# 同步靜態資源（帶快取）
aws $AWS_CLI_PROFILE s3 sync dist/ "s3://$BUCKET_NAME" --delete \
  --cache-control "public, max-age=31536000" \
  --exclude "index.html"

# 同步 index.html（不快取）
aws $AWS_CLI_PROFILE s3 cp dist/index.html "s3://$BUCKET_NAME/index.html" \
  --cache-control "no-cache, no-store, must-revalidate"

# 4. 清除 CloudFront 快取
if [ -n "$DISTRIBUTION_ID" ]; then
    echo "[4/4] 清除 CloudFront 快取..."
    aws $AWS_CLI_PROFILE cloudfront create-invalidation \
      --distribution-id $DISTRIBUTION_ID \
      --paths "/*"
else
    echo "[4/4] 跳過 CloudFront Invalidation（未設定 DISTRIBUTION_ID）"
fi

echo "=========================================="
echo "前端部署完成！"
echo "=========================================="
