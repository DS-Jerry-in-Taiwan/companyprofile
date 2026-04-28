# Phase 26: 前端 Right-Side Results Layout

## 目標
修復前端排版問題：確保結果永遠顯示在右側，與表單並排，而非堆疊在下方。

## 問題描述
使用者回報：儘管已實裝左右分欄 CSS (`flex lg:flex-row`），結果仍然顯示在表單下方，未達到預期效果。

## 技術分析

### 可能原因

| # | 假設 | 機率 | 備註 |
|---|------|:----:|------|
| 1 | Tailwind 樣式未正確編譯或被覆蓋 | 高 | 可能因 build cache 或 CSS specificity 問題 |
| 2 | BriefForm 或 ResultPanel 容器有 `display: block` 樣式 | 中 | 元件內部 CSS 破壞外部 layout |
| 3 | 手機/平板 media query 先觸發且無 fallback | 中 | `lg:` breakpoint 被行動裝置樣式覆蓋 |
| 4 | Vue component props 傳遞問題 | 低 | 可能 `:results` 未正確綁定 |

### 需驗證檔案

```text
frontend/src/App.vue           # flex container 配置
frontend/src/components/BriefForm.vue   # 可能有 width/block 樣式
frontend/src/components/ResultPanel.vue # 可能有 width/block 樣式
frontend/tailwind.config.js    # breakpoint 設定
frontend/src/style.css          # 全域樣式
```

## 開發任務清單

### Task 26.1: 根本原因排查
- [ ] 26.1.1 啟動前端 dev server，檢查 Rendered HTML 結構
- [ ] 26.1.2 使用瀏覽器 devtools 檢查 `.flex` container 是否存在
- [ ] 26.1.3 檢查 Tailwind classes 是否正確應用
- [ ] 26.1.4 確認沒有 Custom CSS 覆蓋 flex 行為

### Task 26.2: 修復實作
依排查結果選擇對應修復方案：

#### 方案 A: CSS 修復（如係原因 1-3）
- [ ] 26.2.1 強制設置 `display: flex` + `flex-wrap: wrap`
- [ ] 26.2.2 調整 breakpoint 或新增 fallback class
- [ ] 26.2.3 確保元件容器 width 正確 (`w-full lg:w-1/3`, `flex-1`)

#### 方案 B: 元件容器修復（如係原因 2）
- [ ] 26.2.4 移除 BriefForm/ResultPanel 內部的 `w-full` 或設定正確 width
- [ ] 26.2.5 添加 `h-fit` 或 `align-self-start` 防止高度擴展

### Task 26.3: 回歸測試
- [ ] 26.3.1 桌面版：確認左右並排
- [ ] 26.3.2 平板版：確認 responsive 行為正確
- [ ] 26.3.3 手機版：確認堆疊行為正確（符合預期）
- [ ] 26.3.4 提交結果後確認結果顯示在右側

### Task 26.4: 文件更新
- [ ] 26.4.1 更新 CHANGELOG.md
- [ ] 26.4.2 記錄修復過程與學習

## 驗收標準

| 條件 | 桌面 (≥1024px) | 平板 (768-1023px) | 手機 (<768px) |
|------|:--------------:|:-----------------:|:-------------:|
| 初始載入 | 表單左、結果區右 | 堆疊 | 堆疊 |
| 提交成功 | 右側顯示新結果 | 下方顯示新結果 | 下方顯示新結果 |
| 提交失敗 | 右側顯示錯誤 | 下方顯示錯誤 | 下方顯示錯誤 |

## 時間估算
- 排查: 30 min
- 修復: 30 min  
- 測試: 15 min
- **總計: ~75 min (1.25 hr)**

## 依賴
- Phase 25: Error Handler 強化 ✅ 已完成
- Phase 26: 本任務

## 其他備註
- 如係 Tailwind version 相關問題，可能需要 `npm install` 確保正確版本
- 建議使用 Chrome DevTools > Elements 檢查 Layout box model