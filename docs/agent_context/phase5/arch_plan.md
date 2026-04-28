# Phase 5 - ARCH 執行計畫 (arch_plan)

此文件為 Phase5 最終測試、優化與交付的可執行計畫，供各 Agent（@INFRA / @ANALYST / @CODER / @ARCH）依序執行。

總原則：每一步都要產生可驗證的輸出檔案；產出物放置於 repo 的 docs/ 與 scripts/ 目錄下，並於每個 Checkpoint 進行 PASS/FAIL 審核。

---------------------------------
Step 1 - 測試環境與監控配置（負責：@INFRA）
- 目標：建立可重現的測試資料夾、啟動或準備監控與耗時紀錄機制
- 具體動作：
  1. 建立資料夾與樣本位置：
     - 建立 data/test_samples/，放入至少 30 筆 JSON 或 CSV 樣本（不同產業、不同規模）
     - 每筆樣本包含：company_name, industry, size, seed_query（必要欄位）
     - 輸入檔案範例路徑：data/test_samples/sample_template.json
  2. 實作輕量監控/計時器腳本：
     - scripts/perf_timer.py：可在呼叫 API 前後紀錄時間戳、階段標籤（search, clean, llm_generate）、耗時(ms)、token_consumed（若可得）
     - scripts/token_cost_logger.py：每次呼叫紀錄 token 數與估算成本（依照 config/token_price.json）
  3. 日誌/監控：若不可部署 Prometheus，可先實作 CSV Logger：logs/perf_logs.csv
  4. 準備監控說明文件：docs/monitoring_setup.md （含如何用 CSV 生成簡易 Grafana 圖表或匯入 Prometheus）
