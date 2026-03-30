# Multi-Agent 開發流程標準化 (Workflow v4.0)

**更新時間**: 2024-12-23  
**重大更新**: 9步驟完整流程 + 流程說明優化

---

## 🎯 適用階段

```
✅ Day 1 步驟1A：履歷解析模組
✅ Day 1 步驟1B：Mock職缺生成
✅ Day 1 步驟1C：其他Mock數據
✅ Day 1 步驟2：State定義
✅ Day 2-7：各Agent開發
```

---

## 📁 標準檔案結構

```
docs/
├── workflows/
│   └── multi_agent_dev_workflow.md          # ← 本文件
└── agent_context/
    └── phaseN/                              # N = 1,2,3...
        ├── 01_dev_goal_context.md           # 開發目標
        ├── 02_dev_flow_context.md           # 開發流程
        ├── 03_agent_roles_context.md        # Agent角色
        ├── 04_agent_prompts_context.md      # Agent Prompt
        ├── 05_validation_checklist.md       # 驗證清單
        ├── 06_delivery_record.md            # 交付記錄
        └── 07_checkpoint_protocol.md        # Checkpoint協議 ✨
```

**v4.0 變更**: 調整流程說明，新增 Step 8-9 詳細說明，保留7份簡報結構

---

## 🚀 完整9步驟標準流程

### **📋 流程總覽**

```
Step 1-6: 文件準備階段（7份 Context 建立）
Step 7:   啟動指令提供（AI 生成啟動 Prompt）
Step 8:   Multi-Agent 執行（Cline 自動運行）
Step 9:   驗證與交付（品質確認與記錄）
```

---

## 📝 Step 1: 建立檔案路徑

### **目的**
建立當前 Phase 的專屬目錄，存放所有 Context 文件

### **執行流程**

**AI 提供指令**:
```bash
mkdir -p docs/agent_context/phaseN/
```

**人類執行**:
```bash
# 在專案根目錄執行
mkdir -p docs/agent_context/phaseN/

# 驗證建立成功
ls -ld docs/agent_context/phaseN/
```

**確認回覆**:
```
✅ phaseN/ 已建立
```

### **常見問題**

| 問題 | 解決方案 |
|------|----------|
| 目錄已存在 | 正常，繼續下一步 |
| 權限不足 | `sudo mkdir -p ...` 或檢查目錄權限 |
| 路徑錯誤 | 確認在專案根目錄執行 |

---

## 📋 Step 2: 定義檔案規格

### **目的**
明確當前 Phase 需要建立的 Context 文件清單（7份簡報）

### **執行流程**

**AI 確認**:
```
確認7份標準檔案：
1. 01_dev_goal_context.md          # 開發目標與需求
2. 02_dev_flow_context.md          # 開發流程與步驟
3. 03_agent_roles_context.md       # Agent 角色與職責
4. 04_agent_prompts_context.md     # Agent 執行 Prompt
5. 05_validation_checklist.md      # 驗證清單
6. 06_delivery_record.md           # 交付記錄
7. 07_checkpoint_protocol.md       # Checkpoint協議 ✨
```

**人類確認**:
```
✅ 7份規格確認
```

### **檔案說明**

| 檔案 | 用途 | 內容 |
|------|------|------|
| 01 | 開發目標 | 定義 Phase 目標、產出物、驗收標準 |
| 02 | 開發流程 | 定義執行步驟、流程圖、時間估算 |
| 03 | Agent角色 | 定義4個 Agent 的職責與任務 |
| 04 | Agent Prompt | 提供4個 Agent 的執行 Prompt |
| 05 | 驗證清單 | 品質檢查項目、自動驗證腳本 |
| 06 | 交付記錄 | 交付物清單、完成時間、驗證結果 |
| 07 | Checkpoint協議 | 觸發點、決策選項、流程控制 ✨ |

### **v4.0 新增說明**

