# Developer Prompt: Stage 3 實作

**任務**: 執行 Stage 3 可觀測性提升優化  
**日期**: 2026-04-14  
**參考文件**: 
- `docs/agent_context/phase14_functionality_recovery/STAGE3_OBSERVABILITY_PLAN.md`
- `docs/agent_context/phase14_functionality_recovery/STAGE3_CHECKLIST.md`

---

## 任務概述

執行 Stage 3 的 6 個工作項目，每項需包含開發、測試、驗證三個階段。

---

## 實作順序

### 1. Bug 修復（按順序執行）

#### 1.1 Bug #1: `logger` 變數錯誤

**問題**:
```
[WARNING] Failed to process final result: cannot access local variable 'logger' where it is not associated with a value
```

**實作步驟**:
1. 在 `src/` 目錄搜尋 "logger" 變數使用，找出問題位置
2. 檢查程式碼路徑，確認 logger 在哪些情況下未初始化
3. 修復初始化邏輯或錯誤處理
4. **驗證**: `grep -r "cannot access local variable" src/`

**部署**: `./scripts/deploy_backend.sh --force`

**測試**:
```bash
curl -X POST https://51nhy1r3v7.execute-api.ap-northeast-1.amazonaws.com/v1/company/profile/process \
  -H "Content-Type: application/json" \
  -d '{"organNo":"1","organ":"私立揚才文理短期補習班","mode":"GENERATE"}'
```

**驗證日誌**:
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/organ-brief-optimization-dev-flaskApi \
  --filter-pattern "logger"
```

**成功標準**: 日誌中無 "cannot access local variable 'logger'" 警告

---

#### 1.2 Bug #2: Non-JSON 回應處理

**問題**:
```
[WARNING] Non-JSON response: 趨勢科技股份有限公司於1988年...
```

**實作步驟**:
1. 找出 LLM 回應解析的程式碼位置（可能在 `post_processing.py` 或 `company_brief_graph.py`）
2. 分析 LLM 為何回傳非 JSON 格式
3. 實作 JSON 解析失敗時的 fallback 處理邏輯
4. 加入有意義的錯誤訊息

**驗證**: 檢視程式碼確認有 fallback 邏輯

**部署**: `./scripts/deploy_backend.sh --force`

**測試**: 執行同一個測試請求

**驗證日誌**:
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/organ-brief-optimization-dev-flaskApi \
  --filter-pattern "Non-JSON"
```

**成功標準**: 
- Non-JSON 警告消失或變成有意義的錯誤訊息
- API 仍能正常返回資料

---

#### 1.3 Bug #3: 台灣用語轉換驗證

**實作步驟**:
1. 檢查 `src/functions/utils/post_processing.py` 中的 `_convert_to_taiwan_terms` 函式
2. 在轉換後加入統計日誌：
```python
def _convert_to_taiwan_terms(text: str) -> str:
    original_len = len(text)
    # ... 轉換邏輯 ...
    logger.info(f"[Taiwan Terms] 轉換前: {original_len} 字, 轉換後: {len(result)} 字")
    return result
```

**部署**: `./scripts/deploy_backend.sh --force`

**測試**: 執行同一個測試請求

**驗證日誌**:
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/organ-brief-optimization-dev-flaskApi \
  --filter-pattern "[Taiwan Terms]"
```

**成功標準**: 日誌中出現台灣用語轉換的統計記錄

---

### 2. Lambda X-Ray 啟用

**實作步驟**:

#### 選項 A: AWS Console（推薦）
1. 開啟 AWS Lambda Console
2. 選擇函數 `organ-brief-optimization-dev-flaskApi`
3. 點擊 "Configuration" → "Monitoring and troubleshooting tools"
4. 點擊 "Edit"
5. 啟用 "Active tracing" (X-Ray)
6. 點擊 "Save"

#### 選項 B: AWS CLI
```bash
aws lambda update-function-configuration \
  --function-name organ-brief-optimization-dev-flaskApi \
  --tracing-config Mode=Active
```

**驗證**:
1. 在 Lambda Console 查看 Monitoring 頁面，確認出現 X-Ray 圖表
2. 執行測試請求後，在 CloudWatch X-Ray 查看 traces

**成功標準**: CloudWatch X-Ray 中可看到 traces 清單

---

### 3. 各環節計時日誌

**實作步驟**:

1. 在 `src/functions/api_controller.py` 加入計時工具：
```python
import time
import logging
import contextlib

logger = logging.getLogger(__name__)

@contextlib.contextmanager
def measure(operation_name: str):
    """計時上下文管理器"""
    start = time.time()
    logger.info(f"[TIMING] {operation_name} 開始")
    try:
        yield
    finally:
        elapsed = (time.time() - start) * 1000
        logger.info(f"[TIMING] {operation_name} 完成，耗時 {elapsed:.2f}ms")
