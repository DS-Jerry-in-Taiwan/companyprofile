#!/bin/bash
# ALB 健康檢查腳本
# 用法: ./scripts/check_alb_health.sh

ALB_DNS="1111datasciencedev-aloadbalancer-1333785764.ap-northeast-1.elb.amazonaws.com"
BASE_PATH="/organ-brief-dev/api/recurit/optimize"

echo "=========================================="
echo "  ALB Health Check"
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
echo "[2/3] API Function Test (STANDARD mode)"
API_URL="https://${ALB_DNS}${BASE_PATH}/v1/company/profile/process"
echo "  URL: $API_URL"
RESULT=$(curl -s --insecure --connect-timeout 120 -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"organ":"台積電","organNo":"22099131","mode":"GENERATE","optimization_mode":"STANDARD"}' 2>&1)

if echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('success') else 1)" 2>/dev/null; then
    BODY_LEN=$(echo "$RESULT" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('body_html','')))" 2>/dev/null)
    echo "  ✅ API call succeeded"
    echo "  Body length: ${BODY_LEN} chars"
    
    # 檢查異常文字
    HAS_BAD=$(echo "$RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
b = d.get('body_html','')
for kw in ['Correct','Final check','【正確輸出】','**']:
    if kw in b:
        print('yes')
        sys.exit(0)
print('no')
" 2>/dev/null)
    if [ "$HAS_BAD" = "yes" ]; then
        echo "  ❌ 內容含異常文字!"
    else
        echo "  ✅ 無異常文字"
    fi
else
    echo "  ❌ API call failed"
    echo "  Response: $(echo "$RESULT" | head -c 200)"
fi

# 3. 版本資訊
echo ""
echo "[3/3] Version Check"
VERSION_URL="https://${ALB_DNS}${BASE_PATH}/version"
echo "  URL: $VERSION_URL"
VERSION=$(curl -s --insecure --connect-timeout 10 "$VERSION_URL" 2>&1)
echo "  Version: $VERSION"

echo ""
echo "=========================================="
echo "  Check completed"
echo "=========================================="