**07_checkpoint_protocol.md** ✨（新增）:
- 定義 Checkpoint 1 和 Checkpoint 2 的觸發條件
- 提供決策選項與流程控制
- 說明如何在 Checkpoint 做出決策
- 包含重新執行與修正流程

---

## 📄 Step 3: 逐一建立檔案

### **目的**
建立7份空白 Markdown 檔案，準備填入內容

### **執行流程**

**AI 提供指令**（逐一提供）:
```bash
# 第1份
touch docs/agent_context/phaseN/01_dev_goal_context.md
```

**人類執行並確認**:
```bash
touch docs/agent_context/phaseN/01_dev_goal_context.md
ls -lh docs/agent_context/phaseN/01_dev_goal_context.md
```

**確認回覆**:
```
✅ 01_dev_goal_context.md 已建立
```

**重複流程**:
- 依序建立 02, 03, 04, 05, 06, 07
- 每份建立後確認
- 確保7份檔案都建立完成

### **批次建立（進階）**

如果熟悉流程，可批次建立：
```bash
cd docs/agent_context/phaseN/
touch 01_dev_goal_context.md \
      02_dev_flow_context.md \
      03_agent_roles_context.md \
      04_agent_prompts_context.md \
      05_validation_checklist.md \
      06_delivery_record.md \
      07_checkpoint_protocol.md

# 驗證
ls -lh *.md
```

**確認回覆**:
```
✅ 7份檔案已建立
```

---

## ✍️ Step 4: 逐一提供內容

### **目的**
AI 分次提供7份文件的完整 Markdown 內容

### **執行流程**

**AI 提供內容**（分次提供）:
```markdown
【第1份檔案內容】

以下是 01_dev_goal_context.md 的完整內容：

# Phase N - 開發目標

**階段**: [階段名稱]
**目的**: [核心目的]

## 🎯 開發目標
...（完整內容）...
```

**人類操作**:
1. 複製 AI 提供的完整內容
2. 打開對應檔案（如 `01_dev_goal_context.md`）
3. 貼入內容
4. 儲存檔案

**注意事項**:
- AI 會分7次提供內容（避免一次過長）
- 每次提供後等待人類確認
- 確保完整複製（不要遺漏標題或結尾）

### **內容提供順序**

```
1. AI 提供 01_dev_goal_context.md 內容
   → 人類貼入並儲存 → 確認

2. AI 提供 02_dev_flow_context.md 內容
   → 人類貼入並儲存 → 確認

3. AI 提供 03_agent_roles_context.md 內容
   → 人類貼入並儲存 → 確認

4. AI 提供 04_agent_prompts_context.md 內容
   → 人類貼入並儲存 → 確認

5. AI 提供 05_validation_checklist.md 內容
   → 人類貼入並儲存 → 確認

6. AI 提供 06_delivery_record.md 內容
   → 人類貼入並儲存 → 確認

7. AI 提供 07_checkpoint_protocol.md 內容 ✨
   → 人類貼入並儲存 → 完成所有內容
```

---

## ✅ Step 5: 逐一確定檔案

### **目的**
確認每份文件內容已正確貼入，檢查完整性

### **執行流程**

**人類逐一確認**:
```
✅ 01_dev_goal_context.md 內容已貼入 (約60行)
✅ 02_dev_flow_context.md 內容已貼入 (約80行)
✅ 03_agent_roles_context.md 內容已貼入 (約70行)
✅ 04_agent_prompts_context.md 內容已貼入 (約150行)
✅ 05_validation_checklist.md 內容已貼入 (約100行)
✅ 06_delivery_record.md 內容已貼入 (約40行)
✅ 07_checkpoint_protocol.md 內容已貼入 (約80行) ✨
```

### **檢查方法**

**基本檢查**:
```bash
# 檢查檔案大小
ls -lh docs/agent_context/phaseN/*.md

# 檢查行數
wc -l docs/agent_context/phaseN/*.md

# 快速預覽
head -20 docs/agent_context/phaseN/01_dev_goal_context.md
```

