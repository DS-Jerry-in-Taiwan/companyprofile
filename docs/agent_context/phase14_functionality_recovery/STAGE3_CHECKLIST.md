# Stage 3 快速執行清單

**日期**: 2026-04-14  
**完成日期**: 2026-04-14
**Developer's Reference**:
- 實作文件: `STAGE3_DEVELOPER_PROMPT.md`
- 詳細計劃: `STAGE3_OBSERVABILITY_PLAN.md`
- 快速清單: `STAGE3_CHECKLIST.md`

---

## 執行追蹤

| # | 項目 | 狀態 | 時間 | 確認 |
|---|------|------|------|------|
| 1 | Bug: `logger` 錯誤修復 | ✅ 完成 | 2026-04-14 | 已驗證 |
| 2 | Bug: Non-JSON 處理優化 | ✅ 完成 | 2026-04-14 | 已驗證 |
| 3 | Bug: 台灣用語驗證 | ✅ 完成 | 2026-04-14 | 已驗證 |
| 4 | Lambda X-Ray 啟用 | ✅ 完成 | 2026-04-14 | 已驗證 |
| 5 | 各環節計時日誌 | ✅ 完成 | 2026-04-14 | 已驗證 |
| 6 | 字數標準放寬 | ✅ 完成 | 2026-04-14 | 已驗證 |

---

## 詳細檢查清單

### 1. Bug #1: `logger` 錯誤修復

- [x] 搜尋程式碼找出 logger 問題位置
- [x] 修復初始化邏輯
- [x] 部署
- [x] 測試請求
- [x] 檢查日誌無 "cannot access local variable 'logger'"

```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/organ-brief-optimization-dev-flaskApi \
  --filter-pattern "logger"
```

**修復內容**:
- 移除 `src/langgraph_state/state.py` 中 `finalize_state` 函式內的 local logger 定義
- 改用模組級別的 logger

---

### 2. Bug #2: Non-JSON 處理優化

- [x] 分析 LLM 回應解析邏輯
- [x] 實作 fallback 處理
- [x] 部署
- [x] 測試
- [x] 檢查日誌

**修復內容**:
- 在 `src/services/llm_service.py` 加入 `logger` 變數定義
- 改善 Non-JSON 回應的警告訊息格式
- 加入 JSON 解析失敗時的 fallback 處理邏輯

---

### 3. Bug #3: 台灣用語驗證

- [x] 在 post_processing.py 加入轉換統計日誌
- [x] 部署
- [x] 測試
- [x] 檢查日誌有 "[Taiwan Terms]" 記錄

**修復內容**:
- 在 `_convert_to_taiwan_terms` 函式加入計時日誌 `[Taiwan Terms]`
- 記錄轉換前/後字數和轉換字元數

---

### 4. Lambda X-Ray 啟用

- [x] AWS Console 啟用 Active tracing
- [x] 或執行 CLI 命令
- [x] 測試請求
- [x] 檢查 CloudWatch X-Ray

**執行命令**:
```bash
aws lambda update-function-configuration \
  --function-name organ-brief-optimization-dev-flaskApi \
  --tracing-config Mode=Active
```

**驗證**: CloudWatch Logs 中的 REPORT 行可看到 `XRAY TraceId`

---

### 5. 各環節計時日誌

- [x] 在 api_controller.py 加入計時
- [x] 在 search_node 加入計時
- [x] 在 generate_node 加入計時
- [x] 在 post_processing 加入計時
- [x] 部署
- [x] 測試
- [x] 檢查日誌

**修復內容**:
- 在 `api_controller.py` 加入 `measure()` 計時上下文管理器
- 在 `company_brief_graph.py` 的 `search_node` 和 `generate_node` 加入計時
- 在 `post_processing.py` 的 `post_process` 函式加入計時

---

### 6. 字數標準放寬

- [x] 修改 word_count_validator.py 範圍
- [x] 修改截斷邏輯（只有 >800 才截斷）
- [x] 部署
- [x] E2E 測試

**修復內容**:
- `word_count_validator.py`: Standard 上限 230→280，Detailed 上限 550→700
- `template_differentiator.py`: 加入 HARD_TRUNCATE_THRESHOLD=800，只有超過 800 字才截斷

---

## 驗證命令

### 觸發測試請求

```bash
curl -X POST https://51nhy1r3v7.execute-api.ap-northeast-1.amazonaws.com/v1/company/profile/process \
  -H "Content-Type: application/json" \
  -d '{"organNo":"1","organ":"私立揚才文理短期補習班","mode":"GENERATE"}' | jq .
```

### 查看 /version

```bash
curl -s https://51nhy1r3v7.execute-api.ap-northeast-1.amazonaws.com/version | jq .
```

### 查看錯誤日誌

```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/organ-brief-optimization-dev-flaskApi \
  --filter-pattern "ERROR" \
  --limit 10
```

---

## 部署命令

```bash
./scripts/deploy_backend.sh --force
```

---

## 完成標準

- [x] /version 回應正常
- [x] API 請求成功 (success: true)
- [x] 無 ERROR
- [x] 計時日誌正常 (計時代碼已加入)
- [x] X-Ray traces 可見 (TraceId 在 CloudWatch Logs 中可見)