```

2. 在以下位置加入計時：
   - `api_controller.py`: 整體請求處理
   - `company_brief_graph.py` 的 `search_node`: 搜尋階段
   - `company_brief_graph.py` 的 `generate_node`: LLM 生成階段
   - `post_processing.py`: 後處理階段

**使用範例**:
```python
with measure("搜尋階段"):
    search_results = search_node(state)

with measure("LLM 生成"):
    result = generate_node(state)
```

**部署**: `./scripts/deploy_backend.sh --force`

**測試**: 執行測試請求

**驗證日誌**:
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/organ-brief-optimization-dev-flaskApi \
  --filter-pattern "[TIMING]"
```

**成功標準**: 日誌中出現各環節的計時記錄

---

### 4. 字數標準放寬

**實作步驟**:

1. 修改 `src/functions/utils/word_count_validator.py` 的範圍設定：
```python
# 原本
RANGES = {
    "concise": (40, 120),
    "standard": (130, 230),
    "detailed": (280, 550),
}

# 修改為
RANGES = {
    "concise": (40, 120),
    "standard": (130, 280),  # 上限放寬
    "detailed": (280, 700),  # 上限放寬
}
```

2. 修改 `src/functions/utils/template_differentiator.py` 的截斷邏輯：
   - 只有當內容超過 800 字才截斷
   - 其他情況只記錄警告，不截斷

**部署**: `./scripts/deploy_backend.sh --force`

**測試**: 執行 E2E 測試確認行為

**成功標準**: 
- 700 字以內的內容不截斷
- 超過 800 字的內容才截斷

---

## 完整驗證腳本

部署完成後，執行以下驗證：

```bash
#!/bin/bash
set -e

API_URL="https://51nhy1r3v7.execute-api.ap-northeast-1.amazonaws.com"
LOG_GROUP="/aws/lambda/organ-brief-optimization-dev-flaskApi"

echo "=========================================="
echo "Stage 3 驗證"
echo "=========================================="

echo ""
echo "1. 檢查 /version"
curl -s "$API_URL/version" | jq .

echo ""
echo "2. 觸發測試請求"
curl -s -X POST "$API_URL/v1/company/profile/process" \
  -H "Content-Type: application/json" \
  -d '{"organNo":"1","organ":"私立揚才文理短期補習班","mode":"GENERATE"}' | jq '.success'

echo ""
echo "3. 等待日誌寫入..."
sleep 5

echo ""
echo "4. 檢查 ERROR"
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern "ERROR" \
  --limit 3 || echo "無 ERROR"

echo ""
echo "5. 檢查計時日誌"
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern "[TIMING]" \
  --limit 5 || echo "無計時日誌"

echo ""
echo "6. 檢查台灣用語轉換"
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --filter-pattern "[Taiwan Terms]" \
  --limit 3 || echo "無台灣用語日誌"

echo ""
echo "=========================================="
echo "驗證完成"
echo "=========================================="
```

---

## 更新 Phase Context 文件

所有項目驗證通過後，更新以下文件：

### 1. 更新 `STAGE3_CHECKLIST.md`

將每個完成項目的勾選框改為 ✅

### 2. 更新 `PROGRESS_TRACKING.md`

```markdown
## Stage 3 完成項目 (2026-04-14)

| # | 項目 | 狀態 |
|---|------|------|
| 1 | Bug: logger 錯誤修復 | ✅ 完成 |
| 2 | Bug: Non-JSON 處理優化 | ✅ 完成 |
| 3 | Bug: 台灣用語驗證 | ✅ 完成 |
| 4 | Lambda X-Ray 啟用 | ✅ 完成 |
| 5 | 各環節計時日誌 | ✅ 完成 |
| 6 | 字數標準放寬 | ✅ 完成 |
```

### 3. 更新 `README.md`（如果需要）

更新版本號為 v0.2.1，添加 Stage 3 完成的功能。

---

## 預估時間

| 項目 | 預估時間 |
|------|---------|
| Bug #1: logger 錯誤 | 30分 |
| Bug #2: Non-JSON 處理 | 1小時 |
| Bug #3: 台灣用語驗證 | 1小時 |
| X-Ray 啟用 | 15分 |
| 計時日誌 | 2小時 |
| 字數標準放寬 | 1小時 |
| **總計** | **約 5-6 小時** |

---

## 成功標準

- [x] /version 端點正常回應
- [x] API 請求正常處理（success: true）
- [x] CloudWatch Logs 無 ERROR
- [x] 日誌中有 [TIMING] 計時記錄
- [x] 日誌中有 [Taiwan Terms] 轉換記錄
- [x] CloudWatch X-Ray 可看到 traces
- [x] PHASE 14 context 文件已更新

**完成日期**: 2026-04-14  
**實際工時**: ~6 小時
