# Phase 22 詳細開發計劃

## 版本
- **文件版本**: v0.2.0
- **建立日期**: 2026-04-23
- **完成日期**: 2026-04-23

---

## Step 1: 建立單元測試（TDD）

### 目標
先寫測試案例，定義 expected behavior

### 測試檔案
`/home/ubuntu/projects/OrganBriefOptimization/tests/test_markdown_cleaner.py`

### 測試案例

```python
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.functions.utils.markdown_cleaner import clean_markdown

class TestMarkdownCleaner(unittest.TestCase):
    
    def test_bold_double_asterisk(self):
        """測試 **bold** 清理"""
        input_text = "**艾兒莫拉韓系服飾**秉持著專業"
        expected = "艾兒莫拉韓系服飾秉持著專業"
        self.assertEqual(clean_markdown(input_text), expected)
    
    def test_header_h2(self):
        """測試 ## 二級標題"""
        input_text = "## 公司簡介\n這是內容"
        expected = "公司簡介\n這是內容"
        self.assertEqual(clean_markdown(input_text), expected)
    
    def test_header_h3(self):
        """測試 ### 三級標題"""
        input_text = "### 服務項目\n這是內容"
        expected = "服務項目\n這是內容"
        self.assertEqual(clean_markdown(input_text), expected)
    
    def test_no_markdown(self):
        """測試無 Markdown 的正常文字"""
        input_text = "這是一般公司簡介內容"
        self.assertEqual(clean_markdown(input_text), input_text)
    
    def test_preserve_phone_format(self):
        """測試保留電話號碼格式（***-****-****）"""
        input_text = "聯絡電話：***-****-****"
        expected = "聯絡電話：***-****-****"
        self.assertEqual(clean_markdown(input_text), expected)
```

### 執行測試
```bash
cd /home/ubuntu/projects/OrganBriefOptimization
python -m pytest tests/test_markdown_cleaner.py -v
```

---

## Step 2: 實作 Markdown 清理模組

### 新增檔案
`/home/ubuntu/projects/OrganBriefOptimization/src/functions/utils/markdown_cleaner.py`

### 實作內容

```python
"""
Markdown Cleaner - 清理 LLM 輸出中的 Markdown 語法

這個模組用於移除公司簡介中的 Markdown 格式（**、##、### 等）
確保輸出為乾淨的純文字或 HTML 格式
"""

import re
from typing import Optional


def clean_markdown(text: str) -> str:
    """
    清理文字中的 Markdown 語法
    
    Args:
        text: 原始文字，可能包含 Markdown 語法
        
    Returns:
        str: 清理後的文字
    """
    if not text:
        return text
    
    # 1. 移除 **bold** 語法（但保留 *** 作為電話號碼格式）
    # 使用負向先行斷言，避免匹配 ***-****-****
    text = re.sub(r'\*\*(?!\*)([^*]+)\*\*', r'\1', text)
    
    # 2. 移除 ### 三級標題
    text = re.sub(r'^#{1,3}\s+', '', text, flags=re.MULTILINE)
    
    # 3. 移除 ## 二級標題（與上一步合併處理）
    
    # 4. 移除 - 列表符號（可選）
    # text = re.sub(r'^[-*]\s+', '', text, flags=re.MULTILINE)
    
    # 5. 移除 *italic* 語法（可選）
    # text = re.sub(r'\*([^*]+)\*', r'\1', text)
    
    return text


def clean_markdown_aggressive(text: str) -> str:
    """
    激進清理模式 - 移除所有 Markdown 語法
    
    Args:
        text: 原始文字
        
    Returns:
        str: 清理後的文字
    """
    if not text:
        return text
    
    # 移除所有 * 和 # 開頭的 Markdown 符號
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    return text


# ========== 測試入口 ==========
if __name__ == "__main__":
    # 簡單測試
    test_cases = [
        ("**艾兒莫拉韓系服飾**", "艾兒莫拉韓系服飾"),
        ("## 公司簡介\n內容", "公司簡介\n內容"),
        ("### 服務項目\n內容", "服務項目\n內容"),
        ("這是正常文字", "這是正常文字"),
        ("聯絡電話：***-****-****", "聯絡電話：***-****-****"),
    ]
    
    for input_text, expected in test_cases:
        result = clean_markdown(input_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} input: {input_text}")
        print(f"   expected: {expected}")
        print(f"   got:      {result}")
        print()
```

---

## Step 3: 整合到現有程式碼

### 選項 A: 整合到 llm_service.py

在 `src/services/llm_service.py` 的 `_parse_response` 方法中加入：

