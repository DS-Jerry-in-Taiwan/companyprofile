# tests/test_search_formatting.py
"""
搜尋格式化測試

驗證搜尋工具返回正確的結構化格式，以及 summary_node 能正確合併結構化資料。
"""

import pytest
import sys
import os

# 確保專案根目錄在路徑中
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.services.search_tools import create_search_tool, SearchResult
from src.langgraph_state.company_brief_graph import summary_node
from src.langgraph_state.state import create_initial_state


class TestSearchFormatting:
    """搜尋格式化測試"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每個測試前的準備"""
        # 檢查必要的 API key
        from dotenv import load_dotenv
        load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

    def test_gemini_fewshot_returns_structured_format(self):
        """驗證 gemini_fewshot 返回結構化格式"""
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key or gemini_key == "dummy_value":
            pytest.skip("GEMINI_API_KEY not configured")

        tool = create_search_tool('gemini_fewshot')
        result = tool.search('Google')

        assert result.success, f"Search failed: {result.raw_answer[:200]}"
        # 檢查是否包含預期的面向
        assert any(k in result.data for k in ['foundation', 'core', 'vibe', 'future']), \
            f"Expected structured format keys, got: {list(result.data.keys())}"
        print(f'✅ gemini_fewshot 返回結構化格式: {list(result.data.keys())}')

    def test_gemini_planner_tavily_returns_structured_format(self):
        """驗證 gemini_planner_tavily 返回結構化格式"""
        gemini_key = os.getenv("GEMINI_API_KEY")
        tavily_key = os.getenv("TAVILY_API_KEY")

        if not gemini_key or gemini_key == "dummy_value":
            pytest.skip("GEMINI_API_KEY not configured")
        if not tavily_key or tavily_key == "dummy_value":
            pytest.skip("TAVILY_API_KEY not configured")

        tool = create_search_tool('gemini_planner_tavily')
        result = tool.search('Apple')

        assert result.success, f"Search failed: {result.raw_answer[:200]}"
        assert result.api_calls > 1, f"Expected multiple API calls, got {result.api_calls}"
        print(f'✅ gemini_planner_tavily 返回結構化格式，API calls: {result.api_calls}')

    def test_summary_node_merges_structured_results(self):
        """驗證 summary_node 能正確合併結構化資料"""
        # 建立結構化搜尋結果（使用 state.py 的 SearchResult 格式）
        from src.langgraph_state.state import SearchResult as StateSearchResult

        search_result = StateSearchResult(
            success=True,
            answer="",
            results=[
                {'aspect': 'foundation', 'content': '成立於2015年', 'success': True},
                {'aspect': 'foundation', 'content': '資本額5000萬', 'success': True},
                {'aspect': 'core', 'content': '主要產品是雲端服務', 'success': True},
                {'aspect': 'vibe', 'content': '開放的企業文化', 'success': True},
                {'aspect': 'future', 'content': '積極擴展國際市場', 'success': True},
            ],
            source="test",
            execution_time=1.0
        )

        # 建立初始狀態
        state = create_initial_state(organ='測試公司')
        state['search_result'] = search_result

        # 執行 summary_node
        result_state = summary_node(state)

        # 驗證 aspect_summaries 存在且有內容
        assert 'aspect_summaries' in result_state, "aspect_summaries not in result_state"
        assert result_state['aspect_summaries'] is not None, "aspect_summaries is None"
        assert 'foundation' in result_state['aspect_summaries'], "foundation not in aspect_summaries"
        assert 'core' in result_state['aspect_summaries'], "core not in aspect_summaries"
        assert 'vibe' in result_state['aspect_summaries'], "vibe not in aspect_summaries"
        assert 'future' in result_state['aspect_summaries'], "future not in aspect_summaries"

        # 驗證 foundation 合併了兩個結果
        foundation_content = result_state['aspect_summaries']['foundation'].content
        assert '成立於2015年' in foundation_content or '資本額5000萬' in foundation_content, \
            f"foundation content not properly merged: {foundation_content}"

        print(f'✅ summary_node 正確合併結構化資料')
        print(f'   foundation: {result_state["aspect_summaries"]["foundation"].content[:50]}...')

    def test_tavily_search_basic(self):
        """驗證 tavily 搜尋基本功能"""
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key or tavily_key == "dummy_value":
            pytest.skip("TAVILY_API_KEY not configured")

        tool = create_search_tool('tavily')
        result = tool.search('Taiwan semiconductor')

        assert result.success, f"Search failed"
        assert result.api_calls == 1, f"Expected 1 API call, got {result.api_calls}"
        print(f'✅ tavily 搜尋成功')


class TestSearchToolFactory:
    """搜尋工具工廠測試"""

    def test_create_search_tool_with_string(self):
        """測試使用字串建立搜尋工具"""
        tool = create_search_tool('tavily')
        assert tool is not None
        assert hasattr(tool, 'search')
        print('✅ create_search_tool 支援字串參數')

    def test_list_available_tools(self):
        """測試列出可用工具"""
        from src.services.search_tools import SearchToolFactory
        tools = SearchToolFactory.list_tools()
        assert 'tavily' in tools
        assert 'gemini_fewshot' in tools
        print(f'✅ 可用工具列表: {tools}')


class TestEndToEnd:
    """端到端流程測試"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每個測試前的準備"""
        from dotenv import load_dotenv
        load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

    def test_structured_search_to_summary_flow(self):
        """測試結構化搜尋到摘要的完整流程"""
        from src.langgraph_state.state import SearchResult as StateSearchResult

        # Step 1: 模擬搜尋結果
        search_result = StateSearchResult(
            success=True,
            answer="",
            results=[
                {'aspect': 'foundation', 'content': '公司成立於1998年，專注於科技創新', 'success': True},
                {'aspect': 'foundation', 'content': '總部位於台北，员工超过500人', 'success': True},
                {'aspect': 'core', 'content': '核心產品包括AI解決方案和雲端平台', 'success': True},
                {'aspect': 'vibe', 'content': '強調創新和開放的企業文化', 'success': True},
                {'aspect': 'future', 'content': '2024年將擴展至東南亞市場', 'success': True},
            ],
            source="gemini_fewshot",
            execution_time=2.5
        )

        # Step 2: 建立狀態
        state = create_initial_state(organ='測試科技公司')
        state['search_result'] = search_result

        # Step 3: 執行摘要節點
        result_state = summary_node(state)

        # Step 4: 驗證結果
        assert result_state['aspect_summaries'] is not None
        assert len(result_state['aspect_summaries']) == 4  # 四個面向

        # 驗證每個面向都有內容
        for aspect in ['foundation', 'core', 'vibe', 'future']:
            assert aspect in result_state['aspect_summaries']
            summary = result_state['aspect_summaries'][aspect]
            assert summary.aspect == aspect
            assert len(summary.content) > 0, f"{aspect} should have content"
            assert summary.source_queries >= 1, f"{aspect} should have at least 1 source"

        print('✅ 端到端流程測試通過')
        print(f'   - 處理了 {len(search_result.results)} 個搜尋結果')
        print(f'   - 產出了 {len(result_state["aspect_summaries"])} 個面向摘要')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
