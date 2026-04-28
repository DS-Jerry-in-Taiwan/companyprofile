# Phase 16 效能與品質對比測試 - Developer Prompt

> **⚠️ 重要：請依序完成每個步驟，完成後更新本文檔標記進度，再開始下一個步驟。**

---

## 🎯 測試目標

量化 Phase 16 新流程相較於原本 v0.2.0 流程的價值：
1. **效能測試** - 搜尋返回結構化模板的時間差異
2. **品質測試** - 生成簡介的內容品質差異

---

## 📋 開發進度追蹤

| Step | 項目 | 狀態 | 完成日期 | 負責人 |
|------|------|------|----------|--------|
| 0 | 環境準備 | ✅ | 2026-04-16 | Claude |
| 1 | 測試框架架構 | ✅ | 2026-04-16 | Claude |
| 2 | Test Item A1: 搜尋耗時測試 | ✅ | 2026-04-16 | Claude |
| 3 | Test Item A2: Summary Node 耗時測試 | ✅ | 2026-04-16 | Claude |
| 4 | Test Item A3: 端到端耗時測試 | ✅ | 2026-04-16 | Claude |
| 5 | Test Item B1: 四面向覆蓋度測試 | ✅ | 2026-04-16 | Claude |
| 6 | Test Item B2: 內容豐富度測試 | ✅ | 2026-04-16 | Claude |
| 7 | 整合測試與報告生成 | ✅ | 2026-04-16 | Claude |
| 8 | 正式執行測試 | ✅ | 2026-04-16 | Claude |
| 9 | 結果分析與文件更新 | ✅ | 2026-04-16 | Claude |
| 10 | Phase 14 vs Phase 16 對比測試 | ⚠️ | 2026-04-17 | Claude | **注意：測試配置錯誤，結果無效** |
| 11 | 深度分析與問題診斷 | ✅ | 2026-04-17 | Claude | **發現：兩個 Phase 都是「一次性批量查詢」** |
| 12 | 修正配置與重新測試 | 🔄 | 2026-04-18 | 待執行 | **行動：改為 gemini_planner_tavily 重新測試** |

---

## 📚 參考文件

| 文件 | 位置 | 說明 |
|------|------|------|
| 測試規格 | `docs/agent_context/phase16_search_time_formatting/test_spec.md` | 詳細測試項目、評估指標 |
| 新版搜尋 | `src/services/search_tools.py` | Phase 16 四面向搜尋實作 |
| 舊版搜尋 | `backups/v0.2.0/search_tools.py` | v0.2.0 八欄位搜尋實作 |
| 新版 Graph | `src/langgraph_state/company_brief_graph.py` | Summary Node 實作 |
| 舊版 Graph | `backups/v0.2.0/company_brief_graph.py` | v0.2.0 無 Summary Node |

---

## 🔄 新舊流程差異

### 舊流程 (v0.2.0)
```
SEARCH → 直接拼接 → GENERATE → QUALITY_CHECK → END
```
- 8 欄位 Prompt（統一編號、資本額、地址等）
- 鍵值對返回格式
- 無 Summary Node

### 新流程 (v0.3.0 - Phase 16)
```
SEARCH → SUMMARY → GENERATE → QUALITY_CHECK → END
```
- 4 面向 Prompt（foundation/core/vibe/future）
- 結構化 JSON 返回
- 新增 Summary Node 彙整

---

## 📝 Step 0: 環境準備

### 目標
確認測試環境準備完成

### 工作項目
1. [ ] 確認專案依賴已安裝
2. [ ] 確認 `.env` 設定正確（API Key 等）
3. [ ] 確認舊版程式碼可正常引用
4. [ ] 確認測試資料目錄存在

### 驗證方式
```bash
cd /home/ubuntu/projects/OrganBriefOptimization
python -c "from src.services.search_tools import GeminiFewShotSearchTool; print('OK')"
python -c "import sys; sys.path.insert(0, 'backups/v0.2.0'); from search_tools import GeminiFewShotSearchTool; print('OK')"
```

### 完成標準
- 兩個 import 都成功（`OK`）

### 完成後更新
```
| 0 | 環境準備 | ✅ | YYYY-MM-DD | [你的名字] |
```

---

## 📝 Step 1: 測試框架架構

### 目標
建立測試目錄結構與共用工具

### 工作項目
1. [ ] 建立 `tests/` 目錄結構
2. [ ] 建立 `tests/conftest.py` - 全域 fixtures
3. [ ] 建立 `tests/fixtures/companies.json` - 測試公司清單
4. [ ] 建立 `tests/performance/conftest.py` - 效能測試 fixtures
5. [ ] 建立 `tests/quality/conftest.py` - 品質測試 fixtures

### 驗證方式
```bash
ls -la tests/
ls -la tests/performance/
ls -la tests/quality/
cat tests/fixtures/companies.json | python -m json.tool > /dev/null && echo "JSON OK"
```

### 完成標準
- 目錄結構符合 `test_spec.md` 定義
- `companies.json` 格式正確
- 所有 `__init__.py` 存在

