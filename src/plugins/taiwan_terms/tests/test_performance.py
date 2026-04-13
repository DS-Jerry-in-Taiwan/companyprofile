"""
效能測試與 Lambda 相容性驗證

此測試驗證：
1. 轉換器在 AWS Lambda 環境下的效能表現
2. 冷啟動時間（詞庫載入時間）
3. 熱啟動效能（詞庫已載入）
4. 記憶體使用情況
5. 處理時間是否符合目標（<50ms）
"""

import os
import sys
import time
import json
import random
import statistics
import psutil
import gc
from typing import List, Dict, Tuple

# 添加模組路徑
module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, module_dir)

# 添加父目錄到路徑
parent_dir = os.path.dirname(module_dir)
sys.path.insert(0, parent_dir)

try:
    from taiwan_terms import TaiwanTermsConverter, ConvertOptions
    from taiwan_terms.loader import TermsLoader
except ImportError:
    # 嘗試直接導入
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "taiwan_terms", os.path.join(module_dir, "__init__.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    TaiwanTermsConverter = module.TaiwanTermsConverter
    ConvertOptions = module.ConvertOptions

    # 載入 loader
    loader_spec = importlib.util.spec_from_file_location(
        "loader", os.path.join(module_dir, "loader.py")
    )
    loader_module = importlib.util.module_from_spec(loader_spec)
    loader_spec.loader.exec_module(loader_module)
    TermsLoader = loader_module.TermsLoader


def generate_test_texts(num_texts: int = 100, avg_length: int = 500) -> List[str]:
    """
    生成測試文字

    Args:
        num_texts: 文字數量
        avg_length: 平均長度（字符）

    Returns:
        測試文字列表
    """
    # 常見的中國用語（來自詞庫）
    china_terms = [
        "软件",
        "网络",
        "服务器",
        "硬盘",
        "内存",
        "文件",
        "文件夹",
        "登录",
        "注册",
        "上传",
        "下载",
        "打印",
        "鼠标",
        "键盘",
        "显示器",
        "笔记本",
        "计算机",
        "程序员",
        "编码",
        "编程",
        "开源",
        "兼容",
        "配置",
        "性能",
        "优化",
        "算法",
        "接口",
        "端口",
        "总线",
        "芯片",
        "半导体",
        "视频",
        "音频",
        "图像",
        "像素",
        "分辨率",
        "质量",
        "运营",
        "客户",
        "信息",
        "数据",
        "账户",
        "微博",
        "博客",
        "视频",
        "音频",
        "网络",
        "互联网",
    ]

    # 常見句子模板
    templates = [
        "我們的{term}產品在市場上表現出色。",
        "通過{term}技術，我們能夠提供更好的服務。",
        "這個{term}系統非常穩定可靠。",
        "我們專注於{term}開發和優化。",
        "最新的{term}更新帶來了顯著的改進。",
        "使用我們的{term}解決方案可以提高效率。",
        "我們在{term}領域擁有豐富的經驗。",
        "這個{term}平台支援多種應用場景。",
        "我們的{term}服務已經獲得廣泛認可。",
        "通過整合{term}，我們實現了無縫連接。",
    ]

    test_texts = []

    for _ in range(num_texts):
        # 隨機選擇幾個詞彙
        selected_terms = random.sample(china_terms, random.randint(3, 8))

        # 建立文字
        text_parts = []
        for term in selected_terms:
            template = random.choice(templates)
            text_parts.append(template.format(term=term))

        # 合併文字
        full_text = " ".join(text_parts)

        # 確保文字長度接近目標
        if len(full_text) < avg_length:
            # 添加額外內容
            extra_terms = random.sample(china_terms, random.randint(2, 5))
            extra_text = " ".join(
                [f"此外，我們還提供{term}服務。" for term in extra_terms]
            )
            full_text += " " + extra_text

        # 限制長度
        if len(full_text) > avg_length * 1.5:
            full_text = full_text[: avg_length * 1.5]

        test_texts.append(full_text)

    return test_texts


def measure_memory_usage() -> Tuple[float, float]:
    """
    測量記憶體使用情況

    Returns:
        (process_memory_mb, python_memory_mb)
    """
    process = psutil.Process(os.getpid())

    # 程序記憶體使用（MB）
    process_memory = process.memory_info().rss / 1024 / 1024

    # Python 物件記憶體（粗略估計）
    gc.collect()
    python_memory = (
        sum(sys.getsizeof(obj) for obj in gc.get_objects() if not isinstance(obj, type))
        / 1024
        / 1024
    )

    return process_memory, python_memory


def test_cold_start() -> Dict[str, float]:
    """
    測試冷啟動（初次載入詞庫）

    Returns:
        統計資訊字典
    """
    print("=== 冷啟動測試 ===")

    # 清除可能存在的快取
    from taiwan_terms.loader import TermsLoader

    loader = TermsLoader.get_instance()
    loader.clear_cache()

    # 強制垃圾回收
    gc.collect()

    # 記錄初始記憶體
    start_memory = measure_memory_usage()

    # 建立轉換器（會觸發詞庫載入）
    start_time = time.time()
    converter = TaiwanTermsConverter(
        ConvertOptions(enable_opencc=True, enable_term_mapping=True, lazy_load=True)
    )

    # 載入詞庫
    converter._loader.load_terms()

    cold_start_time = (time.time() - start_time) * 1000  # 毫秒

    # 記錄結束記憶體
    end_memory = measure_memory_usage()

    # 統計資訊
    stats = {
        "cold_start_time_ms": cold_start_time,
        "process_memory_before_mb": start_memory[0],
        "process_memory_after_mb": end_memory[0],
        "python_memory_before_mb": start_memory[1],
        "python_memory_after_mb": end_memory[1],
        "memory_increase_mb": end_memory[0] - start_memory[0],
        "terms_loaded": converter.get_stats()["terms_loaded"],
    }

    print(f"冷啟動時間: {cold_start_time:.2f}ms")
    print(f"詞庫載入數量: {stats['terms_loaded']}")
    print(f"記憶體增加: {stats['memory_increase_mb']:.2f}MB")
    print(f"處理程序記憶體: {end_memory[0]:.2f}MB")

    # 驗證冷啟動時間符合目標 (<300ms)
    assert cold_start_time < 300, f"冷啟動時間 {cold_start_time:.2f}ms 超過 300ms 目標"

    # 驗證記憶體使用符合目標 (<128MB)
    assert end_memory[0] < 128, f"記憶體使用 {end_memory[0]:.2f}MB 超過 128MB 目標"

    # 驗證詞庫載入成功
    assert stats["terms_loaded"] > 0, "詞庫載入失敗"

    # 返回統計資訊（測試通過）
    return stats


def test_hot_performance() -> Dict[str, float]:
    """
    測試熱啟動效能（詞庫已載入）

    Returns:
        統計資訊字典
    """
    print("\n=== 熱啟動效能測試 ===")

    # 建立轉換器
    converter = TaiwanTermsConverter(
        ConvertOptions(enable_opencc=True, enable_term_mapping=True, collect_stats=True)
    )

    # 建立測試文字
    test_texts = [
        "今天天氣很好，我們使用U盤來存儲數據。",
        "請將文件上傳到雲盤，然後用微信掃碼分享。",
        "這個軟件支持多線程，優化了算法效率。",
        "服務器部署在阿里雲，數據庫用的是MySQL。",
        "公司的現金流很好，投資回報率很高。",
        "需要優化用戶體驗，提高產品質量。",
        "這個項目使用了人工智能技術。",
        "請確保代碼質量，做好單元測試。",
        "視頻會議需要穩定的網絡連接。",
        "公司的微博賬號有很多粉絲。",
    ]

    # 確保詞庫已載入
    if not converter._loader.is_loaded():
        converter._loader.load_terms()

    # 記憶體基準
    gc.collect()
    start_memory = measure_memory_usage()

    # 批次轉換測試
    batch_sizes = [1, 5, 10, 20]
    results = {}

    for batch_size in batch_sizes:
        print(f"\n測試批次大小: {batch_size}")

        # 隨機選擇測試文字
        selected_texts = random.sample(test_texts, min(batch_size, len(test_texts)))

        # 多次測試取平均
        iterations = max(10, 100 // batch_size)  # 總處理文字數約 100
        times = []

        for i in range(iterations):
            start_time = time.time()

            # 單次轉換或批次轉換
            if batch_size == 1:
                result = converter.convert(selected_texts[0])
                times.append(result.stats.total_time_ms)
            else:
                results_list = converter.batch_convert(selected_texts)
                # 計算平均時間
                avg_time = sum(r.stats.total_time_ms for r in results_list) / len(
                    results_list
                )
                times.append(avg_time)

            # 每 10 次輸出進度
            if (i + 1) % 10 == 0:
                print(f"  已完成 {i + 1}/{iterations} 次迭代")

        # 統計
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0

        results[f"batch_{batch_size}"] = {
            "avg_time_ms": avg_time,
            "min_time_ms": min_time,
            "max_time_ms": max_time,
            "std_dev_ms": std_dev,
            "iterations": iterations,
        }

        print(f"  平均時間: {avg_time:.2f}ms")
        print(f"  最小時間: {min_time:.2f}ms")
        print(f"  最大時間: {max_time:.2f}ms")
        print(f"  標準差: {std_dev:.2f}ms")

    # 結束記憶體
    gc.collect()
    end_memory = measure_memory_usage()

    # 綜合統計
    overall_stats = {
        "batch_results": results,
        "process_memory_mb": end_memory[0],
        "python_memory_mb": end_memory[1],
        "memory_increase_mb": end_memory[0] - start_memory[0],
    }

    # 驗證效能目標
    single_batch_time = results.get("batch_1", {}).get("avg_time_ms", 0)
    if single_batch_time > 0:
        assert single_batch_time < 50, (
            f"單次轉換時間 {single_batch_time:.2f}ms 超過 50ms 目標"
        )

    # 驗證記憶體使用
    assert end_memory[0] < 128, f"記憶體使用 {end_memory[0]:.2f}MB 超過 128MB 目標"

    return overall_stats


def test_lambda_compatibility():
    """
    測試 Lambda 相容性
    驗證是否滿足 Lambda 限制：
    1. 部署包大小（間接驗證）
    2. 冷啟動時間 < 300ms（目標）
    3. 熱啟動處理時間 < 50ms（目標）
    4. 記憶體使用 < 128MB（推薦）
    """
    print("\n=== Lambda 相容性測試 ===")

    # 生成測試文字
    print("生成測試文字...")
    test_texts = generate_test_texts(num_texts=50, avg_length=300)

    # 測試冷啟動
    cold_stats = test_cold_start()

    # 建立轉換器（熱啟動）
    converter = TaiwanTermsConverter()

    # 測試熱啟動效能
    hot_stats = test_hot_performance()

    # 檢查 Lambda 限制
    print("\n=== Lambda 限制檢查 ===")

    # 1. 冷啟動時間檢查
    cold_start_time = cold_stats["cold_start_time_ms"]
    if cold_start_time < 300:
        print(f"✓ 冷啟動時間: {cold_start_time:.2f}ms < 300ms (符合)")
    else:
        print(f"✗ 冷啟動時間: {cold_start_time:.2f}ms >= 300ms (警告)")

    # 2. 熱啟動處理時間檢查（單次轉換）
    single_batch = hot_stats["batch_results"]["batch_1"]
    avg_single_time = single_batch["avg_time_ms"]

    if avg_single_time < 50:
        print(f"✓ 單次轉換時間: {avg_single_time:.2f}ms < 50ms (符合)")
    else:
        print(f"✗ 單次轉換時間: {avg_single_time:.2f}ms >= 50ms (警告)")

    # 3. 記憶體使用檢查
    process_memory = cold_stats["process_memory_after_mb"]
    if process_memory < 128:
        print(f"✓ 記憶體使用: {process_memory:.2f}MB < 128MB (符合)")
    elif process_memory < 256:
        print(f"⚠ 記憶體使用: {process_memory:.2f}MB < 256MB (可接受)")
    else:
        print(f"✗ 記憶體使用: {process_memory:.2f}MB >= 256MB (警告)")

    # 4. 詞庫載入檢查
    terms_loaded = cold_stats["terms_loaded"]
    print(f"✓ 詞庫載入數量: {terms_loaded} 條")

    # 綜合評估
    print("\n=== 綜合評估 ===")

    passes = 0
    total = 3  # 冷啟動、熱啟動、記憶體

    if cold_start_time < 300:
        passes += 1
    if avg_single_time < 50:
        passes += 1
    if process_memory < 256:  # 256MB 是可接受的上限
        passes += 1

    if passes == total:
        print("✅ 所有 Lambda 相容性檢查通過！")
    elif passes >= total * 0.7:
        print("⚠ Lambda 相容性檢查部分通過（可接受）")
    else:
        print("❌ Lambda 相容性檢查未通過")

    # 主要 assert 檢查
    assert cold_start_time < 300, f"冷啟動時間 {cold_start_time:.2f}ms 超過 300ms 目標"
    assert avg_single_time < 50, f"單次轉換時間 {avg_single_time:.2f}ms 超過 50ms 目標"
    assert process_memory < 256, (
        f"記憶體使用 {process_memory:.2f}MB 超過 256MB 可接受上限"
    )

    # 嚴格目標檢查
    assert process_memory < 128, (
        f"記憶體使用 {process_memory:.2f}MB 超過 128MB 理想目標"
    )

    # 返回詳細結果
    return {
        "cold_start": cold_stats,
        "hot_performance": hot_stats,
        "lambda_compliance": {
            "cold_start_passed": cold_start_time < 300,
            "hot_performance_passed": avg_single_time < 50,
            "memory_passed": process_memory < 256,
            "overall_passed": passes == total,
        },
    }


def test_edge_cases():
    """
    測試邊界情況
    """
    print("\n=== 邊界情況測試 ===")

    converter = TaiwanTermsConverter()

    test_cases = [
        ("", "空字串"),
        (" " * 100, "空白字串"),
        ("abcdefg12345!@#$%", "純英文和符號"),
        ("<p>這是一個段落</p>", "簡單 HTML"),
        ("軟件和软件同時存在", "混合詞彙"),
        (
            "這是一個很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長的句子",
            "超長句子",
        ),
    ]

    for text, description in test_cases:
        print(f"\n測試: {description}")
        print(f"輸入: {text[:50]}{'...' if len(text) > 50 else ''}")

        result = converter.convert(text)

        if result.success():
            print(f"結果: 成功轉換 ({result.stats.total_time_ms:.2f}ms)")
            if result.stats.terms_replaced > 0:
                print(f"替換詞彙: {result.stats.terms_replaced} 個")
        else:
            print(f"結果: 失敗 - {result.error}")


def main():
    """主測試函數"""
    print("台灣用語轉換器效能測試")
    print("=" * 50)

    try:
        # 測試 Lambda 相容性
        lambda_results = test_lambda_compatibility()

        # 測試邊界情況
        test_edge_cases()

        # 儲存結果
        output_file = "performance_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(lambda_results, f, indent=2, ensure_ascii=False)

        print(f"\n詳細結果已儲存至: {output_file}")

        return 0

    except Exception as e:
        print(f"測試過程中發生錯誤: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
