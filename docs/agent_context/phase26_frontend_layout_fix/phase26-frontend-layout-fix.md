# Phase 26: 前端 Right-Side Results Layout

## 目標
修復前端排版問題：確保結果永遠顯示在右側，與表單並排，而非堆疊在下方。

---

## 問題描述
使用者回報：儘管已實裝左右分欄 CSS (`flex lg:flex-row`），結果仍然顯示在表單下方，未達到預期效果。

---

## 技術分析

### 可能原因

| # | 假設 | 機率 | 備註 |
|---|------|:----:|------|
| 1 | Tailwind 樣式未正確編譯或被覆蓋 | 高 | 可能因 build cache 或 CSS specificity 問題 |
| 2 | BriefForm 或 ResultPanel 容器有 `display: block` 樣式 | 中 | 元件內部 CSS 破壞外部 layout |
| 3 | 手機/平板 media query 先觸發且無 fallback | 中 | `lg:` breakpoint 被行動裝置樣式覆蓋 |
| 4 | Vue component props 傳遞問題 | 低 | 可能 `:results` 未正確綁定 |

---

## 開發流程（逐步執行）

### Step 1: 環境準備與初步排查

#### 開發步驟
1.1 確認後端 API 服務運行中
1.2 啟動前端 dev server: `cd frontend && npm run dev`
1.3 使用瀏覽器開啟 http://localhost:5173
1.4 開啟 Chrome DevTools > Elements 面板
1.5 檢查 `<main>` 標籤的 class 屬性，確認包含 `flex flex-col lg:flex-row`

#### 測試步驟
- [ ] 1.1 後端 API 回應正常 (可用 `/health` 確認)
- [ ] 1.2 前端 dev server 啟動成功，無編譯錯誤
- [ ] 1.3 網頁正確載入，表單顯示
- [ ] 1.4 DevTools Elements 面板可正常運作
- [ ] 1.5 `<main>` 包含預期的 flex classes

#### 通過標準
- 後端 `/health` 回應 200
- 前端 build 無 error/warning
- 瀏覽器 console 無 error
- Elements 面板可見正確的 flex class

#### 禁止事項
- ❌ 不進行 mock test
- ❌ 不跳過此步驟直接修改 CSS
- ❌ 不在未確認根因前修改多個檔案

#### 紀錄
通過後，記錄到 `DEVELOPMENT_LOG.md`:
```
## Step 1: 環境準備與初步排查 ✓
- 完成時間: YYYY/MM/DD HH:MM
- 發現: [觀察到的現象]
- 結論: [是否需要進入下一步或調整策略]
```

---

### Step 2: 分析 Rendered HTML 結構

#### 開發步驟
2.1 在 Elements 面板找到 `<div class="flex flex-col lg:flex-row gap-4">`
2.2 檢查其子元素數量與層級
2.3 確認表單容器與結果容器的 actual width 樣式
2.4 檢查是否有 inline style 覆蓋 class

#### 測試步驟
- [ ] 2.1 flex container 存在於 DOM 中
- [ ] 2.2 有兩個直接子元素（表單、結果）
- [ ] 2.3 表單容器應有 `w-full lg:w-1/3` 或類似 width class
- [ ] 2.4 結果容器應有 `flex-1` 或 `w-full lg:w-2/3`
- [ ] 2.5 無 inline style 覆蓋 display/flex 屬性

#### 通過標準
- DOM 結構正確
- 兩側容器都有正確的 width class
- 無 inline style 破壞 layout

#### 禁止事項
- ❌ 不修改程式碼，只做觀察
- ❌ 不依賴截圖判斷，需有 DOM 證據
- ❌ 不假設原因，直接進入修復

#### 紀錄
通過後，記錄到 `DEVELOPMENT_LOG.md`:
```
## Step 2: 分析 Rendered HTML 結構 ✓
- 完成時間: YYYY/MM/DD HH:MM
- DOM 結構: [描述觀察到的結構]
- Width classes: [表單/結果容器的 class]
- 結論: [發現的問題 / 無異常]
```

---

### Step 3: 寬度測試與 Breakpoint 驗證

#### 開發步驟
3.1 調整瀏覽器視窗寬度至 ≥1024px (桌面)
3.2 使用 DevTools > Computed 面板檢查 container 的 display 屬性
3.3 測量表單容器與結果容器的實際寬度
3.4 切換至平板尺寸 (768px-1023px) 觀察變化
3.5 切換至手機尺寸 (<768px) 觀察變化

#### 測試步驟
- [ ] 3.1 桌面寬度時，表單容器 width > 0
- [ ] 3.2 桌面寬度時，結果容器 width > 0
- [ ] 3.3 桌面寬度時，兩容器並排（可用 getBoundingClientRect 確認）
- [ ] 3.4 平板寬度時，自動變為堆疊
- [ ] 3.5 手機寬度時，保持堆疊

#### 通過標準
- 桌面 (≥1024px): 兩側並排顯示
- 平板 (768-1023px): 堆疊顯示
- 手機 (<768px): 堆疊顯示

#### 禁止事項
- ❌ 不使用 responsive preview，必須用實際視窗調整
- ❌ 不只檢查 class 要檢查 actual computed style
- ❌ 不跳過任何一個 breakpoint 測試

#### 紀錄
通過後，記錄到 `DEVELOPMENT_LOG.md`:
```
## Step 3: 寬度測試與 Breakpoint 驗證 ✓
- 完成時間: YYYY/MM/DD HH:MM
- 桌面 (≥1024px): [並排/堆疊] - 寬度: [表單]px / [結果]px
- 平板 (768-1023px): [並排/堆疊]
- 手機 (<768px): [並排/堆疊]
- 結論: [是否需要修復]
```

---

### Step 4: 提交測試與結果呈現驗證

#### 開發步驟
4.1 填寫表單必填欄位 (organNo, organ)
4.2 點擊「生成簡介」按鈕
4.3 觀察結果出現的位置
4.4 檢查 Results Panel 是否有新項目加入

#### 測試步驟
- [ ] 4.1 表單驗證通過（無 validation error）
- [ ] 4.2 提交按鈕點擊有反應
- [ ] 4.3 結果出現在右側區域（桌面）/ 下方（平板/手機）
- [ ] 4.4 結果內容正確顯示（成功或失敗）

#### 通過標準
- 提交成功時，結果顯示在正確位置
- 提交失敗時，錯誤資訊顯示在正確位置
- 結果可滾動查看（如果多筆）

#### 禁止事項
- ❌ 不使用 mock API response
- ❌ 不跳過「提交成功」與「提交失敗」兩種情況
- ❌ 不只在一种螢幕尺寸測試

#### 紀錄
通過後，記錄到 `DEVELOPMENT_LOG.md`:
```
## Step 4: 提交測試與結果呈現驗證 ✓
- 完成時間: YYYY/MM/DD HH:MM
- 提交成功: [結果位置]
- 提交失敗: [錯誤位置]
- 結論: [是否需要修復]
```

---

### Step 5: 修復實作（如前三步驟有異常）

#### 開發步驟
根據前三步驟發現的問題，選擇對應修復方案：

**修復方案 A: CSS 樣式修復**
- 強制設置 `display: flex` + `flex-wrap: wrap`
- 調整 breakpoint 或新增 fallback class
- 確保元件容器 width 正確 (`w-full lg:w-1/3`, `flex-1`)

**修復方案 B: 元件容器修復**
- 移除 BriefForm/ResultPanel 內部的 `w-full` 阻礙
- 添加 `align-self-start` 防止高度擴展

#### 測試步驟
- [ ] 5.1 修改後重新 build，無 error
- [ ] 5.2 刷新頁面，layout 正確
- [ ] 5.3 重複 Step 3 寬度測試
- [ ] 5.4 重複 Step 4 提交測試

#### 通過標準
- 修復後 build 無錯誤
- 桌面並排顯示正確
- 提交結果位置正確

#### 禁止事項
- ❌ 不修改與 layout 無關的程式碼
- ❌ 不新增多餘的 CSS class
- ❌ 不使用 `!important` 除非必要

#### 紀錄
通過後，記錄到 `DEVELOPMENT_LOG.md`:
```
## Step 5: 修復實作 ✓
- 完成時間: YYYY/MM/DD HH:MM
- 修復方案: [A/B/其他]
- 修改檔案: [檔案名稱與變更]
- 結論: [修復結果]
```

---

### Step 6: 回歸測試

#### 開發步驟
6.1 桌面完整測試流程
6.2 平板完整測試流程
6.3 手機完整測試流程
6.4 多筆結果堆疊測試

#### 測試步驟
- [ ] 6.1.1 桌面：初始載入 → 填寫 → 提交 → 結果在右側
- [ ] 6.1.2 桌面：提交多次 → 多筆結果都在右側
- [ ] 6.2.1 平板：初始載入 → 填寫 → 提交 → 結果在下方
- [ ] 6.3.1 手機：初始載入 → 填寫 → 提交 → 結果在下方
- [ ] 6.4.1 結果列表可正確滾動

#### 通過標準
| 條件 | 桌面 (≥1024px) | 平板 (768-1023px) | 手機 (<768px) |
|------|:--------------:|:-----------------:|:-------------:|
| 初始載入 | 表單左、結果區右 | 堆疊 | 堆疊 |
| 提交成功 | 右側顯示新結果 | 下方顯示新結果 | 下方顯示新結果 |
| 提交失敗 | 右側顯示錯誤 | 下方顯示錯誤 | 下方顯示錯誤 |

#### 禁止事項
- ❌ 不只測試單一尺寸
- ❌ 不只測試成功情況
- ❌ 不跳過滾動測試

#### 紀錄
通過後，記錄到 `DEVELOPMENT_LOG.md`:
```
## Step 6: 回歸測試 ✓
- 完成時間: YYYY/MM/DD HH:MM
- 桌面: [PASS/FAIL] - 描述
- 平板: [PASS/FAIL] - 描述
- 手機: [PASS/FAIL] - 描述
- 結論: [測試結果]
```

---

## 測試指標與通過標準

### 核心指標
| 指標 | 標準 | 測試方法 |
|------|------|----------|
| 桌面並排顯示 | 寬度 ≥1024px 時，flex-direction: row | DevTools Computed |
| 結果位置正確 | 提交後結果在右側而非下方 | 視覺確認 + DOM |
| Responsive 行為 | 平板/手機正確堆疊 | 視窗調整測試 |
| 多筆結果 | 結果列表可滾動 | 實際提交多次 |

### 禁止作為通過標準的測試
- ❌ Mock test / 單元測試
- ❌ 僅檢查 class 名稱存在
- ❌ 僅有截圖無 DOM 證據
- ❌ 僅在單一尺寸測試

### 通過定義
**只有在以上所有 Step 測試步驟全部勾選通過，且在真實瀏覽器環境完成「提交成功 + 提交失敗 + 多尺寸」測試，才視為 Phase 26 完成。**

---

## 驗收標準

| 條件 | 桌面 (≥1024px) | 平板 (768-1023px) | 手機 (<768px) |
|------|:--------------:|:-----------------:|:-------------:|
| 初始載入 | 表單左、結果區右 | 堆疊 | 堆疊 |
| 提交成功 | 右側顯示新結果 | 下方顯示新結果 | 下方顯示新結果 |
| 提交失敗 | 右側顯示錯誤 | 下方顯示錯誤 | 下方顯示錯誤 |

---

## 任務邊界

### 範圍內
- ✅ 前端 CSS Layout 修復
- ✅ Tailwind class 調整
- ✅ Responsive breakpoint 測試
- ✅ 提交功能回歸測試

### 範圍外（禁止）
- ❌ 後端 API 修改
- ❌ 資料庫變更
- ❌ 新功能開發
- ❌ 程式碼重構（除非與 layout 相關）
- ❌ 新增或修改 mock test

---

## 時間估算
- Step 1-4 排查: 45 min
- Step 5 修復（如需要）: 30 min
- Step 6 回歸測試: 15 min
- **總計: ~90 min (1.5 hr)**

---

## 依賴
- Phase 25: Error Handler 強化 ✅ 已完成
- Phase 26: 本任務

---

## 需驗證檔案

```text
frontend/src/App.vue           # flex container 配置
frontend/src/components/BriefForm.vue   # 可能有 width/block 樣式
frontend/src/components/ResultPanel.vue # 可能有 width/block 樣式
frontend/tailwind.config.js    # breakpoint 設定
frontend/src/style.css          # 全域樣式
```

---

## 其他備註
- 如係 Tailwind version 相關問題，可能需要 `npm install` 確保正確版本
- 建議使用 Chrome DevTools > Elements 檢查 Layout box model
- 每個 Step 通過後立即記錄到 DEVELOPMENT_LOG.md