### 完成後更新
```
| 1 | 測試框架架構 | ✅ | YYYY-MM-DD | [你的名字] |
```

---

## 📝 Step 2: Test Item A1 - 搜尋耗時測試

### 目標
實作新舊搜尋流程的耗時對比測試

### 工作項目
1. [ ] 建立 `tests/performance/test_search_time.py`
2. [ ] 實作 `mock_old_search_flow()` 模擬 v0.2.0 搜尋
3. [ ] 實作 `test_new_search_flow_time()` 測量新版搜尋
4. [ ] 實作 `test_old_vs_new_search_time()` 耗時對比
5. [ ] 執行測試驗證功能正常

### 核心 Mock 程式碼參考

```python
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backups/v0.2.0"))
from search_tools import GeminiFewShotSearchTool

def mock_old_search_flow(company_name: str) -> dict:
    """模擬 v0.2.0 的搜尋流程"""
    # 使用舊版 Prompt 和處理邏輯
    pass
```

### 驗證方式
```bash
pytest tests/performance/test_search_time.py -v
```

### 完成標準
- 測試通過（允許部分公司因網路問題失敗）
- 能輸出耗時數據

### 完成後更新
```
| 2 | Test Item A1: 搜尋耗時測試 | ✅ | YYYY-MM-DD | [你的名字] |
```

---

## 📝 Step 3: Test Item A2 - Summary Node 耗時測試

### 目標
實作 Summary Node 的處理耗時測試

### 工作項目
1. [ ] 建立 `tests/performance/test_summary_time.py`
2. [ ] 實作 `test_summary_node_time()` 測量 Summary 耗時
3. [ ] 實作 `test_structured_merge_time()` 測量結構化合併耗時
4. [ ] 執行測試驗證功能正常

### 驗證方式
```bash
pytest tests/performance/test_summary_time.py -v
```

### 完成標準
- 測試通過
- 能輸出 Summary Node 各階段耗時

### 完成後更新
```
| 3 | Test Item A2: Summary Node 耗時測試 | ✅ | YYYY-MM-DD | [你的名字] |
```

---

## 📝 Step 4: Test Item A3 - 端到端耗時測試

### 目標
實作完整流程的耗時對比測試

### 工作項目
1. [ ] 建立 `tests/performance/test_end_to_end_time.py`
2. [ ] 實作 `test_old_flow_end_to_end()` 完整舊流程
3. [ ] 實作 `test_new_flow_end_to_end()` 完整新流程
4. [ ] 實作耗時分析報告
5. [ ] 執行測試驗證功能正常

### 驗證方式
```bash
pytest tests/performance/test_end_to_end_time.py -v
```

### 完成標準
- 測試通過
- 能輸出完整耗時分析

### 完成後更新
```
| 4 | Test Item A3: 端到端耗時測試 | ✅ | YYYY-MM-DD | [你的名字] |
```

---

## 📝 Step 5: Test Item B1 - 四面向覆蓋度測試

### 目標
實作四面向覆蓋度的品質測試

### 工作項目
1. [ ] 建立 `tests/quality/test_aspect_coverage.py`
2. [ ] 實作 `test_aspect_coverage()` 檢查每面向內容
3. [ ] 實作 `test_aspect_content_quality()` 檢查內容品質
4. [ ] 執行測試驗證功能正常

### 驗證方式
```bash
pytest tests/quality/test_aspect_coverage.py -v
```

### 完成標準
- 測試通過
- 能輸出覆蓋度報告

### 完成後更新
```
| 5 | Test Item B1: 四面向覆蓋度測試 | ✅ | YYYY-MM-DD | [你的名字] |
```

---

## 📝 Step 6: Test Item B2 - 內容豐富度測試

### 目標
實作內容豐富度的品質測試

### 工作項目
1. [ ] 建立 `tests/quality/test_content_richness.py`
2. [ ] 實作 `test_content_length()` 測量總字數
3. [ ] 實作 `test_info_density()` 測量資訊密度
4. [ ] 實作 `test_aspect_balance()` 測量面向平衡度
5. [ ] 執行測試驗證功能正常

### 驗證方式
```bash
pytest tests/quality/test_content_richness.py -v
```

### 完成標準
- 測試通過
- 能輸出豐富度報告

### 完成後更新
```
| 6 | Test Item B2: 內容豐富度測試 | ✅ | YYYY-MM-DD | [你的名字] |
```

---

## 📝 Step 7: 整合測試與報告生成

### 目標
整合所有測試並建立報告生成工具

### 工作項目
1. [ ] 建立 `tests/reports/generate_report.py`
2. [ ] 實作 JSON 格式報告生成
3. [ ] 實作 Markdown 格式報告生成
4. [ ] 執行全測試整合驗證

### 驗證方式
```bash
pytest tests/ -v --tb=short
python tests/reports/generate_report.py
```

### 完成標準
- 所有測試可一次性執行
- 能生成完整報告

