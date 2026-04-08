# Google Generative AI 遷移規劃文件

## 1. 遷移影響範圍

### 1.1 需要修改的檔案

| 檔案路徑 | 修改項目 | 緊急性 |
|---------|---------|--------|
| `requirements.txt` | 將 `google-generativeai>=0.8.0` 改為 `google-genai` | 高 |
| `src/services/llm_service.py` | 更新 import、Client 初始化、API 呼叫方式 | 高 |
| `verify_llm.py` | 更新 import、Client 初始化、API 呼叫方式 | 中 |

### 1.2 環境變數變更

| 舊版環境變數 | 新版環境變數 | 說明 |
|------------|------------|------|
| `GEMINI_API_KEY` | `GOOGLE_GENAI_API_KEY` | 新版 SDK 自動讀取此變數 |

> **注意**：若要維持向後相容，可在遷移後同時設定兩組環境變數，或在程式碼中適配。

---

## 2. API 差異對照表

### 2.1 Import 與初始化

```python
# === 舊版 (google-generativeai) ===
import google.generativeai as genai

genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel("gemini-flash-latest")

# === 新版 (google-genai) ===
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")
# 或自動從 GOOGLE_GENAI_API_KEY 環境變數載入
client = genai.Client()
```

### 2.2 生成內容 API

```python
# === 舊版 (google-generativeai) ===
response = model.generate_content("Hello!")

# === 新版 (google-genai) ===
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Hello!",
    config=types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=2048
    )
)
```

### 2.3 回應物件存取

```python
# === 舊版 ===
response.text

# === 新版 ===
response.text  # 相同
```

### 2.4 主要差異摘要

| 項目 | 舊版 `google-generativeai` | 新版 `google-genai` |
|-----|--------------------------|-------------------|
| Import | `import google.generativeai as genai` | `from google import genai` |
| Client 初始化 | `genai.configure(api_key=...)` | `client = genai.Client(api_key=...)` |
| 模型建立 | `genai.GenerativeModel(name)` | 改用 `client.models.generate_content()` |
| 環境變數 | `GEMINI_API_KEY` | `GOOGLE_GENAI_API_KEY` |
| 生成配置 | 直接傳入參數 | 透過 `GenerateContentConfig` 物件 |

---

## 3. 測試策略

### 3.1 單元測試

- 執行現有 `tests/services/test_llm_logic.py` 確認 LLM 邏輯正常
- 新增 API 相容性測試（若需要）

### 3.2 整合測試

- 執行 `verify_llm.py` 確認 API 連線正常
- 執行端到端測試 `scripts/e2e_runner.py`

### 3.3 手動驗證項目

| 測試項目 | 預期結果 |
|---------|---------|
| API 金鑰讀取 | 成功從環境變數載入 |
| 模型生成 | 成功取得文字回應 |
| JSON 解析 | 正確解析 LLMOutput 格式 |
| 錯誤處理 | 適當處理 API 錯誤 |

### 3.4 回滾計畫

若遷移後出現問題：
1. 回復 `requirements.txt` 中的套件版本
2. 回復 import 語法
3. 使用舊版環境變數 `GEMINI_API_KEY`

---

## 4. 風險評估

### 4.1 高風險

| 風險項目 | 說明 | 緩解措施 |
|---------|-----|---------|
| API 回應格式變更 | 新版 SDK 回應結構可能略有差異 | 檢查 `response.text` 屬性是否存在 |
| 環境變數名稱變更 | 需設定新版環境變數 | 在 `.env` 中同時設定兩組變數，或修改程式碼支援兩者 |

### 4.2 中風險

| 風險項目 | 說明 | 緩解措施 |
|---------|-----|---------|
| 配置參數名稱變更 | `GenerationConfig` → `GenerateContentConfig` | 查閱新文件確認參數對應 |
| 非同步支援 | 新版 API 可能有不同的非同步語法 | 確認專案中是否有使用 async/await |

### 4.3 低風險

| 風險項目 | 說明 | 緩解措施 |
|---------|-----|---------|
| 模型名稱變更 | 新版模型名稱格式可能不同 | 確認使用相容的模型名稱 |

---

## 5. 實作檢查清單

- [ ] 更新 `requirements.txt`：`google-generativeai` → `google-genai`
- [ ] 更新 `src/services/llm_service.py` import 語法
- [ ] 更新 `src/services/llm_service.py` Client 初始化
- [ ] 更新 `src/services/llm_service.py` generate_content 呼叫
- [ ] 更新 `verify_llm.py` import 語法
- [ ] 更新 `verify_llm.py` Client 初始化
- [ ] 更新 `verify_llm.py` generate_content 呼叫
- [ ] 設定 `GOOGLE_GENAI_API_KEY` 環境變數（或修改程式碼支援兩者）
- [ ] 執行 `verify_llm.py` 驗證 API 連線
- [ ] 執行單元測試 `pytest tests/services/test_llm_logic.py`
- [ ] 執行端到端測試 `python scripts/e2e_runner.py`

---

## 6. 參考資源

- [Google 官方遷移文件](https://ai.google.dev/gemini-api/docs/migrate)
- [DEV Community 遷移指南](https://dev.to/soytuber/google-generativeai-google-genai-migration-guide-29gl)
- [PyPI: google-genai](https://pypi.org/project/google-genai/)

---

**規劃完成時間**：2026-03-31  
**下一步**：交由 @development_agent 執行遷移實作
