# quality_check_tool.py
"""
Quality Check Tool for LangChain

品質檢查工具，驗證生成的公司簡介內容是否符合標準。
"""

import logging
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

try:
    from langchain.tools import tool, BaseTool
    from langchain.callbacks.manager import CallbackManagerForToolRun

    LANGCHAIN_TOOLS_AVAILABLE = True
except ImportError:
    BaseTool = object
    tool = lambda func: func
    CallbackManagerForToolRun = object
    BaseModel = object
    Field = lambda **kwargs: None
    LANGCHAIN_TOOLS_AVAILABLE = False

logger = logging.getLogger(__name__)

# ===== 品質檢查標準定義 =====


class QualityStandards:
    """品質檢查標準"""

    # 長度標準
    MIN_TITLE_LENGTH = 5
    MAX_TITLE_LENGTH = 100
    MIN_CONTENT_LENGTH = 100
    MAX_CONTENT_LENGTH = 5000
    MIN_SUMMARY_LENGTH = 20
    MAX_SUMMARY_LENGTH = 300

    # 必要欄位
    REQUIRED_FIELDS = ["title", "body_html", "summary"]

    # 禁止模式（不應該出現的內容）
    FORBIDDEN_PATTERNS = [
        r"(?i)error\s+occurred",
        r"(?i)failed\s+to",
        r"(?i)not\s+available",
        r"(?i)無法取得",
        r"(?i)錯誤發生",
        r"(?i)查無資料",
        r"(?i)system\s+error",
        r"(?i)技術問題",
        r"(?i)服務暫停",
    ]

    # 公司名稱檢查
    COMPANY_NAME_REQUIRED = True

    # HTML 標籤檢查
    ALLOWED_HTML_TAGS = [
        "p",
        "div",
        "span",
        "br",
        "strong",
        "b",
        "em",
        "i",
        "ul",
        "ol",
        "li",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    ]

    # 品質分數權重
    WEIGHTS = {
        "length": 25,  # 長度適中
        "required_fields": 25,  # 必要欄位完整
        "company_name": 20,  # 包含公司名稱
        "forbidden_patterns": 15,  # 無禁止內容
        "html_format": 10,  # HTML 格式正確
        "content_quality": 5,  # 內容品質
    }

    # 及格分數
    PASSING_SCORE = 70.0


class QualityCheckInput(BaseModel):
    """品質檢查工具的輸入模式"""

    title: Optional[str] = Field(description="生成的標題")
    body_html: Optional[str] = Field(description="生成的 HTML 內容")
    summary: Optional[str] = Field(description="生成的摘要")
    company_name: str = Field(description="公司名稱（用於檢查是否包含）")
    custom_criteria: Optional[Dict[str, Any]] = Field(
        default=None, description="自訂檢查標準"
    )


class QualityCheckOutput(BaseModel):
    """品質檢查工具的輸出模式"""

    passed: bool = Field(description="是否通過品質檢查")
    score: float = Field(description="品質分數（0-100）")
    issues: List[Dict[str, str]] = Field(description="發現的問題列表")
    suggestions: List[Dict[str, str]] = Field(description="改善建議列表")
    details: Dict[str, Any] = Field(description="詳細檢查結果")
    execution_time: float = Field(description="檢查耗時")