**內容檢查**:
- 確認有 Markdown 標題（# ## ###）
- 確認有內容區塊（不是空白檔案）
- 確認沒有亂碼或複製錯誤

### **常見問題**

| 問題 | 檢查方式 | 解決方案 |
|------|---------|---------| 
| 檔案過小 | `ls -lh` 顯示 < 1KB | 內容可能未完整貼入，重新貼入 |
| 格式錯亂 | 打開檔案檢查 | 確認使用 UTF-8 編碼 |
| 內容截斷 | 檢查檔案結尾 | 重新複製完整內容 |

---

## 🎯 Step 6: 啟動確認

### **目的**
最終確認所有文件準備就緒，準備進入 Agent 執行階段

### **執行流程**

**AI 詢問**:
```
Phase N 準備就緒！準備啟動 @INFRA 嗎？

請確認：
✅ 7份 Context 文件已建立
✅ 所有文件內容已完整貼入
✅ 理解執行模式（混合模式）
✅ 準備好在 Checkpoint 做決策
✅ 準備啟動 Multi-Agent 執行
```

**人類回覆選項**:

**選項1: 直接啟動**
```
✅ 啟動
```
→ AI 進入 Step 7，提供啟動指令

**選項2: 預覽啟動指令**
```
🔍 預覽啟動指令
```
→ AI 先展示啟動指令，確認後再啟動

**選項3: 暫停檢查**
```
⏸️ 暫停，我需要檢查文件
```
→ 暫停流程，人類檢查後再啟動

### **檢查清單**

在啟動前，建議快速檢查：

```bash
# 1. 確認7份檔案都存在
ls -1 docs/agent_context/phaseN/*.md | wc -l
# 應該輸出: 7

# 2. 確認檔案不是空白
for f in docs/agent_context/phaseN/*.md; do
  echo "$f: $(wc -l < $f) lines"
done

# 3. 確認可讀取
cat docs/agent_context/phaseN/01_dev_goal_context.md | head -10
```

---

## 🚀 Step 7: 提供啟動指令

### **目的**
AI 生成完整的 Multi-Agent 啟動指令，供人類複製到 Cline 執行

### **執行流程**

**AI 生成啟動指令**:
```
你現在是一個 Multi-Agent 開發團隊，專案：job_search_agent

**專案根目錄：/home/ubuntu/projects/job_search_agent**

**當前階段：[Day X 步驟Y - 階段名稱]**

**執行模式：混合模式**

請閱讀 Phase N 的7份文件：
1. docs/agent_context/phaseN/01_dev_goal_context.md
2. docs/agent_context/phaseN/02_dev_flow_context.md
3. docs/agent_context/phaseN/03_agent_roles_context.md
4. docs/agent_context/phaseN/04_agent_prompts_context.md
5. docs/agent_context/phaseN/05_validation_checklist.md
6. docs/agent_context/phaseN/06_delivery_record.md
7. docs/agent_context/phaseN/07_checkpoint_protocol.md ✨

**執行順序：**
1. @INFRA 啟動 Phase 1（環境準備）→ 自動執行
2. @ARCH 啟動 Phase 2（架構設計）→ 【Checkpoint 1】人工確認
3. @CODER 啟動 Phase 3（程式實現）→ 自動執行
4. @ANALYST 啟動 Phase 4（測試驗證）→ 【Checkpoint 2】人工確認

**Checkpoint 說明（參考 07_checkpoint_protocol.md）:**
- Checkpoint 1：@ARCH 完成後，需要人工確認架構設計
- Checkpoint 2：@ANALYST 完成後，需要人工確認測試結果

**驗證與交付（參考 05_validation_checklist.md 和 06_delivery_record.md）:**
- 執行時進行自動驗證
- 完成後更新交付記錄

**立即啟動：@INFRA 執行 Phase 1，混合模式，完成後自動啟動 @ARCH**
```

