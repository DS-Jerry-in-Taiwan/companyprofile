#!/bin/bash

# 前端部署腳本（增強版）
# 用法: ./deploy_frontend.sh [OPTIONS]

set -e

# 預設值
STAGE="dev"
AWS_REGION="ap-northeast-1"
AWS_PROFILE=""
SKIP_BUILD=false
DRY_RUN=false

# 解析參數
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--stage) STAGE="$2"; shift 2 ;;
        -r|--region) AWS_REGION="$2"; shift 2 ;;
        -p|--profile) AWS_PROFILE="$2"; shift 2 ;;
        --skip-build) SKIP_BUILD=true; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        -h|--help) grep "^#" "$0" | head -15; exit 0 ;;
        *) echo "未知參數: $1"; exit 1 ;;
    esac
done

BUCKET_NAME="organ-brief-frontend-${STAGE}"

# AWS CLI 參數
AWS_CMD="aws --region $AWS_REGION"
[ -n "$AWS_PROFILE" ] && AWS_CMD="$AWS_CMD --profile $AWS_PROFILE"

# 切換到專案根目錄
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "=========================================="
echo "  前端部署腳本"
echo "=========================================="
echo ""
echo "Stage: $STAGE"
echo "Bucket: $BUCKET_NAME"
echo "Profile: ${AWS_PROFILE:-default}"
echo ""

# 1. 建置前端
if [ "$SKIP_BUILD" = true ]; then
    echo "跳過建置"
else
    echo "=========================================="
    echo "  建置前端"
    echo "=========================================="
    
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] cd frontend && npm install && npm run build"
    else
        cd frontend
        npm install 2>&1 | tail -2
        npm run build 2>&1 | tail -5
        if [ $? -eq 0 ]; then
            echo "前端建置成功！"
        else
            echo "前端建置失敗"
            exit 1
        fi
        cd ..
    fi
fi

# 2. S3 Bucket
echo ""
echo "=========================================="
echo "  S3 Bucket"
echo "=========================================="

if [ "$DRY_RUN" = true ]; then
    echo "[DRY-RUN] aws s3 ls s3://$BUCKET_NAME"
else
    if $AWS_CMD s3 ls "s3://$BUCKET_NAME" > /dev/null 2>&1; then
        echo "Bucket 已存在: $BUCKET_NAME"
    else
        echo "建立新 Bucket: $BUCKET_NAME"
        $AWS_CMD s3 mb "s3://$BUCKET_NAME" 2>&1
        echo "Bucket 建立成功"
        
        # 設置公開讀取
        cat > /tmp/bucket-policy.json << POLICY
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
        }
    ]
}
POLICY
        $AWS_CMD s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file:///tmp/bucket-policy.json 2>&1
        echo "Bucket 政策設置完成"
    fi
fi

# 3. 同步到 S3
echo ""
echo "=========================================="
echo "  同步到 S3"
echo "=========================================="

if [ "$DRY_RUN" = true ]; then
    echo "[DRY-RUN] aws s3 sync frontend/dist/ s3://$BUCKET_NAME --delete"
else
    echo "同步靜態資源..."
    $AWS_CMD s3 sync frontend/dist/ "s3://$BUCKET_NAME" --delete \
        --cache-control "public, max-age=31536000" \
        --exclude "index.html" 2>&1
    
    echo "同步 index.html..."
    $AWS_CMD s3 cp frontend/dist/index.html "s3://$BUCKET_NAME/index.html" \
        --cache-control "no-cache, no-store, must-revalidate" 2>&1
    
    echo "檔案同步完成"
fi

# 4. 清除 CloudFront 快取（自動檢測）
echo ""
echo "=========================================="
echo "  CloudFront 快取清除"
echo "=========================================="

# 自動檢測 CloudFront Distribution
CF_DISTRIBUTION_ID=$($AWS_CMD cloudfront list-distributions \
    --query "DistributionList.Items[?contains(Origins.Items[].DomainName, '$BUCKET_NAME')].Id" \
    --output text 2>/dev/null | tr -d '\n')

if [ -n "$CF_DISTRIBUTION_ID" ] && [ "$CF_DISTRIBUTION_ID" != "None" ]; then
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] aws cloudfront create-invalidation --distribution-id $CF_DISTRIBUTION_ID --paths /*"
    else
        echo "找到 CloudFront Distribution: $CF_DISTRIBUTION_ID"
        echo "清除快取..."
        INVALIDATION_ID=$($AWS_CMD cloudfront create-invalidation \
            --distribution-id "$CF_DISTRIBUTION_ID" \
            --paths "/*" \
            --query 'Invalidation.Id' \
            --output text 2>&1)
        echo "Invalidation ID: $INVALIDATION_ID"
        echo "Status: InProgress"
    fi
else
    echo "未找到關聯的 CloudFront Distribution"
    echo "跳過快取清除"
fi

# 5. 完成
echo ""
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "S3 Bucket: s3://$BUCKET_NAME"
echo ""

# 獲取 CloudFront 網址
CF_DOMAIN=$($AWS_CMD cloudfront list-distributions \
    --query "DistributionList.Items[?contains(Origins.Items[].DomainName, '$BUCKET_NAME')].DomainName" \
    --output text 2>/dev/null | tr -d '\n')

if [ -n "$CF_DOMAIN" ] && [ "$CF_DOMAIN" != "None" ]; then
    echo "CloudFront 網址: https://$CF_DOMAIN"
fi

# S3 網站端點
S3_WEBSITE=$($AWS_CMD s3 website "s3://$BUCKET_NAME" --query 'Endpoint' --output text 2>/dev/null)
if [ -n "$S3_WEBSITE" ]; then
    echo "S3 靜態網站: http://$S3_WEBSITE"
fi

echo ""
