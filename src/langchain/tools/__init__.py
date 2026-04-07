# __init__.py
"""
LangChain Tools Collection

統一管理所有 LangChain Tool，提供便捷的導入和使用介面。
"""

import logging
from typing import List, Dict, Any, Optional

# 導入所有 Tool
from .tavily_tool import (
    tavily_search,
    create_tavily_search_tool,
    search_company_info_tool,
)

from .search_tool import (
    web_search_tool,
    extract_content_tool,
    create_web_search_tool,
    search_and_extract_company_info,
)

from .llm_tool import (
    llm_generate_tool,
    build_prompt_tool,
    generate_company_brief_complete,
    create_llm_generate_tool,
)

logger = logging.getLogger(__name__)

# ===== Tool 註冊表 =====

AVAILABLE_TOOLS = {
    # 搜尋相關 Tools
    "tavily_search": tavily_search,
    "web_search": web_search_tool,
    "extract_content": extract_content_tool,
    "search_company_info": search_company_info_tool,
    "search_and_extract_company_info": search_and_extract_company_info,
    # LLM 相關 Tools
    "llm_generate": llm_generate_tool,
    "build_prompt": build_prompt_tool,
    "generate_company_brief_complete": generate_company_brief_complete,
}

TOOL_CATEGORIES = {
    "search": [
        "tavily_search",
        "web_search",
        "extract_content",
        "search_company_info",
        "search_and_extract_company_info",
    ],
    "llm": [
        "llm_generate",
        "build_prompt",
        "generate_company_brief_complete",
    ],
    "all": list(AVAILABLE_TOOLS.keys()),
}

TOOL_DESCRIPTIONS = {
    "tavily_search": "使用 Tavily API 進行網路搜尋並提取內容（主要搜尋方式）",
    "web_search": "使用傳統網路搜尋查找公司官網（備用搜尋方式）",
    "extract_content": "從 URL 列表提取網頁內容",
    "search_company_info": "搜尋公司資訊的便捷工具（使用 Tavily）",
    "search_and_extract_company_info": "搜尋並提取公司資訊的完整工具（使用傳統搜尋）",
    "llm_generate": "使用 LLM 生成公司簡介內容",
    "build_prompt": "建構 LLM 生成用的 prompt",
    "generate_company_brief_complete": "完整的公司簡介生成工具（組合 prompt 建構和 LLM 生成）",
}

# ===== Tool 管理類別 =====


class ToolManager:
    """Tool 管理器"""

    def __init__(self):
        """初始化 Tool 管理器"""
        self.tools = AVAILABLE_TOOLS.copy()
        self.categories = TOOL_CATEGORIES.copy()
        self.descriptions = TOOL_DESCRIPTIONS.copy()

    def get_tool(self, tool_name: str):
        """
        取得指定的 Tool

        Args:
            tool_name: Tool 名稱

        Returns:
            Tool 函式或類別

        Raises:
            ValueError: 如果 Tool 不存在
        """
        if tool_name not in self.tools:
            available = list(self.tools.keys())
            raise ValueError(
                f"Tool '{tool_name}' not found. Available tools: {available}"
            )

        return self.tools[tool_name]

    def get_tools_by_category(self, category: str) -> Dict[str, Any]:
        """
        取得指定類別的所有 Tools

        Args:
            category: Tool 類別（search, llm, all）

        Returns:
            Tool 字典

        Raises:
            ValueError: 如果類別不存在
        """
        if category not in self.categories:
            available = list(self.categories.keys())
            raise ValueError(
                f"Category '{category}' not found. Available categories: {available}"
            )

        tool_names = self.categories[category]
        return {name: self.tools[name] for name in tool_names if name in self.tools}

    def list_tools(self, category: Optional[str] = None) -> List[Dict[str, str]]:
        """
        列出所有可用的 Tools

        Args:
            category: 篩選的類別（可選）

        Returns:
            Tool 資訊列表
        """
        if category:
            tool_names = self.categories.get(category, [])
        else:
            tool_names = list(self.tools.keys())

        return [
            {
                "name": name,
                "description": self.descriptions.get(name, "No description available"),
                "category": self._get_tool_category(name),
            }
            for name in tool_names
        ]

    def _get_tool_category(self, tool_name: str) -> str:
        """取得 Tool 的類別"""
        for category, tools in self.categories.items():
            if category != "all" and tool_name in tools:
                return category
        return "unknown"

    def register_tool(
        self, name: str, tool: Any, description: str = "", category: str = "custom"
    ):
        """
        註冊新的 Tool

        Args:
            name: Tool 名稱
            tool: Tool 函式或類別
            description: Tool 描述
            category: Tool 類別
        """
        self.tools[name] = tool
        self.descriptions[name] = description

        if category not in self.categories:
            self.categories[category] = []

        if name not in self.categories[category]:
            self.categories[category].append(name)

        # 更新 all 類別
        if name not in self.categories["all"]:
            self.categories["all"].append(name)

        logger.info(f"已註冊 Tool: {name} (類別: {category})")


