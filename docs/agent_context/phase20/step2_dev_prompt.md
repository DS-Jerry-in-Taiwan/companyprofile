# Phase20 Step 2 開發提示：建立配置載入器

## 任務目標

建立 `src/services/config_loader.py`，實現以下功能：
1. 載入 `config/field_mapping.json`
2. 使用 JSON Schema 驗證配置格式
3. 提供 fallback 機制（配置不存在時使用預設值）

---

## 預期產出

```
src/services/config_loader.py
```

包含以下函數：
- `load_field_mapping()` - 載入並驗證 field_mapping.json
- `get_fields()` - 取得字段列表
- `get_field_to_aspect_mapping()` - 取得字段 → 面向映射
- `get_aspects()` - 取得面向列表

---

## 實作規格

### 1. 基本結構

```python
import json
import os
from typing import Dict, List, Optional
from jsonschema import validate, ValidationError

# 配置路徑
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")
FIELD_MAPPING_PATH = os.path.join(CONFIG_DIR, "field_mapping.json")
FIELD_MAPPING_SCHEMA_PATH = os.path.join(CONFIG_DIR, "field_mapping_schema.json")

# 預設映射（fallback 用）
DEFAULT_FIELD_MAPPING = {
    "fields": [
        "unified_number",
        "capital",
        "founded_date",
        "address",
        "officer",
        "main_services",
        "business_items"
    ],
    "mapping": {
        "unified_number": "foundation",
        "capital": "foundation",
        "founded_date": "foundation",
        "address": "foundation",
        "officer": "foundation",
        "main_services": "core",
        "business_items": "core"
    },
    "aspects": ["foundation", "core", "vibe", "future"]
}
```

### 2. 核心函數實作

```python
def load_field_mapping() -> Dict:
    """載入並驗證 field_mapping.json"""
    # 1. 檢查檔案是否存在
    # 2. 讀取 JSON
    # 3. 用 JSON Schema 驗證
    # 4. 回傳配置（驗證失敗則回傳 None）

def get_fields() -> List[str]:
    """取得字段列表"""
    config = load_field_mapping()
    if config:
        return config.get("fields", [])
    return DEFAULT_FIELD_MAPPING["fields"]

def get_field_to_aspect_mapping() -> Dict:
    """取得字段 → 面向映射"""
    config = load_field_mapping()
    if config:
        return config.get("mapping", {})
    return DEFAULT_FIELD_MAPPING["mapping"]

def get_aspects() -> List[str]:
    """取得面向列表"""
    config = load_field_mapping()
    if config:
        return config.get("aspects", [])
    return DEFAULT_FIELD_MAPPING["aspects"]
```

### 3. JSON Schema 驗證

- 使用 `jsonschema` 套件進行驗證
- 如果沒有 `jsonschema`，可用簡單的 key 檢查代替

### 4. Fallback 機制

當配置檔不存在或驗證失敗時：
- 記錄 warning log
- 使用 `DEFAULT_FIELD_MAPPING` 作為預設值

---

## 禁止事項

🚫 **禁止修改的檔案**：
- `src/services/search_tools.py`
- `src/langgraph_state/company_brief_graph.py`
- `src/services/config_driven_search.py`

🚫 **禁止新增的功能**：
- 不要在這個階段修改任何搜尋邏輯
- 不要新增工具類別

---

## Checklist（完成後勾選）

- [ ] `src/services/config_loader.py` 存在
- [ ] `load_field_mapping()` 函數正確載入配置
- [ ] JSON Schema 驗證邏輯正確（如無 jsonschema 套件則用 key 檢查）
- [ ] Fallback 機制正常運作
- [ ] `get_fields()` 回傳正確的 7 個字段
- [ ] `get_field_to_aspect_mapping()` 回傳正確的映射
- [ ] `get_aspects()` 回傳 4 個面向
- [ ] 基本單元測試通過（測試 fallback 機制）

---

## 測試驗證

建立簡單的測試腳本驗證：

```python
# test_config_loader.py
import sys
sys.path.insert(0, "/home/ubuntu/projects/OrganBriefOptimization")

from src.services.config_loader import (
    load_field_mapping,
    get_fields,
    get_field_to_aspect_mapping,
    get_aspects
)

def test_basic():
    # 測試載入
    config = load_field_mapping()
    assert config is not None, "配置載入失敗"
    
    # 測試字段數量
    fields = get_fields()
    assert len(fields) == 7, f"字段數量錯誤: {len(fields)}"
    
    # 測試映射
    mapping = get_field_to_aspect_mapping()
    assert mapping.get("unified_number") == "foundation"
    assert mapping.get("main_services") == "core"
    
    print("所有測試通過!")

if __name__ == "__main__":
    test_basic()
```

---

## 完成標準

1. 執行測試腳本，所有測試通過
2. 確認 `config_loader.py` 能正確讀取 `field_mapping.json`
3. 確認 fallback 機制正常運作

**請開始實作，完成後更新 checklist 文件再往下開發。**