# llm_tool.py
"""
LLM Tool for LangChain

將 LLM 生成功能包裝為 LangChain Tool。
"""

import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

try:
    from langchain.tools import tool, BaseTool
    from langchain.callbacks.manager import CallbackManagerForToolRun

    LANGCHAIN_TOOLS_AVAILABLE = True
except ImportError:
    # 如果 LangChain tools 還未安裝，提供基本實作
    BaseTool = object
    tool = lambda func: func
    CallbackManagerForToolRun = object
    BaseModel = object
    Field = lambda **kwargs: None
    LANGCHAIN_TOOLS_AVAILABLE = False

logger = logging.getLogger(__name__)


class LLMGenerateInput(BaseModel):
    """LLM 生成工具的輸入模式"""

    prompt: str = Field(description="完整的 prompt 字串")
    company_name: Optional[str] = Field(
        default=None, description="公司名稱（可選，用於預設回應）"
    )


class LLMGenerateOutput(BaseModel):
    """LLM 生成工具的輸出模式"""

    success: bool = Field(description="生成是否成功")
    title: Optional[str] = Field(description="生成的標題")
    body_html: Optional[str] = Field(description="生成的 HTML 內容")
    summary: Optional[str] = Field(description="生成的摘要")
    execution_time: float = Field(description="執行時間（秒）")
    error: Optional[str] = Field(description="錯誤訊息（如果有）")


if LANGCHAIN_TOOLS_AVAILABLE:

    class LLMGenerateTool(BaseTool):
        """LLM 生成工具類別"""

        name: str = "llm_generate"
        description: str = (
            "使用 LLM 生成公司簡介內容。"
            "接收組裝好的 prompt 並生成標題、HTML內容和摘要。"
            "輸入格式：{'prompt': '完整prompt字串', 'company_name': '公司名稱'}"
        )
        args_schema = LLMGenerateInput

        def _run(
            self,
            prompt: str,
            company_name: Optional[str] = None,
            run_manager: Optional[CallbackManagerForToolRun] = None,
        ) -> Dict[str, Any]:
            """執行 LLM 生成"""
            try:
                # 導入 LLM 功能
                import sys
                import os

                PROJECT_ROOT = os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        )
                    )
                )
                if PROJECT_ROOT not in sys.path:
                    sys.path.insert(0, PROJECT_ROOT)

                from src.functions.utils.llm_service import call_llm
                import time

                start_time = time.time()

                # 記錄生成開始
                logger.info(f"[LLMGenerateTool] 開始生成簡介，公司: {company_name}")

                # 執行 LLM 生成
                result = call_llm(prompt)

                execution_time = time.time() - start_time

                # 格式化輸出
                output = {
                    "success": True,
                    "title": result.get("title"),
                    "body_html": result.get("body_html"),
                    "summary": result.get("summary"),
                    "execution_time": execution_time,
                    "error": None,
                }

                logger.info(f"[LLMGenerateTool] 生成完成，耗時: {execution_time:.2f}s")

                return output

            except Exception as e:
                execution_time = (
                    time.time() - start_time if "start_time" in locals() else 0.0
                )
                logger.error(f"[LLMGenerateTool] 生成失敗: {e}")

                # 回傳預設結果
                default_company_name = company_name or "公司"
                return {
                    "success": False,
                    "title": f"{default_company_name} - 企業簡介",
                    "body_html": f"<p>{default_company_name} 是一家專業的企業，致力於提供優質的產品和服務。</p>",
                    "summary": f"{default_company_name} - 專業企業，提供優質產品和服務。",
                    "execution_time": execution_time,
                    "error": str(e),
                }


