# Stage 3: 可觀測性提升工作計劃

**建立日期**: 2026-04-14  
**狀態**: 待執行  
**預估工時**: 6 小時

---

## 1. 概述

### 1.1 工作目標

| 目標 | 說明 |
|------|------|
| 程式碼品質 | 消除 ERROR/WARNING |
| 可觀測性 | 可追蹤任請求的完整流程 |
| 數據驅動 | 有各環節時間數據可分析瓶頸 |

### 1.2 工作項目清單

| # | 項目 | 優先級 | 預估工時 |
|---|------|--------|---------|
| 1 | Bug: `logger` 變數錯誤修復 | 🔴 高 | 30分 |
| 2 | Bug: Non-JSON 回應處理優化 | 🔴 高 | 1小時 |
| 3 | 台灣用語轉換驗證 | 🟡 中 | 1小時 |
| 4 | Lambda 啟用 X-Ray 追蹤 | 🟡 中 | 30分 |
| 5 | 各環節計時日誌 | 🟡 中 | 2小時 |
| 6 | 字數標準放寬調整 | 🟢 低 | 1小時 |

---

## 2. Bug 修復

### 2.1 Bug #1: `logger` 變數錯誤

#### 問題描述

```
[WARNING] Failed to process final result: cannot access local variable 'logger' where it is not associated with a value
```

#### 開發步驟

| Step | 動作 | 驗證 |
|------|------|------|
| 1 | 在程式碼中搜尋 "logger" 變數使用 | 找出所有使用點 |
| 2 | 檢查 logger 是否在所有 code path 都有初始化 | 確認問題位置 |
| 3 | 修復 logger 初始化或錯誤處理邏輯 | - |
| 4 | 更新 serverless.yml 重新部署 | 部署完成 |
| 5 | 觸發一次 API 請求 | 無 ERROR |
| 6 | 檢查 CloudWatch Logs | 無 "logger" 相關警告 |

#### 驗證標準

```
✅ Lambda 日誌中無 "cannot access local variable 'logger'" 警告
✅ 所有請求都正常完成
```

#### 驗證命令

```bash
# 查看最近 30 分鐘的錯誤日誌
aws logs filter-log-events \
  --log-group-name /aws/lambda/organ-brief-optimization-dev-flaskApi \
  --start-time $(date -d '30 minutes ago' +%s000) \
  --filter-pattern "logger"
```

---

### 2.2 Bug #2: Non-JSON 回應處理

#### 問題描述

```
[WARNING] Non-JSON response: 趨勢科技股份有限公司於1988年...
```

LLM 回傳純文字而非 JSON 格式，導致後處理出現警告。

#### 開發步驟

| Step | 動作 | 驗證 |
|------|------|------|
| 1 | 找出 LLM 回應解析的程式碼位置 | 確認程式碼 |
| 2 | 分析 LLM 為何回傳非 JSON | 查看日誌 |
| 3 | 設計 fallback 處理邏輯 | - |
| 4 | 實作 JSON 解析失敗時的處理 | - |
| 5 | 加入更有意義的警告訊息 | - |
| 6 | 部署並測試 | - |

#### 驗證標準

```
✅ Non-JSON 警告消失或變成有意義的錯誤訊息
✅ 即使 LLM 回應格式異常，API 仍能正常返回
```

#### 驗證命令

```bash
# 測試 API 並檢查日誌
curl -X POST https://51nhy1r3v7.execute-api.ap-northeast-1.amazonaws.com/v1/company/profile/process \
  -H "Content-Type: application/json" \
  -d '{"organNo":"1","organ":"私立揚才文理短期補習班","mode":"GENERATE"}'

aws logs filter-log-events \
  --log-group-name /aws/lambda/organ-brief-optimization-dev-flaskApi \
  --filter-pattern "Non-JSON" \
  --limit 5
```

---

### 2.3 Bug #3: 台灣用語轉換驗證

#### 問題描述

台灣用語轉換模組已實作但需要確認是否正常運作。

#### 開發步驟

| Step | 動作 | 驗證 |
|------|------|------|
| 1 | 檢查 `post_processing.py` 中的轉換邏輯 | 確認程式碼 |
| 2 | 在轉換後加入統計日誌 | - |
| 3 | 部署並測試 | - |
| 4 | 檢查日誌中的轉換統計 | - |

#### 驗證標準

```
✅ 日誌中有台灣用語轉換的統計資訊
✅ 確認轉換有實際運作（chars_converted > 0）
```

#### 程式碼修改位置