# ===== 全域 Tool 管理器實例 =====

tool_manager = ToolManager()

# ===== 便捷函式 =====


def get_tool(tool_name: str):
    """取得指定的 Tool（便捷函式）"""
    return tool_manager.get_tool(tool_name)


def get_search_tools() -> Dict[str, Any]:
    """取得所有搜尋相關的 Tools"""
    return tool_manager.get_tools_by_category("search")


def get_llm_tools() -> Dict[str, Any]:
    """取得所有 LLM 相關的 Tools"""
    return tool_manager.get_tools_by_category("llm")


def get_all_tools() -> Dict[str, Any]:
    """取得所有可用的 Tools"""
    return tool_manager.get_tools_by_category("all")


def get_available_tools() -> List[Dict[str, str]]:
    """取得所有可用的 Tools"""
    return tool_manager.list_tools()


def list_available_tools(category: Optional[str] = None) -> List[Dict[str, str]]:
    """列出所有可用的 Tools（便捷函式）"""
    return tool_manager.list_tools(category)


def create_tool_list_for_langchain() -> List[Any]:
    """
    建立 LangChain 可用的 Tool 列表

    Returns:
        LangChain Tool 列表
    """
    tools = []

    try:
        # 嘗試建立 Tool 類別實例
        tools.extend(
            [
                create_tavily_search_tool(),
                create_web_search_tool(),
                create_llm_generate_tool(),
            ]
        )
    except Exception as e:
        logger.warning(f"無法建立 LangChain Tool 類別實例: {e}")
        # 使用函式版本
        tools.extend(
            [
                tavily_search,
                web_search_tool,
                llm_generate_tool,
            ]
        )

    return tools


# ===== 高階工作流程 =====


