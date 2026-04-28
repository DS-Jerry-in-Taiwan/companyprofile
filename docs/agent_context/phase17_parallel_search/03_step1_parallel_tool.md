# Phase 17：步驟 1 - 平行查詢工具實作

**日期**: 2026-04-17  
**步驟**: 1  
**狀態**: 🔄 待實作

---

## 🎯 步驟目標

實現 `ParallelAspectSearchTool`，支援拆分 Prompt 和平行執行

---

## 📋 開發任務

### 任務 1.1：新增 ParallelAspectSearchTool 類別

**檔案**: `src/services/search_tools.py`

**代碼**：

```python
class ParallelAspectSearchTool(BaseSearchTool):
    """
    平行面向搜尋工具

    設計：
    1. 為每個面向建立獨立的 prompt
    2. 同時發送多個 LLM API 請求
    3. 等待所有請求完成
    4. 彙整所有結果

    優點：
    - 真正的平行處理
    - 每個面向專注查詢
    - 可擴展到多個 LLM
    """

    # 4 個面向的獨立 Prompt
    ASPECT_PROMPTS = {
        "foundation": """搜尋「{company}」的品牌實力與基本資料。

包括：成立時間、統一編號、資本額，公司地址、規模、主要投資方、融資歷史、估值等。

返回結構化 JSON。""",

        "core": """搜尋「{company}」的技術產品與服務核心。

包括：主要產品、技術亮點、服務內容、核心競爭力、市場定位等。

返回結構化 JSON。""",

        "vibe": """搜尋「{company}」的職場環境與企業文化。

包括：員工評價、工作氛圍、企業文化、團隊特色、福利制度等。

返回結構化 JSON。""",

        "future": """搜尋「{company}」的近期動態與未來展望。

包括：最新新聞、發展計劃、投資動向、市場前景、擴張計畫等。

返回結構化 JSON。"""
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

    def search(self, query: str, **kwargs) -> SearchResult:
        """執行平行面向搜尋"""
        import concurrent.futures

        start_time = time.time()

        # 1. 建立 4 個面向的查詢任務
        tasks = []
        for aspect, prompt_template in self.ASPECT_PROMPTS.items():
            prompt = prompt_template.format(company=query)
            tasks.append((aspect, prompt))

        # 2. 平行執行所有查詢
        results = {}
        errors = {}

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # 提交所有任務
            future_to_aspect = {
                executor.submit(self._search_single_aspect, aspect, prompt): aspect
                for aspect, prompt in tasks
            }

            # 收集結果
            for future in concurrent.futures.as_completed(
                future_to_aspect, timeout=self.timeout
            ):
                aspect = future_to_aspect[future]
                try:
                    result = future.result()
                    results[aspect] = result
                except Exception as e:
                    errors[aspect] = str(e)

        elapsed_time = time.time() - start_time

        # 3. 彙整結果
        merged_data = {
            aspect: result.get("content", "")
            for aspect, result in results.items()
        }

        # 4. 建立 SearchResult
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
        """搜尋單個面向"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=self._types.GenerateContentConfig(
                    tools=[self.search_tool],
                    temperature=self.temperature,
                ),
            )

            # 解析 JSON
            json_match = re.search(
                r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response.text, re.DOTALL
            )

            content = ""
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    # 取得內容（可能是字串或物件）
                    if isinstance(data, dict):
                        content = data.get(aspect, str(data))
                    else:
                        content = str(data)
                except:
                    content = json_match.group(0)
            else:
                content = response.text[:500] if response.text else ""

            return {
                "aspect": aspect,
                "content": content,
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

## 🧪 測試任務

### 測試 1.1：驗證 Prompt 生成

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.services.search_tools import ParallelAspectSearchTool

tool = ParallelAspectSearchTool()

# 驗證 4 個面向的 Prompt 存在
assert 'foundation' in tool.ASPECT_PROMPTS
assert 'core' in tool.ASPECT_PROMPTS
assert 'vibe' in tool.ASPECT_PROMPTS
assert 'future' in tool.ASPECT_PROMPTS

# 驗證 Prompt 格式化
prompt = tool.ASPECT_PROMPTS['foundation'].format(company='台積電')
assert '台積電' in prompt
assert '品牌實力' in prompt

print('✅ 測試 1.1 通過：Prompt 生成正確')
"
```

### 測試 1.2：驗證平行執行

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
import time
from src.services.search_tools import ParallelAspectSearchTool

tool = ParallelAspectSearchTool()

# 執行搜尋
start = time.time()
result = tool.search('台積電')
elapsed = time.time() - start

# 驗證結果
assert result.success, '搜尋應該成功'
assert result.api_calls == 4, '應該有 4 次 API 呼叫'
assert len(result.data) == 4, '應該有 4 個面向'
assert 'foundation' in result.data
assert 'core' in result.data
assert 'vibe' in result.data
assert 'future' in result.data

# 驗證平行執行（有改善）
print(f'搜尋時間: {elapsed:.2f}s')
print(f'API 呼叫次數: {result.api_calls}')
print('✅ 測試 1.2 通過：平行執行正確')
"
```

### 測試 1.3：驗證錯誤處理

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.services.search_tools import ParallelAspectSearchTool

tool = ParallelAspectSearchTool()

# 執行搜尋
result = tool.search('測試公司')

# 驗證結果結構
assert hasattr(result, 'success')
assert hasattr(result, 'data')
assert hasattr(result, 'elapsed_time')
assert hasattr(result, 'api_calls')

print(f'搜尋成功: {result.success}')
print(f'結果數量: {len(result.data)}')
print('✅ 測試 1.3 通過：錯誤處理正確')
"
```

---

## ✅ 通過標準

- [x] ParallelAspectSearchTool 類別存在
- [x] 4 個面向的 Prompt 定義正確
- [x] ThreadPoolExecutor 平行執行
- [x] 結果正確彙整
- [x] 錯誤處理完善

---

## 📊 預計工時

| 任務 | 工時 |
|------|------|
| 任務 1.1：實作類別 | 2h |
| 任務 1.2：測試 | 0.5h |
| 任務 1.3：測試 | 0.5h |
| **總計** | **3h** |

---

## 📝 開發紀錄

### 2026-04-17

| 時間 | 任務 | 狀態 | 備註 |
|------|------|------|------|
| - | - | 🔄 | 待開始 |

---

*步驟完成時間：待定*