- 輸入：無（從 repo）
- 輸出：data/test_samples/*, scripts/perf_timer.py, scripts/token_cost_logger.py, logs/perf_logs.csv（由執行產出）、docs/monitoring_setup.md
- 估時：1.5 小時

---------------------------------
Step 2 - 規模化測試與幻覺評核（負責：@ANALYST）
- 目標：使用批次腳本對 >20 筆樣本產生結果，並標註幻覺/事實不一致處
- 具體動作：
  1. 撰寫批次測試 Runner：scripts/batch_test.py
     - 功能：載入 data/test_samples/*，對每個樣本執行 pipeline，使用 scripts/perf_timer.py 記錄各階段耗時
     - 輸出：outputs/generated_results/<sample_id>.json 與一個總表 docs/final_test_report.csv（每列包含 sample_id, company_name, industry, size, latency_total_s, tokens_used, hallucination_flag, hallucination_notes）
  2. 幻覺檢查模板：scripts/hallucination_checker.py（或 notebooks/hallucination_check.ipynb）
     - 功能：比對搜尋原始來源（若有）與生成內容，並回報可能的 Hallucination（高亮判定詞、來源差異）
     - 輸出補助檔 docs/hallucination_samples.md（列出疑似幻覺範例）
  3. 產出品質報告：docs/final_quality_report.md（包含準確性、吸引力、合規性三個指標的量化評分）
  4. 觸發 Checkpoint 1（見下方審核清單）
- 輸入：data/test_samples/*、scripts/perf_timer.py
- 輸出：outputs/generated_results/*、docs/final_test_report.csv、docs/final_quality_report.md、docs/hallucination_samples.md
- 估時：2.5 小時（含人工/AI 協助的品質判定）

---------------------------------
Step 3 - 代碼修補與細節優化（負責：@CODER）
- 目標：根據 Checkpoint 1 的測試回饋修正 Bug、優化 Prompt 與輸出格式
- 具體動作：
  1. 分析 docs/final_quality_report.md 與 docs/hallucination_samples.md 中的重點問題
  2. 修補項目（範例）：
     - 處理特殊字元導致的解析錯誤（修正 parser）：src/utils/cleaner.py
     - 調整 Prompt 模板或模型參數：src/prompt_templates/*.md
     - 加強 length 與 edge-case 處理（當生成過短或過長時 fallback 政策）
     - 清理冗餘 print/DEBUG 日誌（在 logging config 中設為 DEBUG 層級）
  3. 更新單元測試或增加 E2E 測試：scripts/e2e_runner.py（模擬 3-5 個典型樣本的端到端流程，確認無 error）
  4. 更新 CHANGELOG：docs/CHANGELOG_PHASE5.md（列出修復與優化項目）
- 輸入：docs/final_quality_report.md
- 輸出：修改後源碼（src/**）、scripts/e2e_runner.py、docs/CHANGELOG_PHASE5.md
- 估時：2 小時

---------------------------------
Step 4 - 性能調校、最終評核與交付（負責：@ARCH + @ANALYST）
- 目標：確認性能與成本指標、整理最終交付文檔並觸發 Checkpoint 2
- 具體動作：
  1. 性能回顧：使用 logs/perf_logs.csv 與 scripts/perf_timer.py 的輸出，計算平均 latency、P95、token 平均與總成本（scripts/perf_analysis.py）
  2. 若平均 latency > 20s 或 P95 > 30s，列出優化清單（如：採用更小模型、非同步化搜尋、快取策略）並估算影響成本
  3. 完成最終文件：
     - README.md（包含系統架構圖、安裝與 API 使用範例）
     - docs/architecture_v1.md（系統架構、模組說明、部署 topology）
     - docs/final_delivery_summary.md（專案摘要、測試結果概覽、已修正項目、Known Issues）
     - docs/final_test_report.csv（由 Step2 產出）
  4. 執行 Checkpoint 2（見下方審核清單）；若 PASS，準備打包/標記 release 分支（由 @ARCH 指示）
- 輸入：logs/perf_logs.csv、docs/final_test_report.csv、src/**、docs/**
- 輸出：README.md、docs/architecture_v1.md、docs/final_delivery_summary.md、release-ready source tree
- 估時：1.5 小時

---------------------------------
自動化腳本 / 工具（建議實作清單與預期放置路徑）
- scripts/perf_timer.py              # 計時器、分階段耗時紀錄
- scripts/token_cost_logger.py       # token 計費估算器
- scripts/batch_test.py              # 批次測試 runner
- scripts/hallucination_checker.py   # 幻覺檢查輔助工具
- scripts/e2e_runner.py              # 最小可執行 E2E 測試集
- scripts/perf_analysis.py           # 聚合 perf_logs.csv，輸出平均、P50,P95
- scripts/html_lint_rules.yaml       # HTML lint 標準（若產出 html）
- data/test_samples/sample_template.json
- docs/monitoring_setup.md
- docs/CHANGELOG_PHASE5.md

註：上述腳本若尚未實作，請由對應 Agent 依序建立，範例可放在 scripts/examples/ 供測試使用。

---------------------------------
Checkpoint 審核清單（明確 PASS / FAIL 標準）

Checkpoint 1（由 @ANALYST 觸發，審核者：@ARCH + @CODER）
- 1. 測試覆蓋：docs/final_test_report.csv 必須至少包含 20 筆有效樣本（PASS：>=20；FAIL：<20）
- 2. 幻覺率：final_test_report.csv 中 hallucination_flag 標註比率 < 5%（PASS：<5%；FAIL：>=5%）
- 3. 平均延遲：docs/final_test_report.csv 的平均 latency_total_s < 20s（PASS：<20s；FAIL：>=20s）
- 4. 生成品質：docs/final_quality_report.md 中「準確性」分數 >= 80%（PASS: >=80%；FAIL: <80%）
- 5. 危急 Bug：scripts/e2e_runner.py 執行時無 uncaught exception 或 crash（PASS：無 crash；FAIL：有 crash）

如有任何一項 FAIL，標記為「需要重新優化」並由 @CODER 與 @ANALYST 協同修正後再觸發 Checkpoint1

Checkpoint 2（由 @ARCH 觸發，審核者：指定確認人）
- 1. 文件齊全：README.md、docs/architecture_v1.md、docs/final_delivery_summary.md、docs/final_test_report.csv 全部存在且可讀（PASS：全部存在；FAIL：任一缺失）
- 2. Code Quality：執行 linters（例如 flake8 / pylint）且無阻斷性警告（PASS：無 error；FAIL：有 error）
- 3. 性能與成本門檻：平均 latency < 20s 且 hallucination_rate <5% 且 token 平均成本在可接受範圍（由 PO 覆核）（PASS：符合；FAIL：不符合）
- 4. 交付報告：docs/final_delivery_summary.md 包含測試數據摘要、已修問題列表與已知限制（PASS：內容完整；FAIL：重要欄位缺失）
- 5. git 狀態：最後 commit 已 push 到私有分支 origin-private 且 branch 為 release-ready（PASS：已 push；FAIL：未 push）

---------------------------------
最終交付（Deliverables）及驗收準則
- 1. 完整代碼庫（src/**）
  - 驗收：所有 tests / scripts/e2e_runner.py 執行通過；linter 無阻斷 error
- 2. docs/final_test_report.csv
  - 驗收：至少 20 筆樣本，包含 latency 與 hallucination 標註
- 3. docs/final_quality_report.md
  - 驗收：包含準確性/吸引力/合規性三項量化指標與說明
- 4. README.md、docs/architecture_v1.md、docs/final_delivery_summary.md
  - 驗收：安裝指引、API 範例、系統架構圖、Known issues
- 5. 監控/效能輸出 logs/perf_logs.csv 與 scripts/perf_analysis.py
  - 驗收：可產生平均 latency 與 P95 報表

---------------------------------
風險評估與緩解（至少 5 項）
1) Hallucination 過高
   - 風險：生成內容不可信，導致品質不合格
   - 緩解：降低幻覺容忍率（本階段門檻 5%）；使用檢索對齊 (RAG) 或增加 fact-check 步驟；在批次測試中標註高風險範例
2) API Key/費用超支
   - 風險：測試或壓力測試期間產生高額費用或 Key 被 Rate limited
   - 緩解：在 token_cost_logger 中設定上限告警；對大樣本分批跑（斷點續跑）；在 INFRA 實作成本上限檢查
3) 性能瓶頸 (高延遲)
   - 風險：無法滿足 latency 要求
   - 緩解：採用快取（cache）、非同步化 pipeline、或切換至更小模型做草稿生成，再用大模型做潤飾
4) 自動化測試不穩定/測試膺品（flaky tests）
   - 風險：測試結果無法重現
   - 緩解：確保測試資料種子固定（seed），對外部 API 呼叫做 mocking 選項，用 CI 下定期重跑
5) 數據隱私/外部來源版權問題
   - 風險：抓取或儲存原始搜尋來源可能違反授權
   - 緩解：保存來源時採用摘要化處理（non-identifiable），並在 docs/ 提示合規要求
6) Repo / Release 流程錯誤
   - 風險：未同步 origin-private 或誤推至 main
   - 緩解：release 前由 @ARCH 確認分支並僅使用非破壞性指令；若需要 push，通知並由人為核准

---------------------------------
@ARCH 要建立的檔案 / 腳本（最小起始清單，建議由 @ARCH 建立骨架，並交付給對應 Agent 完成）：
- docs/agent_context/phase5/arch_plan.md    # 本檔（已建立）
- data/test_samples/sample_template.json    # sample 範本 (由 @INFRA 將實際樣本放入)
- scripts/perf_timer.py                      # timer 腳本骨架
- scripts/token_cost_logger.py               # token cost logger
- scripts/batch_test.py                      # batch runner 骨架
- scripts/hallucination_checker.py           # hallucination 檢查骨架
- scripts/e2e_runner.py                      # E2E 測試 runner
- docs/monitoring_setup.md                   # 監控部署說明

---------------------------------
下一步（指示給 @INFRA，自動化啟動指令）
1) 建立目錄與範本：
   mkdir -p data/test_samples logs outputs/generated_results scripts;
   cat > data/test_samples/sample_template.json <<'JSON'
   { "sample_id": "sample-001", "company_name": "ACME Corp", "industry": "manufacturing", "size": "mid", "seed_query": "ACME Corp 公司簡介" }
   JSON

2) 建立 perf timer 與 token logger 的骨架檔（若自動化）：
   touch scripts/perf_timer.py scripts/token_cost_logger.py scripts/batch_test.py scripts/hallucination_checker.py scripts/e2e_runner.py

3) 執行一次快速檢查（確認路徑與權限）：
   python3 - <<'PY'
import os
print('exists:', os.path.isdir('data/test_samples'), os.path.isdir('scripts'))
PY

4) 當上述完成後，@INFRA 請執行：
   - (選項 A) 若要立即跑小規模測試： python3 scripts/batch_test.py --limit 5
   - (選項 B) 若尚無實作，先觸發骨架檔建立並通知 @ANALYST 準備樣本

---------------------------------
最後註記：本檔為 Succinct 的執行計畫，請各 Agent 依照『責任-輸入-輸出-估時』準則執行並在完成後於 PR/Commit 註明附帶的 docs/ 路徑以便 @ARCH 最終核對。