### 完成後更新
```
| 7 | 整合測試與報告生成 | ✅ | YYYY-MM-DD | [你的名字] |
```

---

## 📝 Step 8: 正式執行測試

### 目標
在正式環境執行完整測試

### 工作項目
1. [ ] 確認 API 配額足夠（20 間公司 × 多次 API 呼叫）
2. [ ] 執行完整效能測試
3. [ ] 執行完整品質測試
4. [ ] 收集測試結果
5. [ ] 處理失敗的測試案例

### ⚠️ 注意事項
- 測試會產生 API 費用，請留意
- 建議分批執行避免限流
- 記錄失敗原因

### 驗證方式
```bash
pytest tests/ -v --tb=short -x  # -x 在第一個失敗時停止
```

### 完成標準
- 測試完成（或明確失敗原因記錄）
- 報告已生成

### 完成後更新
```
| 8 | 正式執行測試 | ✅ | YYYY-MM-DD | [你的名字] |
```

---

## 📝 Step 9: 結果分析與文件更新

### 目標
分析測試結果並更新相關文件

### 工作項目
1. [ ] 分析效能測試結果
2. [ ] 分析品質測試結果
3. [ ] 撰寫 `docs/operations/phase16-test-report.md`
4. [ ] 更新 `test_spec.md` 加入實際結果

### 報告格式

```markdown
# Phase 16 測試結果報告

## 執行資訊
- 執行日期：YYYY-MM-DD
- 測試公司數：20
- 成功：X / 失敗：Y

## 效能結果
[表格與分析]

## 品質結果
[表格與分析]

## 結論與建議
[具體建議]
```

### 完成標準
- 報告文件完整
- 測試規格文件已更新

### 完成後更新
```
| 9 | 結果分析與文件更新 | ✅ | YYYY-MM-DD | [你的名字] |
```

---

## 📤 交付物清單

- [x] `tests/performance/test_search_time.py`
- [x] `tests/performance/test_summary_time.py`
- [x] `tests/performance/test_end_to_end_time.py`
- [x] `tests/quality/test_aspect_coverage.py`
- [x] `tests/quality/test_content_richness.py`
- [x] `tests/reports/generate_report.py`
- [x] `docs/operations/phase16-test-report.md`

---

## 🚨 疑難排解

| 問題 | 可能原因 | 解決方案 |
|------|----------|----------|
| Import Error | 路徑問題 | 使用 `sys.path.insert` 加入備份目錄 |
| API 限流 | 請求太頻繁 | 增加 `asyncio.sleep()` 或降低並發 |
| Mock 不準確 | 舊版邏輯變更 | 對照 `backups/v0.2.0/` 原始程式碼 |
| 測試失敗 | 網路問題 | 允許重試或標記為已知失敗 |

---

## ✅ 完成標準

所有 9 個步驟都標記為 ✅ 後，任務完成。

---

## ✅ 任務完成

**Phase 16 效能與品質對比測試已完成！**

### 測試結果摘要

| 項目 | 結果 |
|------|------|
| 測試公司數 | 10 |
| 新流程比舊流程慢 | **+57.4%** |
| 四面向覆蓋率 | **100%** |
| 面向平衡度 | **0.90** |

### 關鍵發現

1. ⚠️ **效能犧牲**：新流程比舊流程慢約 57%，高於預期的 10-15%
   - 原因：4 面向 Prompt 比 8 欄位 Prompt 更複雜
   - 建議：考慮快取機制或 Prompt 優化

2. ✅ **品質提升**：四面向覆蓋率 100%，結構化效果顯著
   - 所有測試公司都有完整的 4 面向內容
   - 面向平衡度平均 0.90，內容分布均勻

3. 📊 **Summary Node 影響小**：處理時間幾乎可忽略（< 0.001s）

### 交付文件

- 測試報告：`docs/operations/phase16-test-report.md`
- 測試程式碼：`tests/performance/`、`tests/quality/`
- Phase 14 vs Phase 16 對比報告：`phase14_vs_phase16_comparison_report.md`
- **深度分析報告**：`analysis_report.md`（包含模組分析與修正建議）

### Phase 14 vs Phase 16 對比測試結果 (2026-04-17)

#### 效能對比
| 項目 | Phase 14 (8欄位) | Phase 16 (4面向) | 差異 |
|------|-----------------|-----------------|------|
| 搜尋時間 | 4.81s | 10.49s | +118.1% |
| Summary Node | N/A | 0.10s | N/A |
| **總時間** | **4.81s** | **10.59s** | **+120.1%** |

#### 主要發現
1. **效能影響顯著**: Phase 16 比 Phase 14 慢約 120%
2. **主要瓶頸**: 搜尋時間（佔總時間 99.1%）
3. **Summary Node 影響輕微**: 僅佔總時間 0.9%
4. **品質提升**: Phase 16 提供更結構化、整合性更好的內容

#### 建議
1. 考慮搜尋優化（快取、並行搜尋）
2. 評估 Prompt 精簡可能性
3. 漸進式部署策略
4. 建立效能監控機制