`src/functions/utils/post_processing.py`:
```python
def _convert_to_taiwan_terms(text: str) -> str:
    """轉換為台灣用語"""
    logger.info(f"[Taiwan Terms] 轉換前字數: {len(text)}")
    
    # ... 轉換邏輯 ...
    
    logger.info(f"[Taiwan Terms] 轉換後字數: {len(result)}, 轉換字元數: {chars_converted}")
    return result
```

#### 驗證命令

```bash
# 查看台灣用語轉換日誌
aws logs filter-log-events \
  --log-group-name /aws/lambda/organ-brief-optimization-dev-flaskApi \
  --filter-pattern "[Taiwan Terms]" \
  --limit 10
```

---

## 3. Lambda X-Ray 追蹤設定

### 3.1 啟用 X-Ray

#### AWS Console 步驟

| Step | 動作 |
|------|------|
| 1 | 開啟 AWS Lambda Console |
| 2 | 選擇函數 `organ-brief-optimization-dev-flaskApi` |
| 3 | 點擊 "Configuration" 頁籤 |
| 4 | 點擊 "Monitoring and troubleshooting tools" |
| 5 | 點擊 "Edit" |
| 6 | 啟用 "Active tracing" (X-Ray) |
| 7 | 點擊 "Save" |

#### CLI 步驟（替代方案）

```bash
aws lambda update-function-configuration \
  --function-name organ-brief-optimization-dev-flaskApi \
  --tracing-config Mode=Active
```

#### IAM 權限設定

X-Ray 會自動新增權限到 Lambda Execution Role，確認有以下權限：

```json
{
  "Effect": "Allow",
  "Action": [
    "xray:PutTraceSegments",
    "xray:PutTelemetryRecords",
    "xray:GetSamplingRules",
    "xray:GetSamplingTargets"
  ],
  "Resource": "*"
}
```

#### 驗證步驟

| Step | 動作 | 驗證 |
|------|------|------|
| 1 | 在 AWS Console 查看 Lambda Monitoring | 出現 X-Ray traces 圖表 |
| 2 | 觸發一次 API 請求 | - |
| 3 | 開啟 CloudWatch X-Ray Service Map | 出現服務節點 |
| 4 | 點擊 traces 查看詳細時間 | 可看到各環節時間 |

#### 驗證標準

```
✅ Lambda Monitoring 中出現 X-Ray 追蹤圖表
✅ CloudWatch X-Ray 可看到 traces 清單
✅ 可點擊查看單次請求的時間分布
```

---

## 4. 各環節計時日誌

### 4.1 目標

在每個主要環節加入計時日誌，格式：

```
[TIMING] {環節名稱} 完成，耗時 {X}ms
```

### 4.2 需要計時的環節

| 環節 | 位置 | 說明 |
|------|------|------|
| 請求接收 | api_controller.py | 接收請求到開始處理 |
| 搜尋階段 | company_brief_graph.py | Tavily/Gemini 搜尋 |
| LLM 生成 | company_brief_graph.py | Gemini 生成簡介 |
| 後處理 | post_processing.py | 台灣用語、HTML 處理 |
| 總耗時 | api_controller.py | 整體流程 |

### 4.3 開發步驟

| Step | 動作 | 驗證 |
|------|------|------|
| 1 | 在 `api_controller.py` 加入計時裝飾器或計時包裝 | - |
| 2 | 在 `company_brief_graph.py` 的 `search_node` 加入計時 | - |
| 3 | 在 `company_brief_graph.py` 的 `generate_node` 加入計時 | - |
| 4 | 在 `post_processing.py` 的主要函式加入計時 | - |
| 5 | 部署並測試 | - |
| 6 | 查看 CloudWatch Logs 確認計時日誌 | - |

### 4.4 計時日誌格式

```python
import time
import logging

logger = logging.getLogger(__name__)

class TimingLogger:
    """計時工具"""
    
    @contextmanager
    def measure(self, operation_name: str):
        start_time = time.time()
        logger.info(f"[TIMING] {operation_name} 開始")
        try:
            yield
        finally:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"[TIMING] {operation_name} 完成，耗時 {elapsed_ms:.2f}ms")

# 使用方式
with timing_logger.measure("搜尋階段"):
    search_results = search_node(state)
```

### 4.5 驗證標準

```
✅ 日誌中出現 "[TIMING]" 標記
✅ 每個環節都有耗時記錄
✅ 可從日誌計算出總耗時
```

#### 驗證命令

```bash
# 查看計時日誌
aws logs filter-log-events \
  --log-group-name /aws/lambda/organ-brief-optimization-dev-flaskApi \
  --filter-pattern "[TIMING]" \
  --limit 20
```

---

## 5. 字數標準放寬

### 5.1 調整方向