**人類操作**:
1. 完整複製上方啟動指令
2. 打開 Cline（或 Claude/ChatGPT）
3. 貼上啟動指令
4. Enter 執行

### **啟動指令說明**

**關鍵要素**:
- ✅ 明確列出7份文件路徑
- ✅ 說明執行順序（INFRA → ARCH → CODER → ANALYST）
- ✅ 標註 Checkpoint 位置（Phase 2 和 Phase 4）
- ✅ 引用7份文件進行執行

**執行模式**（v4.0 支援3種）:

| 模式 | 適用場景 | Checkpoint |
|------|---------|-----------|
| 全自動 | 開發測試 | 無 |
| 人工確認 | 正式發布 | 每個 Phase |
| 混合模式（推薦） | 日常開發 | Phase 2, 4 |

---

## 🤖 Step 8: 執行 Multi-Agent

### **目的**
Agent 團隊自動執行開發任務，人類在 Checkpoint 進行決策

### **執行流程**

#### **8.1 Phase 1 - @INFRA 環境準備**

**自動執行**:
```
@INFRA 開始執行...
→ 建立目錄結構
→ 安裝相依套件
→ 建立初始檔案
→ 自動驗證（參考 05_validation_checklist.md）
→ 輸出完成報告
```

**預期輸出**:
```
【Agent完成報告】
━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Agent: @INFRA
📍 Phase: Phase 1 - 環境準備
⏰ 完成時間: 2024-12-23 16:30:00

✅ 執行結果
  ✅ 建立目錄結構
  ✅ 安裝相依套件
  ✅ 建立初始檔案

📁 輸出檔案
  ✅ data/mock/jobs/ (已建立)
  ✅ src/data_providers/ (已建立)
  ✅ tests/ (已建立)

🔍 自動驗證（05_validation_checklist.md）
  ✅ 目錄結構正確
  ✅ Python 環境正常
  ✅ 套件安裝成功

👉 下一步
  交接給: @ARCH
  執行模式: 自動啟動
━━━━━━━━━━━━━━━━━━━━━━━━━━

正在自動啟動 @ARCH...
```

---

#### **8.2 Phase 2 - @ARCH 架構設計**

**自動執行**:
```
@ARCH 開始執行...
→ 設計數據 Schema
→ 定義 BaseProvider 介面
→ 定義 MockProvider 結構
→ 自動驗證（參考 05_validation_checklist.md）
→ 輸出完成報告
→ 【觸發 Checkpoint 1】
```

**預期輸出**:
```
【Agent完成報告】
━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Agent: @ARCH
📍 Phase: Phase 2 - 架構設計
⏰ 完成時間: 2024-12-23 16:32:00

✅ 執行結果
  ✅ 設計 data_schema.json
  ✅ 定義 BaseProvider 介面
  ✅ 定義 MockProvider 結構

📁 輸出檔案
  ✅ data/mock/data_schema.json
  ✅ src/data_providers/base_provider.py (規範)
  ✅ src/data_providers/mock_provider.py (規範)

🔍 自動驗證（05_validation_checklist.md）
  ✅ Schema 格式正確
  ✅ 必要欄位完整
  ✅ 介面定義清晰

👉 下一步
  【Checkpoint 1】人工確認
━━━━━━━━━━━━━━━━━━━━━━━━━━

【⏸️ Checkpoint 1 - 架構設計確認】

請參考 07_checkpoint_protocol.md 進行確認。

請檢查以下項目：
□ data_schema.json 格式正確
□ BaseProvider 介面完整
□ MockProvider 繼承清晰
□ CrawlerProvider 預留擴展

請選擇：
✅ 確認通過 → @CODER 開始 Phase 3
🔍 詳細檢查 → 顯示完整 schema
❌ 問題：[描述] → 暫停並修正
🔄 重新執行 Phase 2 → @ARCH 重新設計
```

**人類決策**:

