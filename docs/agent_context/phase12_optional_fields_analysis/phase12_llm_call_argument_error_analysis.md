# LLM Runtime Error Analysis: Missing 'wl' Argument

## 概要 / Summary

在本地端測試與自動化流程中，發現 `llm_call_with_retry.<locals>.llm_call_with_retry() missing 1 required positional argument: 'wl'` 的錯誤訊息，阻礙了後端核心功能的正常運作。本報告記錄問題現象、可能原因、排查建議與後續行動建議，作為開發同仁後續修正依據。

---

## 問題現象
- 發生異常：
  - 報錯內容：`llm_call_with_retry.<locals>.llm_call_with_retry() missing 1 required positional argument: 'wl'`
  - 場景：在後端啟動流程或 LLM 相關功能呼叫時觸發。
- 錯誤本質：
  - Python 執行函數時，缺少必須給定的『wl』參數，導致無法正確執行。

---

## 深入技術分析

### 根本原因

此錯誤的**根本原因**來自 `@with_retry` 裝飾器的設計與實際使用不符：

#### 1. 裝飾器的行為（`src/langchain/error_handlers.py` 第 310-340 行）

```python
def with_retry(
    retry_config: Optional[RetryConfig] = None,
    name: Optional[str] = None,
):
    def decorator(func: Callable) -> Callable:
        retry_wrapper = RunnableRetry(func, retry_config, name or func.__name__)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 將參數轉換為單一輸入
            if len(args) == 1 and not kwargs:
                input_data = args[0]
            else:
                input_data = {"args": args, "kwargs": kwargs}

            return retry_wrapper.invoke(input_data)

        return wrapper

    return decorator
```

**問題所在**：
- 裝飾器的 `wrapper` 函數接受 `*args, **kwargs`，但將所有參數**打包成單一 `input_data`**。
- 它只傳遞一個參數給 `retry_wrapper.invoke(input_data)`。

#### 2. 被裝飾的函數（`src/functions/utils/llm_service.py` 第 58-61 行）

```python
@with_retry(retry_config, "llm_call")
def llm_call_with_retry(input_data, wl):
    return _call_llm_core(input_data, wl)

return llm_call_with_retry(prompt, word_limit)
```

**衝突點**：
- 函數定義有 **2 個參數**：`input_data` 和 `wl`
- 呼叫時傳遞 **2 個參數**：`llm_call_with_retry(prompt, word_limit)`
- 但裝飾器的 `wrapper` 只接受第一個參數，將所有參數打包成 `input_data`
- 當 `RunnableRetry.invoke()` 呼叫函式時（第 146-149 行），它調用 `self.runnable(input)`，只傳遞單一參數
- 結果：函式缺少第二個參數 `wl`

### 為什麼會發生？

1. **裝飾器設計與實現的不匹配**：
   - 裝飾器被設計為接受任意數量的參數，但實際上是將其打包為單一輸入。
   - 這適合於**只接受一個參數**的函數，但不適合**需要多個參數**的函數。

2. **函數簽名的不兼容**：
   - 原始函數 `llm_call_with_retry(input_data, wl)` 期望 2 個獨立參數。
   - 裝飾器 `wrapper` 只向底層 `invoke()` 傳遞 1 個打包的參數。

---

## 排查結果與修復方案

### 解決方案

有三種可能的修復方法，推薦方案如下（按優先級）：

#### **方案 A（推薦）：修改函數簽名以配合裝飾器**

改變 `llm_call_with_retry` 以接受單一字典參數，包含所有必要資訊：

```python
def _call_llm_with_retry(prompt, word_limit=None) -> dict:
    """使用重試機制的 LLM 呼叫"""
    try:
        retry_config = get_retry_config()

        @with_retry(retry_config, "llm_call")
        def llm_call_with_retry(inputs):
            # 解包 inputs 字典
            return _call_llm_core(inputs["prompt"], inputs.get("word_limit"))

        # 將參數打包為字典傳遞
        return llm_call_with_retry({"prompt": prompt, "word_limit": word_limit})

    except Exception as e:
        logger.error(f"LLM call with retry failed: {e}")
        return _get_default_response(prompt)
```

**優點**：
- 符合裝飾器的設計意圖
- 清晰且可維護
- 無需改動裝飾器本身

**缺點**：
- 需要在函數內部解包參數

#### **方案 B：改進裝飾器以支援多參數函數**

修改 `with_retry` 裝飾器，使其正確處理多參數函數：