| 模板 | 原本範圍 | 新範圍 | 變更 |
|------|---------|--------|------|
| CONCISE | 40-120 | 40-120 | 不變 |
| STANDARD | 130-230 | 130-280 | 上限放寬 50 字 |
| DETAILED | 280-550 | 280-700 | 上限放寬 150 字 |

### 5.2 截斷策略調整

| 原本策略 | 新策略 |
|---------|--------|
| 超出範圍就截斷 | 只有超過 800 字才截斷 |
| LLM 重寫 | 移除重寫機制 |

### 5.3 開發步驟

| Step | 動作 | 驗證 |
|------|------|------|
| 1 | 修改 `word_count_validator.py` 的範圍設定 | - |
| 2 | 修改 `template_differentiator.py` 的截斷邏輯 | - |
| 3 | 部署並測試 | - |
| 4 | 執行 E2E 測試確認行為 | - |

### 5.4 驗證標準

```
✅ 字數超出 700 字（小於 800）時不截斷
✅ 字數超過 800 字時才截斷
✅ CONCISE 維持 40-120 字範圍
```

---

## 6. 部署流程

### 6.1 部署前檢查清單

```
☐ 所有修改已 commit 到 Git
☐ Git working tree 是乾淨的（無未提交的改動）
☐ 測試程式碼已準備
```

### 6.2 部署步驟

```bash
# 1. 確認 Git 狀態
git status --short

# 2. 部署
./scripts/deploy_backend.sh --force

# 3. 等待部署完成（約 1-2 分鐘）
```

### 6.3 驗證清單

```
☐ /version 端點正常回應
☐ API 請求正常處理
☐ CloudWatch Logs 無 ERROR
☐ 計時日誌正常輸出
☐ X-Ray traces 出現
```

---

## 7. 驗證命令腳本

建立一個驗證腳本 `scripts/verify_stage3.sh`:

```bash
#!/bin/bash

echo "=========================================="
echo "Stage 3 驗證腳本"
echo "=========================================="

API_URL="https://51nhy1r3v7.execute-api.ap-northeast-1.amazonaws.com"
LOG_GROUP="/aws/lambda/organ-brief-optimization-dev-flaskApi"

echo ""
echo "1. 檢查 /version 端點"
curl -s "$API_URL/version" | jq .

echo ""
echo "2. 觸發測試請求"
RESPONSE=$(curl -s -X POST "$API_URL/v1/company/profile/process" \
  -H "Content-Type: application/json" \
  -d '{"organNo":"1","organ":"私立揚才文理短期補習班","mode":"GENERATE"}')
echo "$RESPONSE" | jq '.success'

echo ""
echo "3. 等待 5 秒讓日誌寫入..."
sleep 5

echo ""
echo "4. 檢查 ERROR 數量"
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern "ERROR" \
  --limit 5

echo ""
echo "5. 檢查計時日誌"
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern "[TIMING]" \
  --limit 5

echo ""
echo "6. 檢查 logger 錯誤"
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern "cannot access local variable" \
  --limit 5

echo ""
echo "=========================================="
echo "驗證完成"
echo "=========================================="
```

---

## 8. 完成標準

### 8.1 功能驗收

| 項目 | 標準 |
|------|------|
| API 正常運作 | 所有請求返回 success: true |
| 無 ERROR | CloudWatch Logs 中 ERROR 數量 = 0 |
| 計時日誌 | 每個環節都有 [TIMING] 記錄 |
| X-Ray | CloudWatch X-Ray 中可看到 traces |
| 字數標準 | 超出 700 字但不超過 800 字的內容不截斷 |

### 8.2 文件更新

| 文件 | 更新內容 |
|------|---------|
| README.md | 更新版本為 v0.2.1 |
| stage3_planning.md | 更新為「已完成」狀態 |
| PROGRESS_TRACKING.md | 記錄完成的工作項目 |

---

## 9. 預估工時總結

| 項目 | 預估工時 | 實際工時 |
|------|---------|---------|
| Bug #1: logger 錯誤 | 30分 | |
| Bug #2: Non-JSON 處理 | 1小時 | |
| Bug #3: 台灣用語驗證 | 1小時 | |
| Lambda X-Ray 啟用 | 30分 | |
| 計時日誌 | 2小時 | |
| 字數標準放寬 | 1小時 | |
| **總計** | **6小時** | |

---

## 10. 風險評估

| 風險 | 影響 | 緩解措施 |
|------|------|---------|
| X-Ray 可能增加 Lambda 延遲 | 低 | X-Ray overhead 很小（<5ms） |
| 計時日誌過多 | 低 | 只在 DEBUG 模式開啟計時 |
| 破壞現有功能 | 中 | 部署前在地端測試 |

---

**文件建立**: 2026-04-14  
**更新日期**: 2026-04-14  
**負責**: Development Agent