選項1: ✅ 確認通過
```
✅ 確認通過
```
→ 自動啟動 @CODER

選項2: 🔍 詳細檢查
```
🔍 詳細檢查
```
→ 顯示 schema 詳細內容，檢查後再決定

選項3: ❌ 發現問題
```
❌ 問題：缺少 match_reasons 欄位
```
→ @ARCH 修正後重新驗證

---

#### **8.3 Phase 3 - @CODER 程式實現**

**自動執行**（Checkpoint 1 通過後）:
```
@CODER 開始執行...
→ 實現 BaseProvider
→ 實現 MockProvider
→ 實現測試案例
→ 生成 Mock 數據
→ 自動驗證（參考 05_validation_checklist.md）
→ 輸出完成報告
```

**預期輸出**:
```
【Agent完成報告】
━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Agent: @CODER
📍 Phase: Phase 3 - 程式實現
⏰ 完成時間: 2024-12-23 16:35:00

✅ 執行結果
  ✅ 實現 BaseProvider 抽象類別
  ✅ 實現 MockProvider 生成邏輯
  ✅ 實現 6 個測試案例
  ✅ 生成 50 個 Mock 職缺

📁 輸出檔案
  ✅ src/data_providers/base_provider.py
  ✅ src/data_providers/mock_provider.py
  ✅ tests/test_mock_provider.py
  ✅ data/mock/jobs/mock_jobs.json

🔍 自動驗證（05_validation_checklist.md）
  ✅ 程式碼可正常執行
  ✅ Mock 數據已生成
  ✅ 測試可收集（6個測試）

👉 下一步
  交接給: @ANALYST
  執行模式: 自動啟動
━━━━━━━━━━━━━━━━━━━━━━━━━━

正在自動啟動 @ANALYST...
```

---

#### **8.4 Phase 4 - @ANALYST 測試驗證**

**自動執行**:
```
@ANALYST 開始執行...
→ 執行測試套件
→ 驗證數據品質
→ 生成品質報告
→ 執行效能測試
→ 自動驗證（參考 05_validation_checklist.md）
→ 輸出完成報告
→ 【觸發 Checkpoint 2】
```

**預期輸出**:
```
【Agent完成報告】
━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Agent: @ANALYST
📍 Phase: Phase 4 - 測試驗證
⏰ 完成時間: 2024-12-23 16:38:00

✅ 執行結果
  ✅ 測試通過率 100% (6/6)
  ✅ 生成 50 個職缺
  ✅ 匹配度分布正確（高20/中20/低10）
  ✅ 品質報告完整

📁 輸出檔案
  ✅ data/mock/jobs/mock_jobs.json (85.3 KB)
  ✅ tests/quality_report.txt

🔍 自動驗證（05_validation_checklist.md）
  ✅ 測試 100% 通過
  ✅ 職缺數量正確 (50)
  ✅ 匹配度分布達標
  ✅ 檔案大小合理 (< 100KB)
  ✅ 執行時間 < 5秒

👉 下一步
  【Checkpoint 2】人工確認
━━━━━━━━━━━━━━━━━━━━━━━━━━

【⏸️ Checkpoint 2 - 測試驗證確認】

請參考 07_checkpoint_protocol.md 進行確認。

請檢查以下項目：
□ 測試 100% 通過 (6/6)
□ 職缺數量正確 (50個)
□ 匹配度分布達標（高20/中20/低10）
□ 檔案大小合理 (< 100KB)
□ 執行時間合格 (< 5秒)

請選擇：
✅ 確認通過 → Phase N 完成，進入 Step 9
🔍 詳細檢查 → 顯示測試報告
❌ 問題：[描述] → 暫停並修正
🔄 重新執行 Phase 3/4 → 重新實現/測試
```

**人類決策**:

選項1: ✅ 確認通過
```
✅ 確認通過
```
→ 進入 Step 9（驗證與交付）

選項2: 🔍 詳細檢查
```
🔍 詳細檢查
```
→ 顯示完整測試報告，檢查後再決定

