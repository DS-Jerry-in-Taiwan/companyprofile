# Phase20 Step 4 開發提示：重構 company_brief_graph.py

## 任務目標

修改 `src/langgraph_state/company_brief_graph.py`，讓映射邏輯從配置動態取得：
1. 從 `config_loader.py` 讀取字段 → 面向映射
2. 移除硬編碼的 `FIELD_TO_ASPECT` 字典
3. 保持輸出結果不變

---

## 預期產出

修改 `src/langgraph_state/company_brief_graph.py`：
- 引入 `config_loader`
- 修改映射取得邏輯
- 確保摘要結果與重構前一致

---

## 實作規格

### 1. 引入 config_loader

在 `company_brief_graph.py` 開頭（或適當位置）加入：

```python
# Phase20: 配置驅動
try:
    from src.services.config_loader import (
        get_field_to_aspect_mapping,
        get_aspect_to_fields_mapping,
        reload_config
    )
    CONFIG_DRIVEN_ENABLED = True
except ImportError:
    CONFIG_DRIVEN_ENABLED = False
```

### 2. 找到硬編碼的 FIELD_TO_ASPECT

在 `company_brief_graph.py` 中找到類似這樣的程式碼：

```python
# Phase19: 具體字段到四面向的映射
FIELD_TO_ASPECT = {
    "unified_number": "foundation",
    "capital": "foundation",
    "founded_date": "foundation",
    "address": "foundation",
    "officer": "foundation",
    "main_services": "core",
    "business_items": "core",
}
```

### 3. 修改映射取得邏輯

將使用 `FIELD_TO_ASPECT` 的地方改為從配置讀取：

```python
# 修改前
FIELD_TO_ASPECT = {
    "unified_number": "foundation",
    ...
}

# 使用時
if field and field in FIELD_TO_ASPECT:
    aspect = FIELD_TO_ASPECT[field]

# 修改後
# 直接使用 get_field_to_aspect_mapping()
if CONFIG_DRIVEN_ENABLED:
    field_to_aspect = get_field_to_aspect_mapping()
else:
    field_to_aspect = {
        "unified_number": "foundation",
        "capital": "foundation",
        "founded_date": "foundation",
        "address": "foundation",
        "officer": "foundation",
        "main_services": "core",
        "business_items": "core",
    }

# 使用時
if field and field in field_to_aspect:
    aspect = field_to_aspect[field]
```

### 4. 保持向後兼容

如果配置不存在或載入失敗，系統應該：
- 記錄 warning log
- 使用預設的硬編碼值

---

## 禁止事項

🚫 **禁止修改的部分**：
- 不要修改圖的節點邏輯（只改映射取得方式）
- 不要修改 `summarize_results` 等函數的主要邏輯
- 不要修改輸出格式

---

## Checklist（完成後勾選）

- [ ] 引入 `config_loader`
- [ ] 移除或替換硬編碼的 `FIELD_TO_ASPECT`
- [ ] 映射邏輯從配置動態讀取
- [ ] Fallback 機制正常運作
- [ ] 摘要結果與重構前一致

---

## 測試驗證

可以建立簡單測試驗證：

```python
import sys
sys.path.insert(0, "/home/ubuntu/projects/OrganBriefOptimization")

from src.services.config_loader import (
    get_field_to_aspect_mapping,
    reload_config
)
from src.langgraph_state.company_brief_graph import CompanyBriefGraph

# 重新載入配置
reload_config()

# 測試映射
mapping = get_field_to_aspect_mapping()
print(f"映射: {mapping}")

# 測試 CompanyBriefGraph 是否能正常運作
graph = CompanyBriefGraph()
print("CompanyBriefGraph 初始化成功")

print("測試通過!")
```

---

## 完成標準

1. 執行測試腳本，測試通過
2. 確認映射是從配置動態讀取的
3. 確認摘要結果與重構前一致

**請開始實作，完成後更新 checklist 文件再往下開發。**