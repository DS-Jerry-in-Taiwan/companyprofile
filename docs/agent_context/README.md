# Agent Context - 開發進度筆記

## Phase 39 完成摘要 (2026/05/12)

### LLM 輸出品質架構 — 三層防護

- ✅ **Phase A**: Prompt 自檢指令移除（4 處）+ system_instruction 加入
- ✅ **Phase B**: Gemini response_schema 強制 JSON + system_instruction 參數化
- ✅ **Phase C**: 後處理 Pipeline 化（11 個 Processor + 配置檔驅動）
- ✅ **Phase D**: 品質閘門（8 項檢查）+ 重試機制（最多 2 次，用盡回警語）

### 新增模組

| 模組 | 路徑 | 數量 |
|------|------|------|
| Processors | `src/processors/` | 15 檔案（含 11 個 Processor + Pipeline） |
| Quality | `src/quality/` | 2 檔案（Gate + Checks） |
| Retry | `src/retry/` | 1 檔案（RetryManager） |
| Config | `config/post_processing.json` | 1 檔案 |

### 端到端驗證

- ✅ STANDARD / CONCISE 模式 API 測試通過
- ✅ 品質閘門 8 項檢查全數驗證
- ✅ 重試用盡回傳警語機制測試通過
- ✅ Pipeline 配置檔啟停生效確認

---

## Phase 25 完成摘要 (2026/04/28)

### 數字格式清理
- ✅ `clean_number_format()` - 移除千位逗號 (e.g., "1,000,000" → "1000000")
- ✅ `simplify_number()` - 轉億/萬單位 (e.g., "1.5億", "500萬")

### Error Handler 三層架構
- ✅ **第一層** (`api_controller.py`): 3 個 except (ValidationError, LLMServiceError, Exception)
- ✅ **第二層** (`generate_brief.py`): 2 個 except (ExternalServiceError, Exception)  
- ✅ **第三層** (`company_brief_graph.py`): invoke() + post_process() try/except

### Error Code 精確化
- ✅ 新增 `SVC_008` = "Post-processing failed"
- ✅ error_handled 路徑根據錯誤類型分配對應 ErrorCode
- ✅ 正確的 API error response 結構 (`{ success: false, error: { code, message, details, trace_id } }`)

### P0/P1 漏洞修復
- ✅ `/health` endpoint 加 try/except
- ✅ `template.format()` 加 try/except
- ✅ `_load_template()` 加 try/except
- ✅ `json.dumps/loads` 已確認有 try/except

---

## Phase 26 進行中

### 問題描述
前端排版問題：結果顯示在下方，而非右側並排。

### 開發文件
- `docs/agent_context/phase26_frontend_layout_fix/phase26-frontend-layout-fix.md` - 開發規劃
- `docs/agent_context/phase26_frontend_layout_fix/DEVELOPMENT_LOG.md` - 開發日誌

### 待辦
1. 排查根本原因（可能是 CSS build cache、breakpoint 或元件樣式問題）
2. 修復 Layout (預計 30-60 min)
3. 回歸測試 (15 min)

---

## Commit 歷史 (dev-jerry)

```
696300c feat: 前端改為左右分欄 + 結果歷史堆疊 + 錯誤代碼與細節顯示
4819481 fix: error_handler_node 安全取值 + _load_template try/except
2085706 fix: invoke() error_handled 依錯誤類型分配對應 ErrorCode
e14314d fix: P0 error handler漏洞 - /health + LLM template.format
75a677b feat: 新增 SVC_008 Post-processing failed 錯誤代碼
51a53c8 fix: finalize_state/post_process 補上 try/except, 給 SVC_007
```

---

## 快速參考

### Error Code 映射表
| 關鍵字 | ErrorCode |
|-------|:---------:|
| 429/quota/rate limit | LLM_001 |
| timeout | SVC_002 |
| 搜尋失敗 | SVC_003 |
| template/KeyError | SVC_006 |
| post_process 失敗 | SVC_008 |

### 關鍵檔案位置
- `src/functions/api_controller.py` - API entry point + 第一層 error handler
- `src/functions/utils/generate_brief.py` - 第二層 error handler  
- `src/langgraph_state/company_brief_graph.py` - 第三層 error handler
- `src/functions/utils/error_handler.py` - ErrorCode 枚舉
- `frontend/src/App.vue` - 前端結果陣列管理
- `frontend/src/components/ResultPanel.vue` - 結果呈現

---

## Phase 33 完成摘要 (2026/05/05)

### Token 成本追蹤與 DB Schema 優化

#### DB Schema 變更
- ✅ **移除**: `tokens_used`、`search_tokens_used`、`duration_ms`
- ✅ **新增**: `prompt_tokens`、`completion_tokens`、`search_prompt_tokens`、`search_completion_tokens`、`search_model`、`search_latency_ms`、`total_latency_ms`

#### Token 記錄
- ✅ 全流程 LLM 呼叫盤點：搜尋(1 call) + 生成(1 call) = 每請求 2 次
- ✅ input/output token 拆分記錄（`prompt_token_count` / `candidates_token_count`）
- ✅ 搜尋階段補上 token 記錄（`search_tools.py` 4 個工具）
- ✅ 合併搜尋 + 生成為同一筆 DB 記錄

#### Latency 定義
- ✅ `latency_ms` = 生成階段 API 時間
- ✅ `search_latency_ms` = 搜尋階段時間
- ✅ `total_latency_ms` = 端到端總時間

#### 其他
- ✅ Few-shot 選取改為隨機 1~2 種風格（取代全部選取）
- ✅ 移除 `WE_MIXED_ERROR` 反例
- ✅ `SearchResult` 新增 `model_name` 欄位取代 `tool_type`

#### 開發文件
- `docs/agent_context/phase33/DEVELOPMENT_LOG.md` - 開發日誌
- `docs/agent_context/phase33/DEVELOPMENT_PLAN.md` - 開發規劃
