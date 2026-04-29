#!/bin/bash

# 前端部署腳本（增強版）
# 用法: ./deploy_frontend.sh [OPTIONS]
#
# 選項:
#   -s, --stage STAGE           部署階段 (dev/prod) [默認: dev]
#   -r, --region REGION         AWS 區域 [默認: ap-northeast-1]
#   -p, --profile PROFILE       AWS Profile 名稱
#   --skip-build                跳過前端建置
#   --dry-run                   乾跑模式
#   -h, --help                  顯示幫助信息

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

# ALB API Path (依 stage 區分)
case $STAGE in
    dev)
        ALB_API_PATH="/organ-brief-dev/api/recurit/optimize/v1"
        ;;
    prod)
        ALB_API_PATH="/organ-brief-prd/api/recurit/optimize/v1"
        ;;
    *)
        echo "未知 stage: $STAGE (請使用 dev 或 prod)"
        exit 1
        ;;
esac

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
echo "API Path: $ALB_API_PATH"
echo "Profile: ${AWS_PROFILE:-default}"
echo ""

# 1. 寫入 stage 對應的 .env.production
echo "=========================================="
echo "  設定 API 路徑"
echo "=========================================="
echo "VITE_API_BASE_URL=${ALB_API_PATH}" > frontend/.env.production
echo "API_BASE_URL → ${ALB_API_PATH}"
echo ""

# 2. 建置前端
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

# 3. S3 Bucket
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
        
        # 預設區塊公開存取
        $AWS_CMD s3api put-public-access-block \
            --bucket "$BUCKET_NAME" \
            --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" 2>&1
        echo "已啟用區塊公開存取 (使用 CloudFront OAI)"
    fi
fi

# 4. 同步到 S3
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

# 5. CloudFront Distribution 檢查 / 建立
echo ""
echo "=========================================="
echo "  CloudFront"
echo "=========================================="

CF_DISTRIBUTION_ID=$($AWS_CMD cloudfront list-distributions \
    --query "DistributionList.Items[?contains(Origins.Items[].DomainName, '$BUCKET_NAME')].Id" \
    --output text 2>/dev/null | tr -d '\n')

if [ -n "$CF_DISTRIBUTION_ID" ] && [ "$CF_DISTRIBUTION_ID" != "None" ]; then
    echo "CloudFront Distribution 已存在: $CF_DISTRIBUTION_ID"
    
    # 清除快取
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] aws cloudfront create-invalidation --distribution-id $CF_DISTRIBUTION_ID --paths /*"
    else
        echo "清除快取..."
        INVALIDATION_ID=$($AWS_CMD cloudfront create-invalidation \
            --distribution-id "$CF_DISTRIBUTION_ID" \
            --paths "/*" \
            --query 'Invalidation.Id' \
            --output text 2>&1)
        echo "Invalidation ID: $INVALIDATION_ID"
        echo "Status: InProgress (生效需幾分鐘)"
    fi
else
    echo "尚未建立 CloudFront Distribution"
    echo ""
    echo "請手動建立 CloudFront Distribution:"
    echo "  1. AWS Console → CloudFront → Create Distribution"
    echo "  2. Origin 1: S3 → ${BUCKET_NAME}"
    echo "     - 勾選 'Restrict Bucket Access' (OAI)"
    echo "  3. Origin 2: ALB → ${ALB_DNS:-your-alb-dns}"
    echo "     - Protocol: HTTP only"
    echo "  4. Behaviors:"
    echo "     - /organ-brief-${STAGE}/api/recurit/optimize/* → Origin 2 (ALB)"
    echo "     - Default (*) → Origin 1 (S3)"
    echo "  5. 完成後重新執行此腳本以清除快取"
fi

# 6. 完成
echo ""
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "S3 Bucket: s3://$BUCKET_NAME"
echo ""

# 取得 CloudFront 網址
CF_DOMAIN=$($AWS_CMD cloudfront list-distributions \
    --query "DistributionList.Items[?contains(Origins.Items[].DomainName, '$BUCKET_NAME')].DomainName" \
    --output text 2>/dev/null | tr -d '\n')

if [ -n "$CF_DOMAIN" ] && [ "$CF_DOMAIN" != "None" ]; then
    echo "CloudFront 網址: https://$CF_DOMAIN"
    echo "API 路徑: https://$CF_DOMAIN${ALB_API_PATH}/company/profile/process"
fi
