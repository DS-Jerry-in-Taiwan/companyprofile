# Phase 18：步驟 3 - 程式實作

**日期**: 2026-04-17
**步驟**: 3
**狀態**: ✅ 完成

---

## 🎯 步驟目標

修改 **兩種使用四面向格式的策略工具** 實作 Structured Output：
1. `GeminiFewShotSearchTool`（basic 策略）
2. `ParallelAspectSearchTool`（complete 策略）

---

## 📋 實作任務

### 任務 3.1：修改 GeminiFewShotSearchTool（basic 策略）

**檔案**：`src/services/search_tools.py`

**變更**：
- 新增 `RESPONSE_SCHEMA`（四面向都是 STRING 類型）
- 新增 `_get_structured_config()` 方法
- 簡化 `GEMINI_PROMPT_TEMPLATE`（移除 JSON 格式強調）
- 更新 `search()` 使用 Structured Output

---

### 任務 3.2：修改 ParallelAspectSearchTool（complete 策略）

**檔案**：`src/services/search_tools.py`

**完整程式碼**：

```python
# ===== 策略六：平行面向搜尋工具 =====
class ParallelAspectSearchTool(BaseSearchTool):
    """
    平行面向搜尋工具（Structured Output 版）

    使用 Gemini Structured Output 確保輸出格式一致。
    """

    # 簡化的 Prompt（不需要強調 JSON 格式）
    ASPECT_PROMPTS = {
        "foundation": """你是一個公司資訊搜尋專家。請搜尋「{company}」的品牌實力與基本資料。

包括：成立時間、統一編號、資本額、公司地址、規模、主要投資方、融資歷史、估值、獲獎榮譽等。

【要求】
- 只使用實際搜尋到的資訊
- 返回純文字，不要使用列表或結構化格式""",

        "core": """你是一個公司資訊搜尋專家。請搜尋「{company}」的技術產品與服務核心。

包括：主要產品、技術亮點、服務內容、核心競爭力、市場定位、產業地位等。

【要求】
- 只使用實際搜尋到的資訊
- 返回純文字，不要使用列表或結構化格式""",

        "vibe": """你是一個公司資訊搜尋專家。請搜尋「{company}」的職場環境與企業文化。

包括：員工評價、工作氛圍、企業文化、團隊特色、福利制度、ESG表現等。

【要求】
- 只使用實際搜尋到的資訊
- 返回純文字，不要使用列表或結構化格式""",

        "future": """你是一個公司資訊搜尋專家。請搜尋「{company}」的近期動態與未來展望。

包括：最新新聞、發展計劃、投資動向、市場前景、擴張計畫、策略方向等。

【要求】
- 只使用實際搜尋到的資訊
- 返回純文字，不要使用列表或結構化格式""",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from google import genai
        from google.genai import types

        self.model = kwargs.get("model", "gemini-2.0-flash")
        self.temperature = kwargs.get("temperature", 0.2)
        self.max_workers = kwargs.get("max_workers", 4)
        self.timeout = kwargs.get("timeout", 15)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        self.client = genai.Client(api_key=api_key)
        self._types = types
        self.search_tool = types.Tool(google_search=types.GoogleSearch())

        # 建立 Structured Output Schema
        self._response_schema = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "foundation": types.Schema(
                    type=types.Type.STRING,
                    description="品牌實力與基本資料"
                ),
                "core": types.Schema(
                    type=types.Type.STRING,
                    description="技術產品與服務核心"
                ),
                "vibe": types.Schema(
                    type=types.Type.STRING,
                    description="職場環境與企業文化"
                ),
                "future": types.Schema(
                    type=types.Type.STRING,
                    description="近期動態與未來展望"
                ),
            },
            required=["foundation", "core", "vibe", "future"]
        )

    def _get_structured_config(self) -> "types.GenerateContentConfig":
        """取得 Structured Output Config"""
        return self._types.GenerateContentConfig(
            response_schema=self._response_schema,
            response_mime_type='application/json',
        )

    def search(self, query: str, **kwargs) -> SearchResult:
        """執行平行面向搜尋"""
        import concurrent.futures

        start_time = time.time()

        # 建立 4 個面向的查詢任務
        tasks = []
        for aspect, prompt_template in self.ASPECT_PROMPTS.items():
            prompt = prompt_template.format(company=query)
            tasks.append((aspect, prompt))

        # 平行執行所有查詢
        results = {}

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            future_to_aspect = {
                executor.submit(self._search_single_aspect, aspect, prompt): aspect
                for aspect, prompt in tasks
            }

            for future in concurrent.futures.as_completed(
                future_to_aspect, timeout=self.timeout
            ):
                aspect = future_to_aspect[future]
                try:
                    result = future.result()
                    results[aspect] = result
                except Exception as e:
                    results[aspect] = {"aspect": aspect, "success": False, "error": str(e)}

        elapsed_time = time.time() - start_time

        # 彙整結果
        merged_data = {
            aspect: result.get("content", "") for aspect, result in results.items()
        }

        return SearchResult(
            success=len(results) > 0,
            tool_type="parallel_aspect_search",
            elapsed_time=elapsed_time,
            api_calls=len(tasks),
            data=merged_data,
            raw_answer=json.dumps(merged_data, ensure_ascii=False),
            answer_length=sum(len(str(v)) for v in merged_data.values()),
        )

    def _search_single_aspect(self, aspect: str, prompt: str) -> Dict:
        """搜尋單個面向 - 使用 Structured Output"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=self._get_structured_config(),
            )

            # 直接解析 JSON（因為已經強制 JSON 格式）
            data = json.loads(response.text)

            # 確保返回字串
            content = data.get(aspect, "")
            if not isinstance(content, str):
                content = str(content)

            return {
                "aspect": aspect,
                "content": content,
                "success": True,
            }
        except json.JSONDecodeError as e:
            # 如果 JSON 解析失敗，回退到純文字
            return {
                "aspect": aspect,
                "content": response.text[:500] if response.text else "",
                "success": True,
                "fallback": True,
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

### 任務 3.2：更新工廠註冊

確保工廠正確處理新的實作。

```python
# 在 SearchToolFactory._registry 中已經有
SearchToolType.PARALLEL_ASPECT_SEARCH: ParallelAspectSearchTool,
```

---

## 🧪 測試任務

### 測試 3.1：驗證 Structured Output

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python3 -c "
from src.services.search_tools import ParallelAspectSearchTool

tool = ParallelAspectSearchTool(timeout=30)
result = tool.search('台積電')

print('搜尋成功:', result.success)
print('API 呼叫:', result.api_calls)

for aspect, content in result.data.items():
    print(f'{aspect}: {type(content).__name__} ({len(content)} 字)')

# 驗證都是字串
for aspect, content in result.data.items():
    assert isinstance(content, str), f'{aspect} 應該是 str'
    assert len(content) > 0, f'{aspect} 不應該為空'

print('✅ 所有面向都是字串')
"
```

### 測試 3.2：驗證 Checkpoint 1

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python3 scripts/checkpoint1/test_phase17_complete_flow.py
```

---

## ✅ 通過標準

- [ ] ParallelAspectSearchTool 實作完成
- [ ] Structured Output Schema 正確定義
- [ ] 單元測試通過
- [ ] Checkpoint 1 測試通過

---

## 📊 預計工時

| 任務 | 工時 |
|------|------|
| 任務 3.1：實作 | 1.5h |
| 任務 3.2：工廠更新 | 0.5h |
| **總計** | **2h** |

---

*步驟完成時間：待定*
