"""
平行搜尋工具測試區
==================

目的：測試平行執行多個搜尋工具的效果

測試流程：
1. parallel_search_tool.py - ParallelMultiSourceTool 實作
2. test_parallel_search.py - 測試腳本
3. 比較平行 vs 順序執行的效能

目錄結構：
scripts/stage3_test/parallel_search/
├── parallel_search_tool.py    # 平行搜尋工具實作
├── test_parallel_search.py    # 測試腳本
├── test_results.json          # 測試結果
├── README.md                  # 本檔案
└── results/                  # 測試結果輸出目錄

---

## 測試結果 (2026-04-14)

### 效能比較

| 執行方式 | 耗時 |
|---------|------|
| 順序搜尋 | 10.55s |
| 平行搜尋 | 4.69s |

### 改善幅度

| 指標 | 數值 |
|------|------|
| 效能改善 | **55.6%** |
| 加速比 | **2.25x** |

### 詳細分析

```
順序搜尋 (10.55s)：
  Tavily:  5.90s
  Gemini:  4.66s
  總計:    10.55s

平行搜尋 (4.69s)：
  Tavily:  0.61s (有快取效應?)
  Gemini:  4.67s
  總計:    max(0.61, 4.67) = 4.69s
```

### 結論

✅ 平行搜尋成功減少總耗時
✅ 介面與現有工具相容
✅ 信心度計算正常 (1.0)
✅ 多源結果正常合併

### 待驗證

- [ ] 更多公司名稱測試
- [ ] 真實 cold start 環境測試（目前可能有快取效應）
- [ ] 三個以上來源的效果
- [ ] 整合到正式專案
"""