選項3: ❌ 發現問題
```
❌ 問題：只有15個高匹配職缺
```
→ @CODER 調整邏輯後重新測試

---

### **Step 8 執行時間參考**

| Phase | Agent | 預估時間 | Checkpoint |
|-------|-------|---------|-----------|
| Phase 1 | @INFRA | ~1分鐘 | 無 |
| Phase 2 | @ARCH | ~2分鐘 | ⏸️ Checkpoint 1 |
| Phase 3 | @CODER | ~3分鐘 | 無 |
| Phase 4 | @ANALYST | ~2分鐘 | ⏸️ Checkpoint 2 |
| **總計** | | **~8-10分鐘** | **2次人工確認** |

---

## ✅ Step 9: 完成驗證與交付

### **目的**
最終驗證品質、更新交付記錄、完成 Phase 交付

### **執行流程**

#### **9.1 執行最終驗證**

**參考文件**: `05_validation_checklist.md`

**執行驗證腳本**:
```bash
# 1. 執行完整測試
python -m pytest -v tests/

# 2. 驗證數據品質
python scripts/validate_mock_data.py

# 3. 檢查檔案產出
ls -lh data/mock/jobs/*.json

# 4. 驗證匹配度分布
python -c "
import json
jobs = json.load(open('data/mock/jobs/mock_jobs.json'))
high = sum(1 for j in jobs if j['match_score'] >= 0.7)
mid = sum(1 for j in jobs if 0.4 <= j['match_score'] < 0.7)
low = sum(1 for j in jobs if j['match_score'] < 0.4)
print(f'驗證結果: 高{high}/中{mid}/低{low}')
assert high == 20 and mid == 20 and low == 10, '分布不符'
print('✅ 驗證通過')
"
```

**驗證清單**:
```
□ 測試通過率 100%
□ 職缺數量正確 (50個)
□ 匹配度分布達標（高20/中20/低10）
□ 數據結構完整
□ 檔案大小合理 (< 100KB)
□ 執行效能合格 (< 5秒)
```

---

#### **9.2 更新交付記錄**

**參考文件**: `06_delivery_record.md`

**更新內容**:
```markdown
# Phase N 交付記錄

## 交付資訊
- **階段**: Day 1 步驟1B - Mock職缺生成
- **完成時間**: 2024-12-23 16:40:00
- **執行模式**: 混合模式
- **總耗時**: 10分鐘

## 交付物清單

### 程式碼
- ✅ src/data_providers/base_provider.py (150 lines)
- ✅ src/data_providers/mock_provider.py (280 lines)
- ✅ tests/test_mock_provider.py (200 lines)

### 數據檔案
- ✅ data/mock/data_schema.json (85 lines)
- ✅ data/mock/jobs/mock_jobs.json (50 jobs, 85.3 KB)

### 文件
- ✅ docs/agent_context/phase2/ (7份 Context 文件)

## 驗證結果

### 測試結果
- 測試通過率: 100% (6/6)
- 測試覆蓋率: 95%
- 執行時間: 2.3秒

### 數據品質
- 職缺總數: 50
- 匹配度分布: 高20/中20/低10 ✅
- 數據完整性: 100%
- 檔案大小: 85.3 KB ✅

### Checkpoint 記錄
- Checkpoint 1 (ARCH): ✅ 通過 (16:32)
- Checkpoint 2 (ANALYST): ✅ 通過 (16:38)

## 交付確認
- ✅ 所有驗證項目通過
- ✅ 交付物齊全
- ✅ Phase 2 完成交付

**交付人**: @ANALYST  
**確認人**: [您的名字]  
**日期**: 2024-12-23
```

**更新方式**:
1. 打開 `docs/agent_context/phaseN/06_delivery_record.md`
2. 填入實際完成時間、驗證結果
3. 確認所有交付物清單
4. 儲存檔案

---

