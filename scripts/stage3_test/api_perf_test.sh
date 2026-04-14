#!/bin/bash
# API 效能測試腳本

API_URL="http://localhost:5000"
COMPANY="私立揚才文理短期補習班"
ITERATIONS=3

echo "=========================================="
echo "API 效能測試"
echo "=========================================="
echo "URL: $API_URL"
echo "公司: $COMPANY"
echo "測試次數: $ITERATIONS"
echo ""

for i in $(seq 1 $ITERATIONS); do
    echo "第 $i/$ITERATIONS 次測試..."
    
    START=$(date +%s%3N)
    
    RESPONSE=$(curl -s -X POST "$API_URL/v1/company/profile/process" \
      -H "Content-Type: application/json" \
      -d "{\"organNo\":\"1\",\"organ\":\"$COMPANY\",\"mode\":\"GENERATE\"}" \
      --max-time 60)
    
    END=$(date +%s%3N)
    ELAPSED=$((END - START))
    
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // "error"' 2>/dev/null)
    
    echo "  耗時: ${ELAPSED}ms"
    echo "  成功: $SUCCESS"
    echo ""
    
    # 等待 3 秒再下一次測試
    if [ $i -lt $ITERATIONS ]; then
        sleep 3
    fi
done

echo "=========================================="
echo "測試完成"
echo "=========================================="
