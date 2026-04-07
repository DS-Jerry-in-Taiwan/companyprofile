#!/usr/bin/env python3
"""
Phase 9 LangGraph Integration Demonstration
展示完整的 LangGraph 整合功能
"""

import sys
import os
import logging

# 設定路徑
sys.path.insert(0, "/home/ubuntu/projects/OrganBriefOptimization")

# 設定日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def demo_company_brief_generation():
    """展示公司簡介生成功能"""

    print("=" * 60)
    print("🚀 Phase 9 LangGraph Integration 功能展示")
    print("=" * 60)

    # 測試案例
    test_cases = [
        {
            "name": "完整資料案例",
            "data": {
                "organ": "微軟",
                "organNo": "98765432",
                "companyUrl": "https://www.microsoft.com",
                "brief": "全球領先的軟體和雲端服務公司",
            },
        },
        {
            "name": "最小資料案例",
            "data": {
                "organ": "創新科技",
            },
        },
        {
            "name": "有統編但無網址",
            "data": {
                "organ": "綠能公司",
                "organNo": "11223344",
                "brief": "專注於綠色能源解決方案",
            },
        },
    ]

    try:
        from src.functions.utils.generate_brief import generate_brief

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 測試案例 {i}: {test_case['name']}")
            print(f"輸入資料: {test_case['data']}")
            print("-" * 40)

            # 生成簡介
            result = generate_brief(test_case["data"])

            # 顯示結果
            print(f"✅ 生成成功!")
            print(f"🔄 處理模式: {result.get('processing_mode', 'unknown')}")
            print(f"📊 品質分數: {result.get('quality_score', 'N/A')}")
            print(f"🔍 搜尋來源: {result.get('search_source', 'N/A')}")
            print(f"⚠️  品質警告: {result.get('quality_warning', False)}")
            print(f"❌ 錯誤處理: {result.get('error_handled', False)}")

            print(f"\n📋 生成內容:")
            print(f"標題: {result.get('title', 'N/A')}")
            print(f"摘要: {result.get('summary', 'N/A')}")

            # 顯示內容長度
            body_html = result.get("body_html", "")
            if body_html:
                print(f"內容長度: {len(body_html)} 字元")
                # 顯示內容預覽（前 100 字元）
                preview = body_html[:100].replace("<p>", "").replace("</p>", "").strip()
                print(f"內容預覽: {preview}{'...' if len(body_html) > 100 else ''}")

            print("-" * 40)

    except Exception as e:
        print(f"❌ 測試失敗: {e}")


def demo_langgraph_features():
    """展示 LangGraph 特色功能"""

    print(f"\n🔧 LangGraph 特色功能展示")
    print("=" * 40)

    try:
        from src.langgraph.company_brief_graph import create_company_brief_graph

        # 創建狀態圖實例
        graph = create_company_brief_graph()

        print("✅ LangGraph 狀態圖創建成功")

        # 測試狀態圖功能
        test_data = {
            "organ": "AI 科技公司",
            "organNo": "55667788",
            "brief": "專注人工智慧技術研發",
        }

        print(f"\n🧪 測試狀態圖執行...")
        print(f"測試資料: {test_data}")

        # 執行狀態圖
        result = graph.invoke(
            organ=test_data["organ"],
            organ_no=test_data.get("organNo"),
            user_brief=test_data.get("brief"),
        )

        print(f"\n✅ 狀態圖執行成功!")
        print(f"結果類型: {type(result)}")
        print(
            f"結果鍵值: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}"
        )

        if isinstance(result, dict):
            print(f"標題: {result.get('title', 'N/A')}")
            print(f"品質分數: {result.get('quality_score', 'N/A')}")
            print(f"搜尋來源: {result.get('search_source', 'N/A')}")

    except ImportError as e:
        print(f"❌ LangGraph 不可用: {e}")
    except Exception as e:
        print(f"❌ LangGraph 測試失敗: {e}")


