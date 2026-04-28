# Phase 23 通過標準驗證腳本

## 這不是單元測試
這是**實際驗證腳本**，用來確認 Phase 23 是否真正解決問題。

---

## 執行方式

```bash
# 方式 A：需要 API（會實際調用 LLM）
python scripts/test_phase23_actual_verification.py --mode api --company "台積電" --runs 3

# 方式 B：不需要 API（Mock 測試）
python scripts/test_phase23_actual_verification.py --mode mock --runs 10
```

---

## 通過標準

### 標準 1：開頭多樣化（API 測試）

**測試方法**：對同一間公司調用 N 次，檢查開頭

**通過條件**：
- N 次輸出中，開頭不完全相同
- 或者至少有一次開頭不是「成立於」

**失敗條件**：
- 連續 3 次輸出，開頭完全相同

### 標準 2：段落順序多樣化

**測試方法**：檢查輸出段落是否包含不同關鍵字

**通過條件**：
- 不同次執行，段落順序有變化

### 標準 3：多次調用差異性（單元測試）

**測試方法**：執行多次 get_random_* 函式

**通過條件**：
- 執行 50 次框架選擇，覆蓋 >= 3 種
- 執行 30 次情境選擇，覆蓋 >= 2 種
- 執行 30 次句型選擇，覆蓋 >= 3 種

---

## 實際驗證 vs. 單元測試

| 類型 | 測什麼 | 通過標準 | 需 API |
|------|--------|----------|--------|
| **單元測試** | 能不能選取不同模板 | 覆蓋 3+ 種 | ❌ 否 |
| **實際驗證** | 實際輸出有沒有變化 | 開頭不同 / 段落順序不同 | ✅ 是 |

---

## 為什麼需要實際驗證？

單元測試只證明：
- ✅ 函式能返回不同選項
- ✅ 隨機性正常

**不能證明**：
- ❌ LLM 生成時有沒有參考這些模板
- ❌ 輸出內容真的有變化
- ❌ 問題解決了

---

## 驗證腳本邏輯

```python
def verify_opening_diversity(response_texts):
    """檢查多個回應的開頭是否多樣"""
    first_sentences = [extract_first_sentence(t) for t in response_texts]
    unique = set(first_sentences)
    
    if len(unique) == 1:
        return FAIL  # 全部相同
    elif len(unique) == len(response_texts):
        return PASS  # 全部不同
    else:
        return PARTIAL  # 部分相同

def verify_paragraph_flow(response_texts):
    """檢查段落順序是否多樣"""
    flows = [extract_paragraph_flow(t) for t in response_texts]
    unique = set(flows)
    
    if len(unique) == 1:
        return FAIL
    else:
        return PASS
```

---

## 報告格式

```
============================================================
Phase 23 實際驗證報告
============================================================

【測試對象】
  公司: 台積電
  執行次數: 3

【開頭多樣化】
  第1次: 「在半導體領域，台積電成立於...」
  第2次: 「成立於1987年的台積電...」
  第3次: 「專注於半導體製造的台積電...」

  結果: ⚠️ PARTIAL (2/3 不同)

【段落順序】
  第1次: foundation → core → vibe → future
  第2次: core → foundation → vibe → future
  第3次: core → foundation → vibe → future

  結果: ⚠️ PARTIAL

【總結】
  通過標準 1: ⚠️ 部分通過
  通過標準 2: ⚠️ 部分通過

  總結: 需要改進
============================================================
```

---

## 常見問題

### Q: API 回覆 429 怎麼辦？
A: 這不是 Phase 23 的問題，是配額問題。換個時間再測。

### Q: Mock 測試通過但 API 測試失敗？
A: 這表示選取功能正常，但應用到 LLM 生成失敗。回到實現方式檢查。

### Q: 單元測試通過但實際驗證失敗？
A: 這就是現在的狀況。說明「選擇」做了，「應用」沒做。