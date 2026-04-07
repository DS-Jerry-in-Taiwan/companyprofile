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


def call_llm(prompt) -> dict:
    """
    呼叫 LLM API 生成公司簡介（帶重試機制）

    Args:
        prompt: 公司資料 (dict) 或 prompt 字串 (str)

    Returns:
        dict: 包含 title, body_html, summary 的字典
    """
    if LANGCHAIN_AVAILABLE:
        return _call_llm_with_retry(prompt)
    else:
        return _call_llm_original(prompt)


def _call_llm_with_retry(prompt) -> dict:
    """使用重試機制的 LLM 呼叫"""
    try:
        retry_config = get_retry_config()

        @with_retry(retry_config, "llm_call")
        def llm_call_with_retry(input_data):
            return _call_llm_core(input_data)

        return llm_call_with_retry(prompt)

    except Exception as e:
        logger.error(f"LLM call with retry failed: {e}")
        # 作為最後手段，回傳預設回應
        return _get_default_response(prompt)


def _call_llm_original(prompt) -> dict:
    """原始 LLM 呼叫邏輯"""
    try:
        return _call_llm_core(prompt)
    except Exception as e:
        logger.error(f"LLM API call failed: {str(e)}")
        return _get_default_response(prompt)


def _call_llm_core(prompt) -> dict:
    """核心 LLM 呼叫邏輯"""
    try:
        service = get_llm_service()

        if isinstance(prompt, str):
            company_data = {
                "company_name": "公司",
                "industry": "一般",
                "description": prompt,
                "products_services": "產品服務",
                "company_size": "中小型",
                "founded_year": "2000",
            }
        else:
            company_data = {
                "company_name": prompt.get("company_name", "公司"),
                "industry": prompt.get("industry", "一般"),
                "description": prompt.get("description", prompt.get("prompt", "")),
                "products_services": prompt.get(
                    "products_services", prompt.get("key_products", "")
                ),
                "company_size": prompt.get("company_size", "中小型"),
                "founded_year": prompt.get("founded_year", "2000"),
            }

        result = service.generate(company_data)

        return {
            "title": result.title,
            "body_html": result.body_html,
            "summary": result.summary,
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