#### **9.3 最終確認**

**人類確認**:
```
✅ Phase N 完整交付

確認項目：
✅ 所有驗證通過（參考 05_validation_checklist.md）
✅ 交付記錄已更新（參考 06_delivery_record.md）
✅ 所有檔案已產出
✅ 品質達標
✅ 可進入下一個 Phase
```

**AI 回覆**:
```
🎉 Phase N 完成！

📊 總結：
- 耗時: 10分鐘
- 測試通過率: 100%
- Checkpoint: 2/2 通過
- 交付物: 完整

📁 交付記錄: docs/agent_context/phaseN/06_delivery_record.md

👉 下一步：
準備好進入下一個 Phase 了嗎？
```

---

### **Step 9 檢查清單**

```
□ 執行最終驗證腳本
□ 檢查所有驗證項目通過
□ 更新 06_delivery_record.md
□ 確認交付物齊全
□ 儲存交付記錄
□ 最終確認完成
```

---

## 🎪 標準4個 Agent 角色

| Agent | Phase | 職責 | 驗證標準 |
|-------|-------|------|----------|
| **INFRA** | Phase 1 | 環境準備 | 目錄結構 ✓ |
| **ARCH** | Phase 2 | 架構設計 | Schema ✓ + Checkpoint 1 |
| **CODER** | Phase 3 | 程式實現 | 可執行 ✓ |
| **ANALYST** | Phase 4 | 測試驗證 | 測試 100% ✓ + Checkpoint 2 |

**執行流程**: INFRA → ARCH → CODER → ANALYST → 驗證交付

---

## 🤖 執行模式

### **三種執行模式**

#### **模式1: 全自動模式**
- **適用**: 開發測試、快速迭代
- **流程**: 自動執行全部階段
- **Checkpoint**: 無

#### **模式2: 人工確認模式**
- **適用**: 正式環境、關鍵發布
- **流程**: 每個 Phase 完成後等待確認
- **Checkpoint**: 每個 Phase

#### **模式3: 混合模式（推薦）**
- **適用**: 日常開發（平衡效率與品質）
- **流程**: 關鍵點人工確認，其他自動執行
- **Checkpoint**: Phase 2 (ARCH) 和 Phase 4 (ANALYST)

---

## 📊 v4.0 vs v3.0 對比

| 項目 | v3.0 | v4.0 |
|------|------|------|
| **步驟數** | 7 步驟 | **9 步驟** ✨ |
| **文件數** | 7 份 | **7 份** ✨ |
| **驗證機制** | 內嵌各文件 | **強化** ✨ |
| **Checkpoint協議** | 基本 | **新增詳細說明** ✨ |
| **流程說明** | 簡略 | **詳細完整** ✨ |
| **Step 8** | 簡單提及 | **完整執行流程** ✨ |
| **Step 9** | 無 | **新增驗證交付** ✨ |

---

## 📋 快速啟動 Checklist

```
□ Step 1: 建立 phaseN/ 目錄
□ Step 2: 確認7份文件規格 ✨
□ Step 3: 建立 01-07.md 檔案 ✨
□ Step 4: 提供7份檔案內容 ✨
□ Step 5: 確認內容完整
□ Step 6: 啟動確認
□ Step 7: 複製啟動指令到 Cline
□ Step 8: Multi-Agent 執行（INFRA → ARCH → CODER → ANALYST）✨
□ Step 9: 完成驗證與交付 ✨
  □ 執行最終驗證（05_validation_checklist.md）
  □ 更新交付記錄（06_delivery_record.md）
  □ 參考 Checkpoint 協議（07_checkpoint_protocol.md）✨
  □ 最終確認完成
```

---

## 🎯 使用範例

### **啟動新階段**

```
「進入 Day 1 步驟1B - Mock職缺生成，使用 Multi-Agent 標準流程，混合模式」
```