# 函式版本的 Tool
@tool
def llm_generate_tool(
    prompt: str, company_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    使用 LLM 生成公司簡介內容

    Args:
        prompt: 完整的 prompt 字串，包含所有必要資訊
        company_name: 公司名稱（可選，用於預設回應）

    Returns:
        包含生成結果的字典：
        - success: 生成是否成功
        - title: 生成的標題
        - body_html: 生成的 HTML 內容
        - summary: 生成的摘要
        - execution_time: 執行時間
    """
    try:
        # 導入 LLM 功能
        import sys
        import os

        PROJECT_ROOT = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
            )
        )
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)

        from src.functions.utils.llm_service import call_llm
        import time

        start_time = time.time()

        logger.info(f"[llm_generate_tool] 開始生成簡介，公司: {company_name}")

        # 執行 LLM 生成
        result = call_llm(prompt)

        execution_time = time.time() - start_time

        # 格式化輸出
        output = {
            "success": True,
            "title": result.get("title"),
            "body_html": result.get("body_html"),
            "summary": result.get("summary"),
            "execution_time": execution_time,
            "error": None,
        }

        logger.info(f"[llm_generate_tool] 生成完成，耗時: {execution_time:.2f}s")

        return output

    except Exception as e:
        execution_time = time.time() - start_time if "start_time" in locals() else 0.0
        logger.error(f"[llm_generate_tool] 生成失敗: {e}")

        # 回傳預設結果
        default_company_name = company_name or "公司"
        return {
            "success": False,
            "title": f"{default_company_name} - 企業簡介",
            "body_html": f"<p>{default_company_name} 是一家專業的企業，致力於提供優質的產品和服務。</p>",
            "summary": f"{default_company_name} - 專業企業，提供優質產品和服務。",
            "execution_time": execution_time,
            "error": str(e),
        }


@tool
def build_prompt_tool(
    organ: str,
    organ_no: Optional[str] = None,
    company_url: Optional[str] = None,
    user_brief: Optional[str] = None,
    web_content: Optional[str] = None,
) -> str:
    """
    建構 LLM 生成用的 prompt

    Args:
        organ: 公司名稱
        organ_no: 統一編號（可選）
        company_url: 公司官網（可選）
        user_brief: 用戶提供的簡介（可選）
        web_content: 網路搜尋的內容（可選）

    Returns:
        完整的 prompt 字串
    """
    try:
        # 導入 prompt building 功能
        import sys
        import os

        PROJECT_ROOT = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
            )
        )
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)

        from src.functions.utils.prompt_builder import build_generate_prompt

        logger.info(f"[build_prompt_tool] 建構 prompt，公司: {organ}")

        # 建構 prompt
        prompt = build_generate_prompt(
            organ=organ,
            organ_no=organ_no,
            company_url=company_url,
            user_brief=user_brief,
            web_content=web_content,
        )

        logger.info(f"[build_prompt_tool] Prompt 建構完成，長度: {len(prompt)}")

        return prompt

    except Exception as e:
        logger.error(f"[build_prompt_tool] Prompt 建構失敗: {e}")

        # 回傳基本 prompt
        basic_prompt = f"""
## 公司基本資訊
公司名稱：{organ}
{"統一編號：" + organ_no if organ_no else ""}
{"官網：" + company_url if company_url else ""}

## 輸出要求
請生成一段專業、簡潔的公司簡介（200-300字）。
"""
        return basic_prompt.strip()


@tool
def generate_company_brief_complete(
    organ: str,
    organ_no: Optional[str] = None,
    company_url: Optional[str] = None,
    user_brief: Optional[str] = None,
    web_content: Optional[str] = None,
) -> Dict[str, Any]:
    """
    完整的公司簡介生成工具（組合 prompt 建構和 LLM 生成）

    Args:
        organ: 公司名稱
        organ_no: 統一編號（可選）
        company_url: 公司官網（可選）
        user_brief: 用戶提供的簡介（可選）
        web_content: 網路搜尋的內容（可選）

    Returns:
        生成結果字典
    """
    try:
        logger.info(
            f"[generate_company_brief_complete] 開始完整生成流程，公司: {organ}"
        )

        # 第一步：建構 prompt
        prompt = build_prompt_tool(
            organ, organ_no, company_url, user_brief, web_content
        )

        # 第二步：生成內容
        result = llm_generate_tool(prompt, organ)

        # 添加輸入資訊到結果中
        result["input_info"] = {
            "organ": organ,
            "organ_no": organ_no,
            "company_url": company_url,
            "has_user_brief": bool(user_brief),
            "has_web_content": bool(web_content),
            "prompt_length": len(prompt),
        }

        logger.info(
            f"[generate_company_brief_complete] 完整生成完成，成功: {result['success']}"
        )

        return result

    except Exception as e:
        logger.error(f"[generate_company_brief_complete] 完整生成失敗: {e}")

        # 回傳預設結果
        return {
            "success": False,
            "title": f"{organ} - 企業簡介",
            "body_html": f"<p>{organ} 是一家專業的企業，致力於提供優質的產品和服務。</p>",
            "summary": f"{organ} - 專業企業，提供優質產品和服務。",
            "execution_time": 0.0,
            "error": str(e),
            "input_info": {
                "organ": organ,
                "organ_no": organ_no,
                "company_url": company_url,
                "has_user_brief": bool(user_brief),
                "has_web_content": bool(web_content),
            },
        }


# 便捷函式
def create_llm_generate_tool():
    """建立 LLM 生成工具實例"""
    if LANGCHAIN_TOOLS_AVAILABLE:
        return LLMGenerateTool()
    else:
        return llm_generate_tool
