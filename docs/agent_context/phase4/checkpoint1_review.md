# Checkpoint 1 審核文件（最終版）

版本：v1.0
最後更新：2026-03-30

## 一、概要
- 目的：確認 Phase 4（安全防護與內容審核）中，ARCH 所設計的風控策略與審核狀態機（RiskLevel / RiskStatus / SanitizedContent）可執行且符合預期，準備進入 CODER 的實作階段（Step 3）。
- 目前狀態：
  - Step 1（INFRA）已完成：已安裝 `bleach`，並建立 `config/risk_control/sensitive_keywords.json` 與 `config/risk_control/competitor_names.json`。
  - ARCH 設計產出已就位：`docs/risk_control_flow_diagram.md`、`src/schemas/risk_models.py`。
  - 檢查分支：`review/checkpoint1`（基於 `dev-jerry`）包含本次測試檔案與樣本。

## 二、準備與執行步驟（可複製執行）

### 1. 檢出檢查分支
```bash
git fetch origin
git checkout -b review/checkpoint1 dev-jerry
```

### 2. 確認檔案存在
```bash
ls src/schemas/risk_models.py
ls docs/risk_control_flow_diagram.md
ls config/risk_control/sensitive_keywords.json
ls config/risk_control/competitor_names.json
```

### 3. 建立虛擬環境並安裝依賴
（此專案使用 `.venv` 作為虛擬環境）
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. 執行 Checkpoint1 自動驗證腳本
```bash
source .venv/bin/activate
python tests/checkpoint1_verify.py
```

腳本會載入 `config/risk_control/*`，掃描 `tests/samples/*` 中的樣本，並輸出匹配結果、消毒後片段、遮罩片段與簡單決策（APPROVED / PENDING）。

## 三、人工審核清單（逐項）

下列項目需要人工確認。每項有明確的驗收標準（PASS / FAIL）。

1. 關鍵字清單完整性（由業務 / 法務確認）
   - 檢查項：`config/risk_control/sensitive_keywords.json` 是否包含公司法務/業務認定之禁用字或高風險字彙。
   - 驗收標準：法務或業務確認無遺漏 => PASS；若缺漏，列出缺失並回 ARCH 更新 => FAIL。
   - 自動可檢測項目：檔案存在、JSON 格式正確（自動）；不可自動判斷：業務/法務是否認可（人工）。

2. 競品名單與別名（由業務確認）
   - 檢查項：`config/risk_control/competitor_names.json` 是否包含所有要屏蔽的競品及常見變體（含 domain、簡稱）。
   - 驗收標準：同上，人工核可。自動檢測：檔案存在與語法正確。

3. White-list HTML 標籤（由前端 / UI 確認）
   - 檢查項：允許顯示於 1111 前端編輯器的 HTML 標籤列表（例：`p,a,strong,em,ul,ol,li,br`）是否正確。
   - 驗收標準：前端確認白名單標籤與 `html_sanitizer` 使用的一致 => PASS；若不同，調整白名單或 sanitizer 行為 => FAIL。

4. Masking（遮罩）策略（法務/業務/安全共識）
   - 檢查項：競品遮罩預設為 `***`，是否接受？是否需要 preserve-length 或 partial-mask？
   - 驗收標準：若接受 `***` => PASS；否則指定新策略與更新 config。

5. Banned 行為與 REJECT 流程（法務/合規）
   - 檢查項：禁止（banned）關鍵字是否需直接 REJECT（不可人工覆核）或需先 PENDING 人工審核？
   - 驗收標準：若政策要求直接 REJECT，確認保存/匯報流程（例如是否保留原文的安全備份）=> PASS；否則調整策略 => FAIL。

6. 審核狀態流（PENDING -> REVIEW -> APPROVE/REJECT）與 SLA（由運營/產品指定）
   - 檢查項：確認 PENDING 的審核人員、SLA（例如 24 小時內完成）、審核界面需求。
   - 驗收標準：運營指定審核清單與 SLA => PASS；否則需補充。

7. Audit log 欄位與保存策略（資訊安全）
   - 檢查項：是否包含 event_id、timestamp、input_id、matched_keywords、risk_score、decision、reviewer_id、notes 等欄位；保留或加密敏感資料的策略需明確。
   - 驗收標準：資訊安全確認欄位與存儲方式 => PASS。

8. 自動化測試覆蓋（由 QA / ANALYST 確認）
   - 檢查項：`tests/checkpoint1_verify.py` 是否可運行，samples 是否覆蓋博弈、競品、XSS、乾淨樣本等必要情境。
   - 驗收標準：`python tests/checkpoint1_verify.py` 全部 PASS => PASS；若 FAIL，分析原因並回 ARCH/CODER 調整。