```python
def with_retry(
    retry_config: Optional[RetryConfig] = None,
    name: Optional[str] = None,
):
    """
    重試裝飾器 - 支援多參數函數
    """

    def decorator(func: Callable) -> Callable:
        retry_wrapper = RunnableRetry(func, retry_config, name or func.__name__)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 保留原始參數結構，由 RunnableRetry 直接呼叫
            return retry_wrapper.invoke_with_args(args, kwargs)

        return wrapper

    return decorator
```

並在 `RunnableRetry` 中新增 `invoke_with_args` 方法。

**優點**：
- 更靈活，支援任意簽名的函數
- 無需修改現有函數

**缺點**：
- 需要改動核心裝飾器邏輯
- 可能影響其他使用此裝飾器的地方

#### **方案 C：移除裝飾器，使用回退機制**

在 `_call_llm_with_retry` 中不使用 `@with_retry` 裝飾器，而是直接在函數內部實現重試邏輯：

```python
def _call_llm_with_retry(prompt, word_limit=None) -> dict:
    """使用重試機制的 LLM 呼叫"""
    retry_config = get_retry_config()
    last_error = None

    for attempt in range(1, retry_config.max_attempts + 1):
        try:
            return _call_llm_core(prompt, word_limit)
        except Exception as e:
            last_error = e
            if attempt < retry_config.max_attempts:
                wait_time = retry_config.calculate_wait_time(attempt)
                logger.info(f"等待 {wait_time:.2f} 秒後重試...")
                time.sleep(wait_time)
            else:
                logger.error(f"LLM call failed after {retry_config.max_attempts} attempts: {e}")

    return _get_default_response(prompt)
```

**優點**：
- 最直接，無裝飾器複雜性
- 清楚的控制流

**缺點**：
- 代碼重複（如果其他地方也需要重試）
- 不利用現有的重試框架

---

## 測試與驗證計畫

### 1. 單元測試

```python
# tests/test_llm_service_retry.py
import pytest
from src.functions.utils.llm_service import _call_llm_with_retry, _call_llm_core

def test_llm_call_with_retry_success(mocker):
    """測試 LLM 呼叫成功"""
    mock_result = {
        "title": "Test Company",
        "body_html": "<p>Test</p>",
        "summary": "Test Summary"
    }
    mocker.patch('src.functions.utils.llm_service._call_llm_core', return_value=mock_result)
    
    result = _call_llm_with_retry("Test prompt", word_limit=100)
    
    assert result == mock_result


def test_llm_call_with_retry_fallback(mocker):
    """測試 LLM 呼叫失敗時回退到預設響應"""
    mocker.patch('src.functions.utils.llm_service._call_llm_core', side_effect=Exception("API Error"))
    
    result = _call_llm_with_retry("Test prompt", word_limit=100)
    
    assert result is not None
    assert "title" in result
    assert "body_html" in result


def test_llm_call_with_multiple_retries(mocker):
    """測試多次重試機制"""
    call_count = [0]
    
    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] < 3:
            raise Exception("Temporary failure")
        return {
            "title": "Success",
            "body_html": "<p>Success</p>",
            "summary": "Success"
        }
    
    mocker.patch('src.functions.utils.llm_service._call_llm_core', side_effect=side_effect)
    
    result = _call_llm_with_retry("Test prompt")
    
    assert result["title"] == "Success"
    assert call_count[0] >= 2
```

### 2. 整合測試

```python
# tests/test_api_llm_integration.py
def test_api_generate_brief_with_word_limit():
    """測試包含 word_limit 的完整 API 流程"""
    from src.functions.api_controller import generate_brief
    
    payload = {
        "company_name": "Test Co",
        "industry": "Technology",
        "description": "A test company",
        "word_limit": 50
    }
    
    result = generate_brief(payload)
    
    assert result["status"] == "success"
    assert "brief" in result
```

### 3. 驗證檢查清單

- [ ] 選定修復方案（A/B/C）
- [ ] 實施代碼修改
- [ ] 運行單元測試，確保通過
- [ ] 運行整合測試，確保 API 端對端可用
- [ ] 本地啟動後端，手動測試 `POST /api/brief` 端點
- [ ] 確認沒有新的錯誤訊息
- [ ] 提交代碼變更

---

## 推薦實施步驟

1. **優先使用方案 A**（修改函數簽名），因為：
   - 改動最小
   - 符合裝飾器設計
   - 風險最低

2. **次選方案 B**（改進裝飾器），如果：
   - 多個地方需要多參數重試函數
   - 團隊決定改進整體設計

3. **避免方案 C**，除非：
   - 決定放棄使用裝飾器模式
   - 需要更直接的控制流

---

## 記錄者
由專案分析與開發助理自動產生，日期：2026-04-08

---

> **後續步驟**：backend developer 應根據本分析選擇合適方案，實施修改，並執行測試驗證。
