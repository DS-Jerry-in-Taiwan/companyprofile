import os
import sys
from dotenv import load_dotenv
import logging

# 確保 src 目錄在 Python 路徑中
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv()

logger = logging.getLogger(__name__)

# 嘗試導入 LangChain 錯誤處理
try:
    from src.langchain.error_handlers import with_retry, RetryableError
    from src.langchain.retry_config import get_retry_config

    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangChain error handling not available: {e}")
    LANGCHAIN_AVAILABLE = False


def get_llm_service():
    """取得 LLM Service 實例"""
    from src.services.llm_service import LLMService

    return LLMService()


def call_llm(prompt, word_limit=None) -> dict:
    """
    呼叫 LLM API 生成公司簡介（帶重試機制）

    Args:
        prompt: 公司資料 (dict) 或 prompt 字串 (str)
        word_limit: 字數限制（可選）

    Returns:
        dict: 包含 title, body_html, summary 的字典
    """
    if LANGCHAIN_AVAILABLE:
        return _call_llm_with_retry(prompt, word_limit)
    else:
        return _call_llm_original(prompt, word_limit)


def _call_llm_with_retry(prompt, word_limit=None) -> dict:
    """使用重試機制的 LLM 呼叫"""
    try:
        retry_config = get_retry_config()

        @with_retry(retry_config, "llm_call")
        def llm_call_with_retry(inputs):
            # 解包 inputs 字典以支援裝飾器的單參數設計
            prompt_data = inputs.get("prompt")
            wl = inputs.get("word_limit")
            return _call_llm_core(prompt_data, wl)

        # 將參數打包為字典傳遞給裝飾後的函數
        return llm_call_with_retry({"prompt": prompt, "word_limit": word_limit})

    except Exception as e:
        logger.error(f"LLM call with retry failed: {e}")
        # 作為最後手段，回傳預設回應
        return _get_default_response(prompt)


def _call_llm_original(prompt, word_limit=None) -> dict:
    """原始 LLM 呼叫邏輯"""
    try:
        return _call_llm_core(prompt, word_limit)
    except Exception as e:
        logger.error(f"LLM API call failed: {str(e)}")
        return _get_default_response(prompt)


def _call_llm_core(prompt, word_limit=None) -> dict:
    """核心 LLM 呼叫邏輯 - 直接使用傳入的 Prompt（包含 Few-shot）"""
    try:
        from google.genai import types

        service = get_llm_service()

        # 動態計算 max_output_tokens
        # 公式：min(word_limit * 2, 4096)
        if word_limit:
            max_tokens = min(word_limit * 2, 4096)
        else:
            max_tokens = 4096

        # 直接使用 service 的 Gemini API 呼叫，傳入我們的 prompt
        response = service.client.models.generate_content(
            model=service.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2, max_output_tokens=max_tokens
            ),
        )

        # 獲取回應文字
        response_text = response.text.strip()

        # 嘗試解析為 JSON
        try:
            result = service._parse_response(response_text)
            return {
                "title": result.title,
                "body_html": result.body_html,
                "summary": result.summary,
            }
        except (ValueError, Exception) as json_error:
            # JSON 解析失敗，使用純文字回應
            logger.info(f"LLM 返回純文字回應，直接使用")

            # 從 prompt 中提取公司名稱
            company_name = "公司"
            if isinstance(prompt, str):
                for line in prompt.split("\n"):
                    if "公司名稱" in line:
                        parts = line.split("：")
                        if len(parts) > 1:
                            company_name = parts[1].strip()
                            break

            return {
                "title": f"{company_name} - 企業簡介",
                "body_html": f"<p>{response_text}</p>",
                "summary": response_text[:100] + "..."
                if len(response_text) > 100
                else response_text,
            }

    except Exception as e:
        if LANGCHAIN_AVAILABLE:
            # 將錯誤包裝為可重試的錯誤
            raise RetryableError(f"LLM API call failed: {str(e)}", "LLMError", e)
        else:
            raise RuntimeError(f"LLM API call failed: {str(e)}")


def _get_default_response(prompt) -> dict:
    """當所有重試都失敗時的預設回應"""
    company_name = "公司"

    if isinstance(prompt, str):
        # 嘗試從字串中提取公司名稱
        lines = prompt.split("\n")
        for line in lines:
            if "公司名稱" in line or "company_name" in line.lower():
                parts = line.split("：") or line.split(":")
                if len(parts) > 1:
                    company_name = parts[1].strip()
                    break
    elif isinstance(prompt, dict):
        company_name = prompt.get("company_name", prompt.get("organ", "公司"))

    logger.warning(f"返回 {company_name} 的預設回應")

    return {
        "title": f"{company_name} - 企業簡介",
        "body_html": f"<p>{company_name} 是一家專業的企業，致力於提供優質的產品和服務。</p>",
        "summary": f"{company_name} - 專業企業，提供優質產品和服務。",
    }
