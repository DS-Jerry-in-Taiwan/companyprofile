#!/bin/bash
# Phase 29 API 實際驗證腳本
# 對 10 家測試公司呼叫真實 API，掃描輸出是否含中國用語
# 使用方式: bash scripts/test_phase29_live_api.sh

set -e

API_URL="https://datasciencealb-dev.1111.com.tw/organ-brief-dev/api/recurit/optimize/v1/company/profile/process"

# 10 家測試公司（包含 3 種模式）
COMPANIES=(
    '{"organ": "Crystal手工義大利麵", "organNo": "117234127", "mode": "GENERATE", "optimization_mode": "STANDARD"}'
    '{"organ": "國祥工程行", "organNo": "73569327", "mode": "GENERATE", "optimization_mode": "STANDARD"}'
    '{"organ": "學悟處一對一文理補習班", "organNo": "72530562", "mode": "GENERATE", "optimization_mode": "DETAILED"}'
    '{"organ": "莫索造型沙龍", "organNo": "10430056", "mode": "GENERATE", "optimization_mode": "CONCISE"}'
    '{"organ": "圓緻空間設計工作室", "organNo": "117159915", "mode": "GENERATE", "optimization_mode": "DETAILED"}'
    '{"organ": "瑞昱半導體股份有限公司", "organNo": "7039", "mode": "GENERATE", "optimization_mode": "STANDARD"}'
    '{"organ": "家立淨", "organNo": "71533095", "mode": "GENERATE", "optimization_mode": "CONCISE"}'
    '{"organ": "銳碁資訊股份有限公司", "organNo": "71696526", "mode": "GENERATE", "optimization_mode": "STANDARD"}'
    '{"organ": "全家便利商店", "organNo": "69588457", "mode": "GENERATE", "optimization_mode": "STANDARD"}'
    '{"organ": "基隆市衛生局", "organNo": "73164462", "mode": "GENERATE", "optimization_mode": "STANDARD"}'
)

# 中國用語檢查清單（含 OpenCC 可處理和不可處理的）
CN_TERMS=("網絡" "打印機" "服務器" "內存" "鼠標" "硬盤" "軟件" "光盤"
          "視頻" "音頻" "短信" "出租車" "地鐵" "快遞" "打印" "外賣"
          "小區" "物業" "輔導班" "筆記本電腦" "光驅" "光碟機")

echo "========================================="
echo "  Phase 29 API 實際驗證"
echo "  三層防護：bug fix + prompt + terms.json"
echo "========================================="
echo ""

total=0
pass=0
failed_companies=()

for company_json in "${COMPANIES[@]}"; do
    total=$((total + 1))
    organ=$(echo "$company_json" | python3 -c "import sys,json; print(json.load(sys.stdin)['organ'])")
    mode=$(echo "$company_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('optimization_mode','STANDARD'))")
    
    echo "[$total/10] $organ ($mode)..."
    
    # 呼叫 API，取得 body 和 http code
    response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "$company_json")
    
    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" != "200" ]; then
        echo "  ⚠️  HTTP $http_code（略過）"
        failed_companies+=("$organ (HTTP $http_code)")
        continue
    fi
    
    # 從回應中取出 body_html 和 summary
    full_text=$(echo "$body" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    body = data.get('body_html', '') or ''
    summary = data.get('summary', '') or ''
    print(body + ' ' + summary)
except:
    print('')
")
    
    # 檢查中國用語
    found=()
    for term in "${CN_TERMS[@]}"; do
        if echo "$full_text" | grep -q "$term"; then
            found+=("$term")
        fi
    done
    
    if [ ${#found[@]} -eq 0 ]; then
        echo "  ✅ 無中國用語"
        pass=$((pass + 1))
    else
        echo "  ❌ 發現中國用語: ${found[*]}"
        failed_companies+=("$organ (${found[*]})")
    fi
done

echo ""
echo "========================================="
echo "  驗證結果"
echo "========================================="
echo "  通過: $pass/$total"
echo ""

if [ ${#failed_companies[@]} -gt 0 ]; then
    echo "  失敗清單:"
    for item in "${failed_companies[@]}"; do
        echo "    ❌ $item"
    done
    exit 1
else
    echo "  ✅ 全部通過！"
fi
