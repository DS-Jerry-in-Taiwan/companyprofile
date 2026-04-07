#!/usr/bin/env python3
"""
Phase 9 LangGraph 整合測試
測試新的狀態圖整合是否正常運作
"""

import sys
import os
import logging

# 設定路徑
sys.path.insert(0, "/home/ubuntu/projects/OrganBriefOptimization")

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_langgraph_availability():
    """測試 LangGraph 模組是否可用"""
    try:
        from src.langgraph.company_brief_graph import (
            generate_company_brief,
            create_company_brief_graph,
        )

        logger.info("✅ LangGraph 模組可用")
        return True
    except ImportError as e:
        logger.warning(f"❌ LangGraph 模組不可用: {e}")
        return False


def test_langchain_tools_availability():
    """測試 LangChain Tools 是否可用"""
    try:
        from src.langchain.tools import get_available_tools

        tools = get_available_tools()
        logger.info(f"✅ LangChain Tools 可用，共 {len(tools)} 個工具")
        for tool_info in tools:
            tool_name = (
                tool_info.get("name", "Unknown")
                if isinstance(tool_info, dict)
                else str(tool_info)
            )
            tool_desc = (
                tool_info.get("description", "No description")
                if isinstance(tool_info, dict)
                else "No description"
            )
            logger.info(f"  - {tool_name}: {tool_desc}")
        return True
    except ImportError as e:
        logger.warning(f"❌ LangChain Tools 不可用: {e}")
        return False


def test_generate_brief_integration():
    """測試 generate_brief 整合"""
    try:
        from src.functions.utils.generate_brief import generate_brief

        # 測試資料
        test_data = {
            "organ": "台積電",
            "organNo": "12345678",
            "brief": "半導體製造公司",
        }

        logger.info("🧪 測試 generate_brief 整合...")
        result = generate_brief(test_data)

        # 檢查結果格式
        required_fields = ["title", "body_html", "summary"]
        for field in required_fields:
            if field not in result:
                logger.error(f"❌ 缺少必要欄位: {field}")
                return False

        # 檢查處理模式
        processing_mode = result.get("processing_mode", "unknown")
        logger.info(f"✅ generate_brief 整合成功，處理模式: {processing_mode}")
        logger.info(f"  - 標題: {result['title']}")
        logger.info(f"  - 品質分數: {result.get('quality_score', 'N/A')}")

        return True

    except Exception as e:
        logger.error(f"❌ generate_brief 整合測試失敗: {e}")
        return False


def test_state_graph_simulation():
    """測試狀態圖模擬模式"""
    try:
        from src.langgraph.company_brief_graph import CompanyBriefGraph

        logger.info("🧪 測試狀態圖模擬執行...")
        graph = CompanyBriefGraph()

        # 測試資料
        result = graph.invoke("測試公司", "12345678", None, "測試簡介")

        if result and isinstance(result, dict):
            logger.info("✅ 狀態圖模擬執行成功")
            logger.info(f"  - 模擬模式: {result.get('simulation_mode', False)}")
            return True
        else:
            logger.error("❌ 狀態圖模擬執行失敗，無效結果")
            return False

    except Exception as e:
        logger.error(f"❌ 狀態圖模擬執行失敗: {e}")
        return False


def main():
    """主測試函式"""
    logger.info("🚀 開始 Phase 9 LangGraph 整合測試")

    tests = [
        ("LangGraph 模組可用性", test_langgraph_availability),
        ("LangChain Tools 可用性", test_langchain_tools_availability),
        ("generate_brief 整合", test_generate_brief_integration),
        ("狀態圖模擬執行", test_state_graph_simulation),
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- 測試: {test_name} ---")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"測試 {test_name} 發生異常: {e}")
            results.append((test_name, False))

    # 總結
    logger.info("\n" + "=" * 50)
    logger.info("📊 測試結果總結:")
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"  {status} - {test_name}")
        if success:
            passed += 1

    total = len(results)
    logger.info(f"\n🎯 總計: {passed}/{total} 項測試通過")

    if passed == total:
        logger.info("🎉 所有測試通過！Phase 9 LangGraph 整合成功")
    else:
        logger.warning(f"⚠️  有 {total - passed} 項測試失敗，需要檢查")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
