# Agent Context - 開發進度筆記

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
- `docs/agent_context/phase26_frontend_layout_fix/phase26-frontend-layout-fix.md`

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