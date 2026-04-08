#!/bin/bash

# 後端部署腳本
# 用法: ./deploy_backend.sh [stage]

set -e

STAGE=${1:-dev}
REGION="ap-northeast-1"

echo "=========================================="
echo "部署後端服務"
echo "Stage: $STAGE"
echo "Region: $REGION"
echo "=========================================="

# 切換到專案根目錄（serverless.yml 所在位置）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# 登入 ECR（Serverless 部署時需要）
echo "[1/2] 登入 ECR..."
ACCOUNT_ID=$(aws --profile $AWS_PROFILE sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# 部署（Serverless 會自動 build & push image）
echo "[2/2] 部署 Serverless..."
serverless deploy --stage $STAGE

echo "=========================================="
echo "後端部署完成！"
echo "=========================================="
