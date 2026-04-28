# Phase20 Step 3 開發提示：重構 search_tools.py

## 任務目標

修改 `src/services/search_tools.py`，讓 `GeminiFewShotSearchTool` 的 prompt 從配置動態生成：
1. 從 `config_loader.py` 讀取字段列表
2. 動態生成 prompt 中的字段列表
3. 保持輸出格式不變

---

## 預期產出

修改 `src/services/search_tools.py`：
- 修改 `GeminiFewShotSearchTool.GEMINI_PROMPT_TEMPLATE` 為動態生成
- 確保輸出結果與重構前一致

---

## 實作規格

### 1. 引入 config_loader

在 `search_tools.py` 開頭加入：

```python
# Phase20: 配置驅動
try:
    from src.services.config_loader import get_fields
    CONFIG_DRIVEN_ENABLED = True
except ImportError:
    CONFIG_DRIVEN_ENABLED = False
```

### 2. 修改 Prompt 生成邏輯

目前的問題：
```python
# 目前的 GEMINI_PROMPT_TEMPLATE 是硬編碼的
GEMINI_PROMPT_TEMPLATE = """...
1. 統一編號：公司的統一編號（8位數字）
2. 資本額：公司的資本額（新台幣）
3. 成立時間：公司的成立時間或日期
...
"""
```

修改為：

```python
def _build_dynamic_prompt(self, company_name: str) -> str:
    """
    動態生成 prompt（從配置讀取字段）

    Args:
        company_name: 公司名稱

    Returns:
        str: 完整的 prompt 字串
    """
    # 從配置讀取字段列表
    if CONFIG_DRIVEN_ENABLED:
        fields = get_fields()
    else:
        # Fallback 到預設字段
        fields = [
            "unified_number",
            "capital",
            "founded_date",
            "address",
            "officer",
            "main_services",
            "business_items"
        ]

    # 生成字段列表文字
    field_list_text = "\n".join([f"{i+1}. {field}" for i, field in enumerate(fields)])

    # 組合 prompt
    prompt = f"""你是一個公司資訊搜尋專家。請搜尋「{company_name}」的詳細資訊。

【搜尋任務】
請使用 Google Search 搜尋並提取以下具體字段資訊：

{field_list_text}

【輸出格式】
請用 JSON 格式回覆，格式如下：
{{"unified_number": "值", "capital": "值", "founded_date": "值", "address": "值", "officer": "值", "main_services": "值", "business_items": "值"}}

【嚴格要求】
- 只使用實際搜尋到的資訊，絕對不要編造或推測
- 如果某字段找不到相關資訊，使用 "未找到"
- 絕對不要用 xxx 或任何占位符
- 使用專業、客觀的語言
- 用繁體中文回答
- 只回覆 JSON，不要有其他內容"""

    return prompt
```

### 3. 修改 search() 方法

將：
```python
def search(self, query: str, **kwargs) -> SearchResult:
    prompt = self.GEMINI_PROMPT_TEMPLATE.format(company_name=query)
```

改為：
```python
def search(self, query: str, **kwargs) -> SearchResult:
    prompt = self._build_dynamic_prompt(query)
```

---

## 禁止事項

🚫 **禁止修改的部分**：
- 不要修改工具的搜尋邏輯（`_search()` 方法）
- 不要修改輸出格式（保持 JSON 結構）
- 不要修改 `RESPONSE_SCHEMA`
- 不要修改其他工具類別（如 TavilyBatchSearchTool、ParallelAspectSearchTool 等）

---

## Checklist（完成後勾選）

- [ ] `GeminiFewShotSearchTool` 引入 `config_loader`
- [ ] `_build_dynamic_prompt()` 方法正確從配置讀取字段
- [ ] Fallback 機制正常運作（配置不存在時使用預設字段）
- [ ] `search()` 方法使用動態生成的 prompt
- [ ] 輸出格式與重構前一致（7 字段 JSON）
- [ ] 現有測試通過

---

## 測試驗證

可以建立簡單測試驗證：

```python
# 驗證 prompt 生成
from src.services.search_tools import GeminiFewShotSearchTool

tool = GeminiFewShotSearchTool()
prompt = tool._build_dynamic_prompt("台積電")

# 驗證包含正確字段
assert "unified_number" in prompt
assert "capital" in prompt
assert "founded_date" in prompt
assert len(prompt) > 100  # prompt 不應該太短

print("Prompt 生成測試通過!")
print(f"Prompt 長度: {len(prompt)}")
```

---

## 完成標準

1. 執行測試腳本，測試通過
2. 確認 prompt 是動態生成的（不是硬編碼）
3. 確認輸出格式不變

**請開始實作，完成後更新 checklist 文件再往下開發。**