（每一項中，標記 "人工判斷" 的項目代表不可自動化決定，需人員簽核）

## 四、測試樣本與執行方法（自動化 + 手動）

已放置範例檔於：`tests/samples/`

- `gambling.txt`：包含博弈/賭博/虛擬貨幣/洗錢等詞彙（預期：PENDING）
- `competitor.txt`：包含 104、518、yes123、LinkedIn 等（預期：PENDING + masked）
- `xss.html`：包含 `<script>`（預期：APPROVED_SANITIZED => script 被移除）
- `clean.txt`：正常商業文案（預期：APPROVED）

執行指令：
```bash
source .venv/bin/activate
python tests/checkpoint1_verify.py
```

輸出說明：腳本會列出每個樣本的匹配結果、消毒後片段、遮罩後片段，以及根據簡化決策規則（匹配敏感詞或競品則為 PENDING）判斷是否 PASS。

## 五、測試結果摘要（此次執行）

- 執行命令：`python tests/checkpoint1_verify.py`（在 `review/checkpoint1` 分支、`.venv` 已啟用）
- 結果總結：所有 sample 通過預期檢查（All samples pass expectations: True）

匹配與示例：
- `gambling.txt` 匹配到敏感詞：[`博弈`, `賭博`, `虛擬貨幣`, `洗錢`] => 決策：PENDING
- `competitor.txt` 匹配到競品：[`104`, `518`, `yes123`, `LinkedIn`, `104.com.tw`] => 決策：PENDING（已 masking 為 `***`）
- `xss.html` 經 bleach 清洗後 script 被移除（Sanitized） => 決策：APPROVED（但顯示為已消毒）
- `clean.txt` 無匹配 => 決策：APPROVED

（詳細輸出請參考執行結果紀錄或直接在 CI/本機執行腳本查看）

## 六、本次變更紀錄（檔案與 commit 摘要）

新增 / 修改檔案：
- `config/risk_control/sensitive_keywords.json`（新增，commit: infra: add risk control config files）
- `config/risk_control/competitor_names.json`（新增，commit: infra: add risk control config files）
- `docs/risk_control_flow_diagram.md`（ARCH 輸出）
- `src/schemas/risk_models.py`（ARCH 輸出）
- `tests/checkpoint1_verify.py`（新增，commit: test: add checkpoint1 verification script and sample cases）
- `tests/samples/*`（新增多個樣本）
- `tests/checkpoint1_verify.py`（修正：CJK substring fallback，commit: test: improve checkpoint1 scanner fallback for CJK substring matching）

（實際 commit 在本地分支 `review/checkpoint1`，請檢查 git log 以取得完整 hash）

## 七、下一步建議（給 CODER 與 ANALYST）

### CODER（Step 3）優先項目：
1. 實作 `src/services/risk_control_service.py`：整合 token_manager、regex scanner、competitor masking、html sanitizer 與決策邏輯（banned/sensitive/watch weighting 與 thresholds）。
2. 實作 `src/services/html_sanitizer.py`：封裝 bleach.clean 與 allowed_tags/attrs 配置，並提供 `sanitize(html)->str` API。
3. 實作 `src/services/competitor_shield.py`：針對 HTML text node 進行遮罩，避免破壞標籤結構。
4. 提供可配置的 masking 策略並將設定放在 `config/risk_control/`（例如 `competitor_masking_strategy`）。

### ANALYST（Checkpoint 2 前需完成）：
1. 擴充負面測試套件（more samples，包括多語、變體、混淆用字、特殊符號規避等）。
2. 設計 False Positive / False Negative 測試矩陣並定義可接受閾值（例如 FP < 5%）。
3. 與法務/業務確認 banned 與 masking 策略並紀錄簽核證明。

## 八、簽核範本（請審核人填寫）

簽核人：______李岳駿______________

日期：_________20260330___________

結果（請打勾）：
- [✅] ✅ 確認通過 - 同意 CODER 開始 Step 3 實作
- [ ] 🔍 需修正 - 請回 ARCH/CODER 修改後重新審核
- [ ] ❌ 暫停 - 因政策或外部依賴需暫停

備註：
_____________________________________________________________________

---

如需我（@ANALYST）協助把 Checkpoint1 的自動化驗證搬到 CI（例如 GitHub Actions）或擴充測試樣本，我可以接手實作；請回覆是否授權我在 `review/checkpoint1` 分支繼續新增測試或開 PR。
