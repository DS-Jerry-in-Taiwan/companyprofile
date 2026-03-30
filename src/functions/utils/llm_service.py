# gemini_service.py
"""
Gemini Service Wrapper
- 封裝 Gemini API 呼叫
"""


def call_llm(prompt):
    # TODO: 串接真實 LLM API
    # 這裡僅回傳假資料
    return {
        "body_html": f"<p>{prompt}</p>",
        "summary": prompt[:50],
        "tags": ["AI", "公司簡介"],
    }
