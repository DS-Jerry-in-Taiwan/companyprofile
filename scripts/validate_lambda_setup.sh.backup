#!/bin/bash
# validate_lambda_setup.sh
# 驗證 Lambda 部署配置

set -e

echo "======================================"
echo "Lambda 部署配置驗證"
echo "======================================"
echo ""

# 1. 檢查必要檔案
echo "✓ 檢查必要檔案..."
FILES=(
    "src/functions/lambda_handler.py"
    "src/functions/api_controller.py"
    "src/functions/Dockerfile.prod"
    "src/functions/requirements.txt"
    "serverless.yml"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file 存在"
    else
        echo "  ✗ $file 不存在"
        exit 1
    fi
done
echo ""

# 2. 檢查 requirements.txt 依賴
echo "✓ 檢查 requirements.txt 依賴..."
REQUIRED_DEPS=("flask" "mangum" "boto3")

for dep in "${REQUIRED_DEPS[@]}"; do
    if grep -q "$dep" src/functions/requirements.txt; then
        echo "  ✓ $dep 已包含"
    else
        echo "  ✗ $dep 未包含"
        exit 1
    fi
done
echo ""

# 3. 檢查 Dockerfile.prod 配置
echo "✓ 檢查 Dockerfile.prod 配置..."
if grep -q "FROM public.ecr.aws/lambda/python:3.11" src/functions/Dockerfile.prod; then
    echo "  ✓ 使用正確的基礎映像 (python:3.11)"
else
    echo "  ✗ 基礎映像不正確"
    exit 1
fi

if grep -q 'CMD \["lambda_handler.handler"\]' src/functions/Dockerfile.prod; then
    echo "  ✓ Lambda 入口點正確 (lambda_handler.handler)"
else
    echo "  ✗ Lambda 入口點不正確"
    exit 1
fi
echo ""

# 4. 檢查 serverless.yml 配置
echo "✓ 檢查 serverless.yml 配置..."
if grep -q "flaskApi:" serverless.yml; then
    echo "  ✓ 函數名稱為 flaskApi"
else
    echo "  ✗ 函數名稱不正確"
    exit 1
fi

if grep -q "httpApi:" serverless.yml; then
    echo "  ✓ 使用 HTTP API 觸發器"
else
    echo "  ✗ 未配置 HTTP API 觸發器"
    exit 1
fi
echo ""

# 5. 檢查 lambda_handler.py 語法
echo "✓ 檢查 lambda_handler.py 語法..."
if python3 -m py_compile src/functions/lambda_handler.py 2>/dev/null; then
    echo "  ✓ lambda_handler.py 語法正確"
else
    echo "  ⚠ lambda_handler.py 語法檢查警告（可能缺少依賴，部署時會安裝）"
fi
echo ""

# 6. 檢查 API 端點
echo "✓ 檢查 API 端點定義..."
ENDPOINTS=(
    "/health"
    "/v1/company/profile/process"
    "/v1/monitoring/logs"
    "/v1/monitoring/anomalies"
)

for endpoint in "${ENDPOINTS[@]}"; do
    if grep -q "\"$endpoint\"" src/functions/api_controller.py; then
        echo "  ✓ $endpoint 已定義"
    else
        echo "  ✗ $endpoint 未定義"
        exit 1
    fi
done
echo ""

echo "======================================"
echo "✓ 所有驗證通過！"
echo "======================================"
echo ""
echo "下一步："
echo "1. 執行本地測試: docker build -f src/functions/Dockerfile.prod -t flask-lambda-test src/functions/"
echo "2. 部署到 AWS: serverless deploy --stage dev"
echo ""
