#!/bin/bash

# 後端部署腳本
# 用法: ./deploy_backend.sh [stage]
# 環境變數: AWS_PROFILE (可選), AWS_REGION (可選，預設: ap-northeast-1)

set -e

STAGE=${1:-dev}
AWS_REGION=${AWS_REGION:-"ap-northeast-1"}

echo "=========================================="
echo "部署後端服務"
echo "Stage: $STAGE"
echo "Region: $AWS_REGION"
echo "AWS Profile: ${AWS_PROFILE:-使用默認憑證}"
echo "=========================================="

# 切換到專案根目錄（serverless.yml 所在位置）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# 設定 AWS CLI 參數（如果指定了 profile）
AWS_CLI_PROFILE=""
if [ -n "$AWS_PROFILE" ]; then
    AWS_CLI_PROFILE="--profile $AWS_PROFILE"
fi

# 登入 ECR（Serverless 部署時需要）
echo "[1/2] 登入 ECR..."
ACCOUNT_ID=$(aws $AWS_CLI_PROFILE sts get-caller-identity --query Account --output text)
aws $AWS_CLI_PROFILE ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# 部署（Serverless 會自動 build & push image）
echo "[2/2] 部署 Serverless..."
serverless deploy --stage $STAGE

echo "=========================================="
echo "後端部署完成！"
echo "=========================================="