AI 將自動執行：
1. Step 1-6：建立 phase2/ 的7份文件
2. Step 7：提供啟動指令
3. Step 8：等待複製到 Cline 執行
4. Step 9：完成後驗證與交付

---

## 📚 相關文件

### **必讀文件**
- `開發團隊的Agent分工.txt`
- `multiagents-開發架構.txt`

### **參考文件**
- `docs/agent_context/phaseN/` - 各階段 Context 檔案（7份簡報）
- `docs/phase<N>_development_manual.md` - 各階段開發手冊

---

## 🚨 常見問題

| 問題 | 解決方案 |
|------|----------|
| 檔案命名錯誤 | `mv old_name 0X_new_name.md` |
| 目錄不存在 | `mkdir -p docs/agent_context/phaseN/` |
| Agent 不回應 | 重新複製啟動指令到新對話 |
| 執行中斷 | 從中斷的 Agent 繼續 |
| Checkpoint 卡住 | 參考 07_checkpoint_protocol.md |
| 驗證失敗 | 檢查 05_validation_checklist.md |
| 交付記錄不完整 | 補充 06_delivery_record.md |

---

## 🎉 v4.0 更新內容

### **核心更新**
- ✅ **9步驟完整流程**（Step 1-9 詳細說明）
- ✅ **7份文件結構**（保留完整結構，新增 07_checkpoint_protocol.md）
- ✅ **新增 Step 8**（Multi-Agent 執行詳細流程）
- ✅ **新增 Step 9**（驗證與交付機制）
- ✅ **強化 Checkpoint 協議**（07_checkpoint_protocol.md）
- ✅ **流程說明優化**（每步驟詳細說明）

### **設計原則**
- **完整性**: 9步驟涵蓋從準備到交付全流程
- **可追溯**: 交付記錄提供完整歷史
- **品質保證**: 驗證清單確保品質
- **高效平衡**: 混合模式兼顧效率與品質
- **詳細指導**: 每步驟有完整說明與範例
- **7份簡報**: 維持結構，強化流程控制

---

## 📖 完整初始化 Prompt

```
先不要提供代碼，我現在要使用 Multi-Agent 架構進入開發

當前階段：[Day X 步驟Y - 階段名稱]
執行模式：混合模式（推薦）

請按照 Multi-Agent Workflow v4.0 標準流程：

Step 1-6: 建立7份 Context 檔案
  - 01_dev_goal_context.md
  - 02_dev_flow_context.md
  - 03_agent_roles_context.md
  - 04_agent_prompts_context.md
  - 05_validation_checklist.md
  - 06_delivery_record.md
  - 07_checkpoint_protocol.md ✨

Step 7: 提供啟動指令（明確列出7份文件）
Step 8: Multi-Agent 執行（Checkpoint 1 和 2）
Step 9: 驗證與交付（更新交付記錄）

參考文件：
- 開發團隊的Agent分工.txt
- multiagents-開發架構.txt
- Multi-Agent開發流程標準化 v4.0

立即開始 Step 1：請確認 phaseN/ 路徑
```

---

**🎉 Workflow v4.0 準備就緒！**

**下次開發直接說：**
> 「進入 [Day X 步驟Y]，使用 Multi-Agent 標準流程 v4.0，混合模式」

**AI 將自動執行完整9步驟流程！** 🚀

---

## 📋 版本歷史

- **v1.0** (2024-12-22): 初始版本，基礎6步驟流程
- **v2.0** (2024-12-23): 新增 Step 7 啟動指令模板
- **v3.0** (2024-12-23): 整合混合模式協議、Checkpoint 機制、7份文件結構
- **v4.0** (2024-12-23): 
  - **9步驟完整流程**（新增 Step 8 和 Step 9）
  - **7份文件結構**（保留完整，新增 07_checkpoint_protocol.md）
  - **強化 Checkpoint 協議**（詳細觸發點與決策選項）
  - **每步驟詳細說明**（不再簡略）
  - **完整執行範例**（Step 8 詳細流程）
