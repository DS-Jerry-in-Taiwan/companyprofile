#!/bin/bash
# ALB 健康檢查腳本（支援 dev / prod）
# 用法:
#   ./scripts/check_alb_health.sh          # 預設 dev
#   ./scripts/check_alb_health.sh dev      # dev 環境
#   ./scripts/check_alb_health.sh prod     # prod 環境

set -e

STAGE="${1:-dev}"

case "$STAGE" in
  dev)
    ALB_DNS="1111datasciencedev-aloadbalancer-1333785764.ap-northeast-1.elb.amazonaws.com"
    BASE_PATH="/organ-brief-dev/api/recurit/optimize"
    ;;
  prod)
    ALB_DNS="1111datascience-aloadbalancer-575563269.ap-northeast-1.elb.amazonaws.com"
    BASE_PATH="/organ-brief-prd/api/recurit/optimize"
    ;;
  *)
    echo "❌ 未知 stage: $STAGE (請用 dev 或 prod)"
    exit 1
    ;;
esac

echo "=========================================="
echo "  ALB Health Check — ${STAGE}"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# 1. Health Check
echo ""
echo "[1/3] Health Endpoint"
HEALTH_URL="https://${ALB_DNS}${BASE_PATH}/health"
echo "  URL: $HEALTH_URL"
RESULT=$(curl -s --insecure --connect-timeout 10 "$HEALTH_URL" 2>&1)
if echo "$RESULT" | grep -q "healthy"; then
    echo "  ✅ Service is healthy"
    echo "  Response: $RESULT"
else
    echo "  ❌ Service unavailable"
    echo "  Response: $RESULT"
fi

# 2. API 功能測試
echo ""
echo "[2/3] API Function Test"
API_URL="https://${ALB_DNS}${BASE_PATH}/v1/company/profile/process"
echo "  URL: $API_URL"
RESULT=$(curl -s --insecure --connect-timeout 120 -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"organ":"台積電","organNo":"22099131","mode":"GENERATE","optimization_mode":"STANDARD"}' 2>&1)

SUCCESS=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('code','FAIL'))" 2>/dev/null)
BODY_LEN=$(echo "$RESULT" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('body_html','')))" 2>/dev/null)

if [ "$SUCCESS" = "SUCCESS" ] || [ "$SUCCESS" = "QUALITY_EXHAUSTED" ]; then
    echo "  ✅ API call succeeded (code=$SUCCESS)"
    echo "  Body length: ${BODY_LEN} chars"
else
    echo "  ❌ API call failed"
    echo "  Response: $(echo "$RESULT" | head -c 300)"
fi

# 3. 版本資訊
echo ""
echo "[3/3] Version Check"
VERSION_URL="https://${ALB_DNS}${BASE_PATH}/version"
VERSION=$(curl -s --insecure --connect-timeout 10 "$VERSION_URL" 2>&1)
echo "  Version: $VERSION"

echo ""
echo "=========================================="
echo "  ✅ Check completed (${STAGE})"
echo "=========================================="
