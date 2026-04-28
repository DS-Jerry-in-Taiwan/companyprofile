---
# Phase 12 — run_api.py 啟動報錯相對導入問題技術分析

## 問題現象

使用如下指令啟動後端服務時：
```bash
python run_api.py
```
遇到報錯：
```
ImportError: attempted relative import with no known parent package
  File "/home/ubuntu/projects/OrganBriefOptimization/src/functions/api_controller.py", line 12
    from .utils.request_validator import validate_request, ValidationError
```

## 成因分析

1. **相對導入寫法 (`from .utils.xxx`) 問題**
   - 由於 run_api.py 以腳本直接執行，但 api_controller.py 中用的是「相對導入」語法（帶點 `.` 的寫法）。
   - Python 直譯為“無父包”脈絡下的單文件，其相對導入會失效。
   - 結果導致 ImportError。

2. **近期是否動到過？**
   - 本次 optional numeric field 型態修補主要涉及表單驗證與數值邏輯，不直接關聯 import 行為。
   - 目前這個報錯，與 recent 修補內容無直接衝突，是專案 Python package 結構和 import 設計自身的潛在問題，只是現階段暴露出來。

## 解決建議

### (1) 建議採用：改為絕對導入
將 `src/functions/api_controller.py`（以及其他同目錄檔案）所有：
```python
from .utils.xxx import Foo
```
改為
```python
from utils.xxx import Foo
```
即：去掉前綴的「.」轉為直接導入

- 這樣配合 run_api.py「加 sys.path」方式啟動，import 行為會一致且兼容。

### (2) 或 (不推薦)：用 module 方式執行
可將 project 當 package，用如下方式執行，但需保證有 __init__.py：
```bash
python -m src.functions.api_controller
```
- 須調整 project 結構與習慣（不建議現階段這樣做）

## 總結

- 本報錯屬於「Python package 結構與相對導入慣例」問題。
- 近期 field validator/refactor 並未造成本錯誤，是目前 run_api.py 執行方式與 import 設計本身矛盾所觸發。
- 修改方法為：統一移除 .utils 的點，全部用絕對下標方式引用。

---

**建議開發者：**
- 先將所有 `from .utils.` 相關的相對導入改為 `from utils.` 絕對導入
- 測試 run_api.py 可否正常啟動
- 逐一檢查其他可能相同寫法的檔案
- 若仍有問題再補充回報

(技術分析 by Project Analyst)
2026-04-08
