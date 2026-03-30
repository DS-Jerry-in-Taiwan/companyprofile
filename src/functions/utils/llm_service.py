import os
from dotenv import load_dotenv

load_dotenv()


def get_llm_service():
    """取得 LLM Service 實例"""
    from src.services.llm_service import LLMService

    return LLMService()


def call_llm(prompt) -> dict:
    """
    呼叫 LLM API 生成公司簡介

    Args:
        prompt: 公司資料 (dict) 或 prompt 字串 (str)

    Returns:
        dict: 包含 title, body_html, summary 的字典
    """
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
        raise RuntimeError(f"LLM API call failed: {str(e)}")