class QualityChecker:
    """品質檢查器核心類別"""

    def __init__(self, standards: Optional[QualityStandards] = None):
        """
        初始化品質檢查器

        Args:
            standards: 品質標準（可選，預設使用標準配置）
        """
        self.standards = standards or QualityStandards()

    def check_length(
        self, title: Optional[str], body_html: Optional[str], summary: Optional[str]
    ) -> Dict[str, Any]:
        """檢查長度"""
        result = {"score": 0, "issues": [], "details": {}}

        # 檢查標題長度
        title_length = len(title or "")
        result["details"]["title_length"] = title_length

        if title_length < self.standards.MIN_TITLE_LENGTH:
            result["issues"].append(
                {
                    "type": "title_too_short",
                    "message": f"標題過短（{title_length} 字元，最少需要 {self.standards.MIN_TITLE_LENGTH} 字元）",
                }
            )
        elif title_length > self.standards.MAX_TITLE_LENGTH:
            result["issues"].append(
                {
                    "type": "title_too_long",
                    "message": f"標題過長（{title_length} 字元，最多 {self.standards.MAX_TITLE_LENGTH} 字元）",
                }
            )
        else:
            result["score"] += 33

        # 檢查內容長度
        content_length = len(body_html or "")
        result["details"]["content_length"] = content_length

        if content_length < self.standards.MIN_CONTENT_LENGTH:
            result["issues"].append(
                {
                    "type": "content_too_short",
                    "message": f"內容過短（{content_length} 字元，最少需要 {self.standards.MIN_CONTENT_LENGTH} 字元）",
                }
            )
        elif content_length > self.standards.MAX_CONTENT_LENGTH:
            result["issues"].append(
                {
                    "type": "content_too_long",
                    "message": f"內容過長（{content_length} 字元，最多 {self.standards.MAX_CONTENT_LENGTH} 字元）",
                }
            )
        else:
            result["score"] += 34

        # 檢查摘要長度
        summary_length = len(summary or "")
        result["details"]["summary_length"] = summary_length

        if summary_length < self.standards.MIN_SUMMARY_LENGTH:
            result["issues"].append(
                {
                    "type": "summary_too_short",
                    "message": f"摘要過短（{summary_length} 字元，最少需要 {self.standards.MIN_SUMMARY_LENGTH} 字元）",
                }
            )
        elif summary_length > self.standards.MAX_SUMMARY_LENGTH:
            result["issues"].append(
                {
                    "type": "summary_too_long",
                    "message": f"摘要過長（{summary_length} 字元，最多 {self.standards.MAX_SUMMARY_LENGTH} 字元）",
                }
            )
        else:
            result["score"] += 33

        return result

    def check_required_fields(
        self, title: Optional[str], body_html: Optional[str], summary: Optional[str]
    ) -> Dict[str, Any]:
        """檢查必要欄位"""
        result = {"score": 0, "issues": [], "details": {}}

        fields = {
            "title": title,
            "body_html": body_html,
            "summary": summary,
        }

        missing_fields = []
        empty_fields = []

        for field_name in self.standards.REQUIRED_FIELDS:
            value = fields.get(field_name)
            result["details"][f"has_{field_name}"] = bool(value)

            if value is None:
                missing_fields.append(field_name)
            elif not value.strip():
                empty_fields.append(field_name)
            else:
                result["score"] += 100 // len(self.standards.REQUIRED_FIELDS)

        if missing_fields:
            result["issues"].append(
                {
                    "type": "missing_fields",
                    "message": f"缺少必要欄位: {', '.join(missing_fields)}",
                }
            )

        if empty_fields:
            result["issues"].append(
                {
                    "type": "empty_fields",
                    "message": f"欄位為空: {', '.join(empty_fields)}",
                }
            )

        return result

    def check_company_name(
        self,
        title: Optional[str],
        body_html: Optional[str],
        summary: Optional[str],
        company_name: str,
    ) -> Dict[str, Any]:
        """檢查是否包含公司名稱"""
        result = {"score": 0, "issues": [], "details": {}}

        if not company_name:
            result["details"]["company_name_check"] = "skipped"
            result["score"] = 100  # 如果沒有公司名稱要求，給滿分
            return result

        # 檢查各個欄位是否包含公司名稱
        fields_with_company = []

        if title and company_name in title:
            fields_with_company.append("title")

        if body_html and company_name in body_html:
            fields_with_company.append("body_html")

        if summary and company_name in summary:
            fields_with_company.append("summary")

        result["details"]["company_name_in_fields"] = fields_with_company
        result["details"]["company_name"] = company_name

        if fields_with_company:
            result["score"] = 100
        else:
            result["issues"].append(
                {
                    "type": "missing_company_name",
                    "message": f"內容中未包含公司名稱「{company_name}」",
                }
            )

        return result

    def check_forbidden_patterns(
        self, title: Optional[str], body_html: Optional[str], summary: Optional[str]
    ) -> Dict[str, Any]:
        """檢查禁止模式"""
        result = {"score": 100, "issues": [], "details": {"forbidden_matches": []}}

        all_content = f"{title or ''} {body_html or ''} {summary or ''}"

        for pattern in self.standards.FORBIDDEN_PATTERNS:
            matches = re.findall(pattern, all_content)
            if matches:
                result["forbidden_matches"].extend(matches)
                result["score"] -= 20  # 每找到一個禁止模式扣20分
                result["issues"].append(
                    {
                        "type": "forbidden_pattern",
                        "message": f"發現禁止內容: {matches[0]}",
                    }
                )

        result["score"] = max(0, result["score"])  # 確保分數不小於0
        return result

    def check_html_format(self, body_html: Optional[str]) -> Dict[str, Any]:
        """檢查 HTML 格式"""
        result = {"score": 0, "issues": [], "details": {}}

        if not body_html:
            result["details"]["html_check"] = "skipped"
            result["score"] = 100
            return result

        # 檢查是否為有效的 HTML
        has_html_tags = bool(re.search(r"<[^>]+>", body_html))
        result["details"]["has_html_tags"] = has_html_tags

        if has_html_tags:
            # 檢查 HTML 標籤是否配對
            open_tags = re.findall(r"<(\w+)[^>]*>", body_html)
            close_tags = re.findall(r"</(\w+)>", body_html)

            result["details"]["open_tags"] = open_tags
            result["details"]["close_tags"] = close_tags

            # 簡單檢查：每個開始標籤都應該有對應的結束標籤
            unmatched_tags = []
            for tag in open_tags:
                if tag not in close_tags or open_tags.count(tag) != close_tags.count(
                    tag
                ):
                    unmatched_tags.append(tag)

            if unmatched_tags:
                result["issues"].append(
                    {
                        "type": "unmatched_html_tags",
                        "message": f"HTML 標籤未配對: {', '.join(set(unmatched_tags))}",
                    }
                )
            else:
                result["score"] += 50

            # 檢查是否使用允許的標籤
            used_tags = set(open_tags)
            disallowed_tags = used_tags - set(self.standards.ALLOWED_HTML_TAGS)

            if disallowed_tags:
                result["issues"].append(
                    {
                        "type": "disallowed_html_tags",
                        "message": f"使用了不建議的 HTML 標籤: {', '.join(disallowed_tags)}",
                    }
                )
            else:
                result["score"] += 50
        else:
            # 如果沒有 HTML 標籤，檢查是否至少有基本格式
            if body_html.strip():
                result["score"] = 80  # 有內容但沒有 HTML 格式
            else:
                result["issues"].append(
                    {"type": "empty_content", "message": "內容為空"}
                )

        return result

    def check_content_quality(
        self, title: Optional[str], body_html: Optional[str], summary: Optional[str]
    ) -> Dict[str, Any]:
        """檢查內容品質"""
        result = {"score": 0, "issues": [], "details": {}}

        # 檢查內容多樣性（簡單的字詞重複檢查）
        if body_html:
            # 移除 HTML 標籤
            text_content = re.sub(r"<[^>]+>", "", body_html)
            words = text_content.split()
            unique_words = set(words)

            diversity_ratio = len(unique_words) / len(words) if words else 0
            result["details"]["word_diversity"] = diversity_ratio

            if diversity_ratio > 0.6:
                result["score"] += 50
            elif diversity_ratio > 0.4:
                result["score"] += 30
            else:
                result["issues"].append(
                    {"type": "low_content_diversity", "message": "內容重複性較高"}
                )

        # 檢查是否有實質內容（非預設模板內容）
        template_indicators = [
            "專業的企業",
            "致力於提供優質",
            "是一家公司",
            "的企業資訊",
        ]

        all_content = f"{title or ''} {body_html or ''} {summary or ''}"
        template_matches = [
            indicator for indicator in template_indicators if indicator in all_content
        ]

        result["details"]["template_indicators"] = template_matches

        if template_matches:
            result["issues"].append(
                {
                    "type": "template_content",
                    "message": f"內容疑似使用預設模板: {', '.join(template_matches)}",
                }
            )
        else:
            result["score"] += 50

        return result

    def perform_quality_check(
        self,
        title: Optional[str],
        body_html: Optional[str],
        summary: Optional[str],
        company_name: str,
        custom_criteria: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        執行完整的品質檢查

        Args:
            title: 標題
            body_html: HTML 內容
            summary: 摘要
            company_name: 公司名稱
            custom_criteria: 自訂檢查標準

        Returns:
            品質檢查結果
        """
        import time

        start_time = time.time()

        # 執行各項檢查
        checks = {
            "length": self.check_length(title, body_html, summary),
            "required_fields": self.check_required_fields(title, body_html, summary),
            "company_name": self.check_company_name(
                title, body_html, summary, company_name
            ),
            "forbidden_patterns": self.check_forbidden_patterns(
                title, body_html, summary
            ),
            "html_format": self.check_html_format(body_html),
            "content_quality": self.check_content_quality(title, body_html, summary),
        }

        # 計算加權分數
        total_score = 0
        for check_name, check_result in checks.items():
            weight = self.standards.WEIGHTS.get(check_name, 1)
            weighted_score = check_result["score"] * weight / 100
            total_score += weighted_score

        # 收集所有問題和建議
        all_issues = []
        for check_result in checks.values():
            all_issues.extend(check_result["issues"])

        # 生成改善建議
        suggestions = self._generate_suggestions(checks, company_name)

        # 組合詳細結果
        details = {
            "individual_checks": checks,
            "weights_used": self.standards.WEIGHTS,
            "standards": {
                "min_content_length": self.standards.MIN_CONTENT_LENGTH,
                "max_content_length": self.standards.MAX_CONTENT_LENGTH,
                "required_fields": self.standards.REQUIRED_FIELDS,
                "passing_score": self.standards.PASSING_SCORE,
            },
        }

        execution_time = time.time() - start_time
        passed = total_score >= self.standards.PASSING_SCORE

        return {
            "passed": passed,
            "score": round(total_score, 2),
            "issues": all_issues,
            "suggestions": suggestions,
            "details": details,
            "execution_time": execution_time,
        }

    def _generate_suggestions(
        self, checks: Dict[str, Any], company_name: str
    ) -> List[Dict[str, str]]:
        """生成改善建議"""
        suggestions = []

        # 基於檢查結果生成建議
        if checks["length"]["issues"]:
            suggestions.append(
                {"category": "length", "suggestion": "調整內容長度以符合標準範圍"}
            )

        if checks["required_fields"]["issues"]:
            suggestions.append(
                {"category": "completeness", "suggestion": "確保所有必要欄位都有內容"}
            )

        if checks["company_name"]["issues"]:
            suggestions.append(
                {
                    "category": "company_name",
                    "suggestion": f"在標題、內容或摘要中加入公司名稱「{company_name}」",
                }
            )

        if checks["forbidden_patterns"]["issues"]:
            suggestions.append(
                {
                    "category": "content_quality",
                    "suggestion": "移除錯誤訊息或無效內容，提供更有意義的資訊",
                }
            )

        if checks["html_format"]["issues"]:
            suggestions.append(
                {
                    "category": "formatting",
                    "suggestion": "修正 HTML 格式，確保標籤正確配對",
                }
            )

        if checks["content_quality"]["issues"]:
            suggestions.append(
                {
                    "category": "quality",
                    "suggestion": "提供更多元化和具體的內容，避免使用預設模板",
                }
            )

        return suggestions


# ===== LangChain Tool 實作 =====

if LANGCHAIN_TOOLS_AVAILABLE:

    class QualityCheckTool(BaseTool):
        """品質檢查工具類別"""

        name: str = "quality_check"
        description: str = (
            "檢驗生成的公司簡介內容品質。"
            "檢查長度、必要欄位、公司名稱、禁止內容等標準。"
            "輸入格式：{'title': '標題', 'body_html': '內容', 'summary': '摘要', 'company_name': '公司名'}"
        )
        args_schema = QualityCheckInput

        def _run(
            self,
            title: Optional[str] = None,
            body_html: Optional[str] = None,
            summary: Optional[str] = None,
            company_name: str = "",
            custom_criteria: Optional[Dict[str, Any]] = None,
            run_manager: Optional[CallbackManagerForToolRun] = None,
        ) -> Dict[str, Any]:
            """執行品質檢查"""
            try:
                logger.info(f"[QualityCheckTool] 開始品質檢查，公司: {company_name}")

                # 建立品質檢查器
                checker = QualityChecker()

                # 執行檢查
                result = checker.perform_quality_check(
                    title=title,
                    body_html=body_html,
                    summary=summary,
                    company_name=company_name,
                    custom_criteria=custom_criteria,
                )

                logger.info(
                    f"[QualityCheckTool] 品質檢查完成，通過: {result['passed']}, 分數: {result['score']}"
                )

                return result

            except Exception as e:
                logger.error(f"[QualityCheckTool] 品質檢查失敗: {e}")
                return {
                    "passed": False,
                    "score": 0.0,
                    "issues": [{"type": "error", "message": str(e)}],
                    "suggestions": [
                        {"category": "error", "suggestion": "請檢查輸入格式並重試"}
                    ],
                    "details": {"error": str(e)},
                    "execution_time": 0.0,
                }


# 函式版本的 Tool
@tool
def quality_check_tool(
    title: Optional[str] = None,
    body_html: Optional[str] = None,
    summary: Optional[str] = None,
    company_name: str = "",
    custom_criteria: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    檢驗生成的公司簡介內容品質

    Args:
        title: 標題
        body_html: HTML 內容
        summary: 摘要
        company_name: 公司名稱（用於檢查是否包含）
        custom_criteria: 自訂檢查標準（可選）

    Returns:
        品質檢查結果：
        - passed: 是否通過檢查
        - score: 品質分數 (0-100)
        - issues: 發現的問題列表
        - suggestions: 改善建議列表
        - details: 詳細檢查結果
    """
    try:
        logger.info(f"[quality_check_tool] 開始品質檢查，公司: {company_name}")

        # 建立品質檢查器
        checker = QualityChecker()

        # 執行檢查
        result = checker.perform_quality_check(
            title=title,
            body_html=body_html,
            summary=summary,
            company_name=company_name,
            custom_criteria=custom_criteria,
        )

        logger.info(
            f"[quality_check_tool] 品質檢查完成，通過: {result['passed']}, 分數: {result['score']}"
        )

        return result

    except Exception as e:
        logger.error(f"[quality_check_tool] 品質檢查失敗: {e}")
        return {
            "passed": False,
            "score": 0.0,
            "issues": [{"type": "error", "message": str(e)}],
            "suggestions": [
                {"category": "error", "suggestion": "請檢查輸入格式並重試"}
            ],
            "details": {"error": str(e)},
            "execution_time": 0.0,
        }


# ===== 便捷函式 =====


def create_quality_check_tool():
    """建立品質檢查工具實例"""
    if LANGCHAIN_TOOLS_AVAILABLE:
        return QualityCheckTool()
    else:
        return quality_check_tool


def quick_quality_check(
    llm_result: Dict[str, Any], company_name: str
) -> Dict[str, Any]:
    """
    快速品質檢查（便捷函式）

    Args:
        llm_result: LLM 生成結果（包含 title, body_html, summary）
        company_name: 公司名稱

    Returns:
        品質檢查結果
    """
    return quality_check_tool(
        title=llm_result.get("title"),
        body_html=llm_result.get("body_html"),
        summary=llm_result.get("summary"),
        company_name=company_name,
    )


def get_quality_standards() -> Dict[str, Any]:
    """取得目前的品質標準"""
    standards = QualityStandards()
    return {
        "length_limits": {
            "title": {
                "min": standards.MIN_TITLE_LENGTH,
                "max": standards.MAX_TITLE_LENGTH,
            },
            "content": {
                "min": standards.MIN_CONTENT_LENGTH,
                "max": standards.MAX_CONTENT_LENGTH,
            },
            "summary": {
                "min": standards.MIN_SUMMARY_LENGTH,
                "max": standards.MAX_SUMMARY_LENGTH,
            },
        },
        "required_fields": standards.REQUIRED_FIELDS,
        "forbidden_patterns": standards.FORBIDDEN_PATTERNS,
        "allowed_html_tags": standards.ALLOWED_HTML_TAGS,
        "weights": standards.WEIGHTS,
        "passing_score": standards.PASSING_SCORE,
    }
