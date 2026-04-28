# Phase 18：步驟 2 - 解決方案設計

**日期**: 2026-04-17
**步驟**: 2
**狀態**: ✅ 完成

---

## 🎯 步驟目標

設計 Structured Output Schema，確保輸出格式一致。

---

## 💡 解決方案：Gemini Structured Output

### 原理

Gemini 的 Structured Output 功能允許開發者定義輸出的 JSON Schema，確保模型回應符合指定格式：

```python
from google.genai import types

# 定義 Schema
schema = types.Schema(
    type=types.Type.OBJECT,
    properties={
        'foundation': types.Schema(
            type=types.Type.STRING,
            description='品牌實力與基本資料，不超過500字'
        ),
        'core': types.Schema(
            type=types.Type.STRING,
            description='技術產品與服務核心，不超過500字'
        ),
        'vibe': types.Schema(
            type=types.Type.STRING,
            description='職場環境與企業文化，不超過500字'
        ),
        'future': types.Schema(
            type=types.Type.STRING,
            description='近期動態與未來展望，不超過500字'
        ),
    },
    required=['foundation', 'core', 'vibe', 'future']
)

# 使用 Config
config = types.GenerateContentConfig(
    response_schema=schema,
    response_mime_type='application/json',
)
```

### 優勢

| 項目 | 說明 |
|------|------|
| **格式保證** | 100% 輸出符合 Schema |
| **類型安全** | 每個欄位都是指定類型 |
| **簡化解析** | 無需正則表達式解析 |
| **Prompt 簡化** | 不需要強調 JSON 格式 |

---

## 📋 Schema 設計

### 四面向 Schema

```python
from google.genai import types

# 四面向輸出 Schema
ASPECT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "foundation": types.Schema(
            type=types.Type.STRING,
            description="品牌實力與基本資料：公司名稱、成立時間、統一編號、資本額、規模、主要投資方、獲獎榮譽等。不超過500字。",
            max_length=500
        ),
        "core": types.Schema(
            type=types.Type.STRING,
            description="技術產品與服務核心：主要產品、技術亮點、服務內容、核心競爭力、市場定位、產業地位等。不超過500字。",
            max_length=500
        ),
        "vibe": types.Schema(
            type=types.Type.STRING,
            description="職場環境與企業文化：員工評價、工作氛圍、企業文化、團隊特色、福利制度、ESG表現等。不超過500字。",
            max_length=500
        ),
        "future": types.Schema(
            type=types.Type.STRING,
            description="近期動態與未來展望：最新新聞、發展計劃、投資動向、市場前景、擴張計畫、策略方向等。不超過500字。",
            max_length=500
        ),
    },
    required=["foundation", "core", "vibe", "future"]
)
```

### Config 設定

```python
# Structured Output Config
STRUCTURED_CONFIG = types.GenerateContentConfig(
    response_schema=ASPECT_SCHEMA,
    response_mime_type='application/json',
)
```

---

## 🔄 實作變更

### 變更 1：ParallelAspectSearchTool

**檔案**：`src/services/search_tools.py`

**變更內容**：

```python
class ParallelAspectSearchTool(BaseSearchTool):
    # 移除原本的 ASPECT_PROMPTS
    # 新增簡化的 Prompt

    # 簡化的 Prompt（不需要強調 JSON 格式）
    ASPECT_PROMPTS = {
        "foundation": """你是一個公司資訊搜尋專家。請搜尋「{company}」的品牌實力與基本資料，包括成立時間、統一編號、資本額、規模、主要投資方、獲獎榮譽等。只使用實際搜尋到的資訊。""",

        "core": """你是一個公司資訊搜尋專家。請搜尋「{company}」的技術產品與服務核心，包括主要產品、技術亮點、服務內容、核心競爭力、市場定位、產業地位等。只使用實際搜尋到的資訊。""",

        "vibe": """你是一個公司資訊搜尋專家。請搜尋「{company}」的職場環境與企業文化，包括員工評價、工作氛圍、企業文化、團隊特色、福利制度、ESG表現等。只使用實際搜尋到的資訊。""",

        "future": """你是一個公司資訊搜尋專家。請搜尋「{company}」的近期動態與未來展望，包括最新新聞、發展計劃、投資動向、市場前景、擴張計畫、策略方向等。只使用實際搜尋到的資訊。""",
    }

    # 新增 Schema
    RESPONSE_SCHEMA = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "foundation": types.Schema(type=types.Type.STRING),
            "core": types.Schema(type=types.Type.STRING),
            "vibe": types.Schema(type=types.Type.STRING),
            "future": types.Schema(type=types.Type.STRING),
        },
        required=["foundation", "core", "vibe", "future"]
    )

    def _get_structured_config(self) -> types.GenerateContentConfig:
        """取得 Structured Output Config"""
        return types.GenerateContentConfig(
            response_schema=self.RESPONSE_SCHEMA,
            response_mime_type='application/json',
        )

    def _search_single_aspect(self, aspect: str, prompt: str) -> Dict:
        """搜尋單個面向 - 使用 Structured Output"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=self._get_structured_config(),  # 使用 Structured Output
            )

            # 直接解析 JSON（因為已經強制 JSON 格式）
            data = json.loads(response.text)

            return {
                "aspect": aspect,
                "content": data.get(aspect, ""),  # 一定是字串
                "success": True,
            }
        except Exception as e:
            return {
                "aspect": aspect,
                "content": "",
                "success": False,
                "error": str(e),
            }
```

---

## 🧪 測試驗證

### 測試 2.1：驗證輸出格式

```python
from src.services.search_tools import ParallelAspectSearchTool

tool = ParallelAspectSearchTool(timeout=30)
result = tool.search('台積電')

# 驗證所有面向都是字串
for aspect, content in result.data.items():
    assert isinstance(content, str), f"{aspect} 應該是 str，實際是 {type(content)}"
    assert len(content) > 0, f"{aspect} 不應該為空"

print("✅ 所有面向都是字串")
```

### 測試 2.2：驗證無巢狀結構

```python
result = tool.search('南晃交通器材')

# 驗證沒有 dict
for aspect, content in result.data.items():
    assert not content.startswith('{'), f"{aspect} 不應該以 {{ 開頭"
    assert not isinstance(content, dict), f"{aspect} 不應該是 dict"

print("✅ 沒有巢狀 dict")
```

---

## ✅ 通過標準

- [x] Schema 設計完成
- [x] 四面向都是 STRING 類型
- [x] max_length 設定正確
- [x] required 欄位完整

---

*步驟完成時間：2026-04-17 14:30*

---

## 📊 預計工時

| 任務 | 工時 |
|------|------|
| 任務 2.1：Schema 設計 | 0.5h |
| 任務 2.2：Prompt 簡化 | 0.25h |
| 任務 2.3：Config 設計 | 0.25h |
| **總計** | **1h** |

---

*步驟完成時間：待定*