def execute_company_brief_workflow(
    organ: str,
    organ_no: Optional[str] = None,
    company_url: Optional[str] = None,
    user_brief: Optional[str] = None,
    preferred_search: str = "tavily",
) -> Dict[str, Any]:
    """
    執行完整的公司簡介生成工作流程

    Args:
        organ: 公司名稱
        organ_no: 統一編號（可選）
        company_url: 公司官網（可選）
        user_brief: 用戶簡介（可選）
        preferred_search: 偏好的搜尋方式（tavily 或 web_search）

    Returns:
        完整的執行結果
    """
    logger.info(f"開始執行公司簡介生成工作流程: {organ}")
    workflow_result = {
        "organ": organ,
        "search_phase": {},
        "generation_phase": {},
        "final_result": {},
        "execution_summary": {},
    }

    try:
        import time

        start_time = time.time()

        # 第一階段：搜尋公司資訊
        logger.info(f"第一階段：搜尋 {organ} 的資訊")

        search_result = None
        web_content = None

        if preferred_search == "tavily":
            search_tool = get_tool("tavily_search")
            search_result = search_tool(f"{organ} 官網", max_results=3)

            if search_result.get("success"):
                web_content = search_result.get("answer")
                if not web_content and search_result.get("results"):
                    # 合併搜尋結果內容
                    contents = []
                    for result in search_result["results"][:3]:
                        if result.get("content"):
                            contents.append(result["content"])
                    web_content = "\n\n".join(contents)
        else:
            # 使用傳統搜尋
            search_extract_tool = get_tool("search_and_extract_company_info")
            search_result = search_extract_tool(organ, company_url)

            if search_result.get("success"):
                extraction_result = search_result.get("extraction_result", {})
                contents = extraction_result.get("contents", [])
                if contents:
                    # 合併提取的內容
                    web_content = "\n\n".join(
                        [
                            c["content"]
                            for c in contents
                            if c.get("success") and c.get("content")
                        ]
                    )

        workflow_result["search_phase"] = {
            "method": preferred_search,
            "success": search_result.get("success", False) if search_result else False,
            "result": search_result,
            "has_content": bool(web_content),
            "content_length": len(web_content) if web_content else 0,
        }

        # 第二階段：生成公司簡介
        logger.info(f"第二階段：生成 {organ} 的簡介")

        generate_tool = get_tool("generate_company_brief_complete")
        generation_result = generate_tool(
            organ=organ,
            organ_no=organ_no,
            company_url=company_url,
            user_brief=user_brief,
            web_content=web_content,
        )

        workflow_result["generation_phase"] = generation_result

        # 第三階段：整理最終結果
        execution_time = time.time() - start_time

        workflow_result["final_result"] = {
            "title": generation_result.get("title"),
            "body_html": generation_result.get("body_html"),
            "summary": generation_result.get("summary"),
            "success": generation_result.get("success", False),
            "quality_metadata": {
                "search_success": workflow_result["search_phase"]["success"],
                "search_method": preferred_search,
                "has_web_content": workflow_result["search_phase"]["has_content"],
                "has_user_brief": bool(user_brief),
                "generation_success": generation_result.get("success", False),
            },
        }

        workflow_result["execution_summary"] = {
            "total_time": execution_time,
            "search_time": search_result.get("execution_time", 0)
            if search_result
            else 0,
            "generation_time": generation_result.get("execution_time", 0),
            "success": workflow_result["final_result"]["success"],
            "error_count": len(
                [
                    phase
                    for phase in [
                        workflow_result["search_phase"],
                        workflow_result["generation_phase"],
                    ]
                    if not phase.get("success", True)
                ]
            ),
        }

        logger.info(f"工作流程完成: {workflow_result['execution_summary']}")

        return workflow_result

    except Exception as e:
        logger.error(f"工作流程執行失敗: {e}")

        # 回傳預設結果
        workflow_result["final_result"] = {
            "title": f"{organ} - 企業簡介",
            "body_html": f"<p>{organ} 是一家專業的企業，致力於提供優質的產品和服務。</p>",
            "summary": f"{organ} - 專業企業，提供優質產品和服務。",
            "success": False,
            "error": str(e),
        }

        workflow_result["execution_summary"] = {
            "total_time": 0.0,
            "success": False,
            "error": str(e),
        }

        return workflow_result


# ===== 模組匯出 =====

__all__ = [
    # Tool 管理
    "ToolManager",
    "tool_manager",
    # 便捷函式
    "get_tool",
    "get_search_tools",
    "get_llm_tools",
    "get_all_tools",
    "get_available_tools",
    "list_available_tools",
    "create_tool_list_for_langchain",
    # 工作流程
    "execute_company_brief_workflow",
    # 個別 Tools
    "tavily_search",
    "web_search_tool",
    "llm_generate_tool",
    "build_prompt_tool",
    "generate_company_brief_complete",
    # Tool 建立函式
    "create_tavily_search_tool",
    "create_web_search_tool",
    "create_llm_generate_tool",
    # 便捷工具
    "search_company_info_tool",
    "search_and_extract_company_info",
]