def demo_langchain_tools():
    """展示 LangChain Tools 功能"""

    print(f"\n🛠️ LangChain Tools 功能展示")
    print("=" * 40)

    try:
        from src.langchain.tools import get_available_tools, tool_manager

        # 取得可用工具
        tools = get_available_tools()
        print(f"✅ 可用工具數量: {len(tools)}")

        # 顯示工具分類
        categories = ["search", "llm"]
        for category in categories:
            category_tools = tool_manager.get_tools_by_category(category)
            print(f"\n📂 {category.upper()} 類別工具 ({len(category_tools)} 個):")

            for tool_name, tool_func in category_tools.items():
                description = tool_manager.descriptions.get(tool_name, "無描述")
                print(f"  - {tool_name}: {description}")

        # 測試工具管理器功能
        print(f"\n🔧 工具管理器功能測試:")
        try:
            # 測試取得特定工具
            tavily_tool = tool_manager.get_tool("tavily_search")
            print(f"✅ 成功取得 tavily_search 工具: {type(tavily_tool)}")

            # 測試工具列表功能
            search_tools_list = tool_manager.list_tools("search")
            print(f"✅ 搜尋類工具列表: {len(search_tools_list)} 項")

        except Exception as e:
            print(f"❌ 工具管理器測試失敗: {e}")

    except ImportError as e:
        print(f"❌ LangChain Tools 不可用: {e}")
    except Exception as e:
        print(f"❌ LangChain Tools 測試失敗: {e}")


def demo_error_handling():
    """展示錯誤處理和重試機制"""

    print(f"\n⚠️ 錯誤處理機制展示")
    print("=" * 40)

    try:
        from src.langchain.error_handlers import RunnableWithRetryAndFallbacks
        from src.langchain.retry_config import get_retry_config

        # 顯示重試配置
        config = get_retry_config()
        print(f"✅ 重試配置:")
        print(f"  - 最大重試次數: {config.get('max_retries', 'N/A')}")
        print(f"  - 重試延遲: {config.get('retry_delay', 'N/A')} 秒")
        print(f"  - 退避倍數: {config.get('backoff_multiplier', 'N/A')}")

        # 測試錯誤處理包裝器
        print(f"\n🔧 錯誤處理包裝器測試:")

        def test_function():
            return {"result": "success", "message": "測試成功"}

        # 包裝函式
        wrapped_function = RunnableWithRetryAndFallbacks(
            primary=test_function, operation_name="test_operation"
        )

        # 執行測試
        result = wrapped_function()
        print(f"✅ 包裝器執行成功: {result}")

    except ImportError as e:
        print(f"❌ 錯誤處理模組不可用: {e}")
    except Exception as e:
        print(f"❌ 錯誤處理測試失敗: {e}")


def main():
    """主展示函式"""

    print("🎯 Phase 9 LangChain/LangGraph Integration")
    print("完整功能展示開始...")

    # 1. 公司簡介生成展示
    demo_company_brief_generation()

    # 2. LangGraph 功能展示
    demo_langgraph_features()

    # 3. LangChain Tools 展示
    demo_langchain_tools()

    # 4. 錯誤處理機制展示
    demo_error_handling()

    print("\n" + "=" * 60)
    print("🎉 Phase 9 整合展示完成！")
    print("=" * 60)

    # 總結
    print("\n📊 Phase 9 主要成就:")
    print("✅ LangGraph 狀態圖整合 - 統一流程控制")
    print("✅ LangChain 錯誤處理 - 穩定重試和 Fallback")
    print("✅ Tool 包裝和管理 - 模組化工具架構")
    print("✅ 品質檢查機制 - 多維度評分和改善建議")
    print("✅ 向後相容性 - 與現有 API 無縫整合")
    print("✅ 動態路由 - 根據執行狀況智慧決策")

    print("\n🔮 技術特色:")
    print("🔄 自動重試和錯誤恢復")
    print("📊 即時品質評分和監控")
    print("🎛️ 彈性的處理模式選擇")
    print("🧩 模組化的 Tool 架構")
    print("🔍 詳細的執行追蹤和日誌")


if __name__ == "__main__":
    main()