```python
# 在解析 JSON 後，加入 Markdown 清理
from src.functions.utils.markdown_cleaner import clean_markdown

# 清理 body_html 中的 Markdown
if hasattr(result, 'body_html') and result.body_html:
    result.body_html = clean_markdown(result.body_html)
```

### 選項 B: 整合到 post_processing.py（推薦）

在 `src/functions/utils/post_processing.py` 的 `_normalize_plain_text_format` 或新增 `_clean_markdown` 函數：

```python
def _clean_markdown(text: str) -> str:
    """清理 Markdown 語法"""
    from src.functions.utils.markdown_cleaner import clean_markdown
    return clean_markdown(text)
```

然後在 `post_process_html` 或 `process_output` 中呼叫。

---

## Step 4: 整合測試驗證

### 測試腳本
`/home/ubuntu/projects/OrganBriefOptimization/scripts/test_markdown_cleanup.py`

### 測試內容

```python
#!/usr/bin/env python3
"""Markdown 清理整合測試"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.functions.utils.markdown_cleaner import clean_markdown

def test_real_output():
    """測試真實 LLM 輸出"""
    
    # 模擬 Phase 14 Stage 2 問題輸出
    test_cases = [
        {
            "name": "格式汙染案例 1",
            "input": "**艾兒莫拉韓系服飾**秉持著專業與穩健的經營精神，將「服務客戶至上」奉為核心宗旨。",
            "expected_not_contains": ["**"]
        },
        {
            "name": "格式汙染案例 2", 
            "input": "## 公司簡介\n全球華人集團成立於1999年...",
            "expected_not_contains": ["##"]
        },
        {
            "name": "正常輸出",
            "input": "這是一家專業的科技公司，致力於提供優質的產品和服務。",
            "expected_not_contains": []
        }
    ]
    
    all_passed = True
    
    for case in test_cases:
        result = clean_markdown(case["input"])
        
        # 檢查不應該包含的字符
        passed = True
        for char in case.get("expected_not_contains", []):
            if char in result:
                passed = False
                all_passed = False
                print(f"❌ {case['name']}: 仍有 '{char}' 殘留")
                print(f"   輸入: {case['input']}")
                print(f"   輸出: {result}")
                break
        
        if passed:
            print(f"✅ {case['name']}")
    
    return all_passed


def test_performance():
    """測試處理速度"""
    import time
    
    # 生成測試文字
    long_text = "**測試內容**\n" * 1000
    
    start = time.time()
    for _ in range(100):
        clean_markdown(long_text)
    elapsed = time.time() - start
    
    avg_ms = (elapsed / 100) * 1000
    print(f"\n⏱️  平均處理時間: {avg_ms:.2f}ms")
    
    if avg_ms < 50:
        print("✅ 性能測試通過 (< 50ms)")
        return True
    else:
        print("❌ 性能測試失敗 (>= 50ms)")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Markdown 清理整合測試")
    print("=" * 50)
    
    result1 = test_real_output()
    result2 = test_performance()
    
    print("\n" + "=" * 50)
    if result1 and result2:
        print("🎉 所有測試通過！")
    else:
        print("⚠️ 部分測試失敗")
    print("=" * 50)
```

### 執行測試
```bash
cd /home/ubuntu/projects/OrganBriefOptimization
python scripts/test_markdown_cleanup.py
```

---

## Step 5: 更新 Prompt 範例（可選）

在 `src/functions/utils/prompt_builder.py` 的 Few-shot 範例中加入：

```python
# 在輸出要求中新增
sections.append("\n⚠️ 禁止事項")
sections.append("- 禁止使用 Markdown 語法（**、##、### 等）")
sections.append("- 輸出應為流暢的段落文字，避免使用列表或標題格式")
```

---

## 預期時間

| 步驟 | 預估時間 |
|------|---------|
| Step 1: 單元測試 | 15 分鐘 |
| Step 2: 實作模組 | 30 分鐘 |
| Step 3: 整合 | 15 分鐘 |
| Step 4: 整合測試 | 30 分鐘 |
| **總計** | **約 1.5 小時** |

---

## 風險與對策

| 風險 | 對策 |
|------|------|
| 誤傷電話號碼 `***-****-****` | 使用負向先行斷言 `(?!\*)` |
| LLM 生成 HTML 而非 Markdown | 保留 `<p>`, `<b>` 等 HTML 標籤 |
| 處理速度過慢 | 使用正則表達式，目標 < 50ms |

---

## 下一步

→ 閱讀 `TEST_METRICS.md` 確認測試指標 → 開始 Step 1