"""
平行搜尋速度比較器
===================

比較 Tavily 與 Gemini Flash Lite 的平行搜尋速度
並整合彙整、簡介生成、標籤生成流程
"""

import os
import sys
import json
import time
import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# 取得專案根目錄
_CURRENT_FILE = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_FILE)))
)
sys.path.insert(0, PROJECT_ROOT)

# 匯入新增的模組
from summarizer import FourAspectSummarizer
from brief_generator import BriefGenerator, BriefLength
from tag_generator import TagGenerator
from evaluator import ContentEvaluator


@dataclass
class QueryResult:
    """單一查詢結果"""

    query: str
    aspect: str
    success: bool
    elapsed_time: float
    answer: str
    error: str = ""


@dataclass
class ProviderResult:
    """單一提供者結果"""

    provider: str
    total_time: float
    query_results: List[QueryResult]
    success_count: int
    failure_count: int


class ParallelComparisonRunner:
    """平行搜尋速度比較器"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "test_queries.json"
            )

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.aspects = self.config["aspects"]
        self.companies = self.config["companies"]

    def generate_queries(self, company: str) -> List[Dict[str, str]]:
        """根據公司名稱生成查詢"""
        queries = []

        for aspect, aspect_config in self.aspects.items():
            for query_template in aspect_config["queries"]:
                query = query_template.replace("{company}", company)
                queries.append(
                    {
                        "aspect": aspect,
                        "query": query,
                    }
                )

        return queries

    async def run_tavily(self, queries: List[Dict[str, str]]) -> ProviderResult:
        """執行 Tavily 平行搜尋"""
        from providers.tavily_search import tavily_search

        print(f"\n🔍 Tavily 平行搜尋（{len(queries)} 個查詢）...")

        start = time.time()

        # 並行執行
        tasks = [tavily_search(q["query"]) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start

        # 組裝結果
        query_results = []
        success_count = 0
        failure_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                query_results.append(
                    QueryResult(
                        query=queries[i]["query"],
                        aspect=queries[i]["aspect"],
                        success=False,
                        elapsed_time=0,
                        answer="",
                        error=str(result),
                    )
                )
                failure_count += 1
            else:
                # SearchResult 屬性存取
                query_results.append(
                    QueryResult(
                        query=queries[i]["query"],
                        aspect=queries[i]["aspect"],
                        success=result.success,
                        elapsed_time=result.elapsed_time,
                        answer=result.raw_answer,
                        error="",
                    )
                )
                if result.success:
                    success_count += 1
                else:
                    failure_count += 1

        print(f"   ✅ 成功: {success_count}, ❌ 失敗: {failure_count}")
        print(f"   ⏱️  總耗時: {total_time:.2f}s")

        return ProviderResult(
            provider="tavily",
            total_time=total_time,
            query_results=query_results,
            success_count=success_count,
            failure_count=failure_count,
        )

    async def run_gemini_flash(self, queries: List[Dict[str, str]]) -> ProviderResult:
        """執行 Gemini Flash Lite 平行搜尋"""
        from providers.gemini_search import gemini_flash_search

        print(f"\n🔍 Gemini Flash Lite 平行搜尋（{len(queries)} 個查詢）...")

        start = time.time()

        # 並行執行
        tasks = [gemini_flash_search(q["query"]) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start

        # 組裝結果
        query_results = []
        success_count = 0
        failure_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                query_results.append(
                    QueryResult(
                        query=queries[i]["query"],
                        aspect=queries[i]["aspect"],
                        success=False,
                        elapsed_time=0,
                        answer="",
                        error=str(result),
                    )
                )
                failure_count += 1
            else:
                # SearchResult 屬性存取
                query_results.append(
                    QueryResult(
                        query=queries[i]["query"],
                        aspect=queries[i]["aspect"],
                        success=result.success,
                        elapsed_time=result.elapsed_time,
                        answer=result.raw_answer,
                        error="",
                    )
                )
                if result.success:
                    success_count += 1
                else:
                    failure_count += 1

        print(f"   ✅ 成功: {success_count}, ❌ 失敗: {failure_count}")
        print(f"   ⏱️  總耗時: {total_time:.2f}s")

        return ProviderResult(
            provider="gemini_flash",
            total_time=total_time,
            query_results=query_results,
            success_count=success_count,
            failure_count=failure_count,
        )

    async def compare_single_company(self, company: str) -> Dict[str, Any]:
        """比較單一公司的兩種方案"""
        print(f"\n{'=' * 60}")
        print(f"公司：{company}")
        print(f"{'=' * 60}")

        queries = self.generate_queries(company)
        print(f"查詢數量：{len(queries)}")

        # 並行執行兩種方案
        tavily_result, gemini_result = await asyncio.gather(
            self.run_tavily(queries),
            self.run_gemini_flash(queries),
        )

        # 計算比較
        comparison = self._compare_results(tavily_result, gemini_result)

        return {
            "company": company,
            "queries": queries,
            "tavily": asdict(tavily_result),
            "gemini_flash": asdict(gemini_result),
            "comparison": comparison,
        }

    def _compare_results(
        self, tavily: ProviderResult, gemini: ProviderResult
    ) -> Dict[str, Any]:
        """比較兩種方案的結果"""

        # 速度比較
        speed_diff = tavily.total_time - gemini.total_time
        speed_improvement = (
            (tavily.total_time - gemini.total_time) / tavily.total_time * 100
            if tavily.total_time > 0
            else 0
        )

        # 各面向耗時比較
        aspect_comparison = {}
        for aspect in self.aspects.keys():
            tavily_times = [
                q.elapsed_time
                for q in tavily.query_results
                if q.aspect == aspect and q.success
            ]
            gemini_times = [
                q.elapsed_time
                for q in gemini.query_results
                if q.aspect == aspect and q.success
            ]

            tavily_avg = sum(tavily_times) / len(tavily_times) if tavily_times else 0
            gemini_avg = sum(gemini_times) / len(gemini_times) if gemini_times else 0

            aspect_comparison[aspect] = {
                "tavily_avg": round(tavily_avg, 3),
                "gemini_avg": round(gemini_avg, 3),
                "winner": "tavily" if tavily_avg < gemini_avg else "gemini_flash",
            }

        return {
            "speed": {
                "tavily_total": round(tavily.total_time, 3),
                "gemini_flash_total": round(gemini.total_time, 3),
                "difference": round(speed_diff, 3),
                "improvement_percent": round(speed_improvement, 1),
                "winner": "tavily" if speed_diff > 0 else "gemini_flash",
            },
            "reliability": {
                "tavily_success_rate": f"{tavily.success_count}/{len(tavily.query_results)}",
                "gemini_flash_success_rate": f"{gemini.success_count}/{len(gemini.query_results)}",
            },
            "aspect_comparison": aspect_comparison,
        }

    # ===== 彙整與生成相關方法 =====

    def run_summarization(self, query_results: List[QueryResult]) -> Dict[str, Any]:
        """
        執行四面向彙整

        Args:
            query_results: 查詢結果列表

        Returns:
            Dict: 彙整後的四面向結果
        """
        print("\n📋 四面向彙整中...")

        summarizer = FourAspectSummarizer()

        # 轉換為 dict 格式
        results_dict = [asdict(r) for r in query_results]

        summaries = summarizer.summarize(results_dict)
        summary_dict = summarizer.to_dict(summaries)

        # 打印各面向狀態
        for aspect, summary in summaries.items():
            char_count = summary.total_characters
            queries = summary.source_queries
            print(f"   {aspect}: {char_count} 字（{queries} 個查詢成功）")

        print("   ✅ 彙整完成")
        return summary_dict

    def run_brief_generation(
        self, company: str, summaries: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        執行簡介生成

        Args:
            company: 公司名稱
            summaries: 四面向彙整結果

        Returns:
            Dict: 生成的簡介
        """
        print("\n📝 簡介生成中...")

        generator = BriefGenerator()
        brief = generator.generate(company, summaries, BriefLength.MEDIUM)

        print(f"   標題：{brief.title}")
        print(f"   字數：{brief.word_count} 字")
        print(f"   耗時：{brief.generation_time:.2f}s")
        print(f"   ✅ 生成完成")
        print(f"\n   內容預覽：")
        preview = (
            brief.content[:150] + "..." if len(brief.content) > 150 else brief.content
        )
        for line in preview.split("\n"):
            print(f"      {line}")

        return generator.to_dict(brief)

    def run_tag_generation(
        self, company: str, brief: str, summaries: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        執行標籤生成

        Args:
            company: 公司名稱
            brief: 公司簡介
            summaries: 四面向彙整結果

        Returns:
            Dict: 生成的標籤
        """
        print("\n🏷️  標籤生成中...")

        generator = TagGenerator()
        tags = generator.generate(company, brief, summaries)

        print(f"   標籤數：{len(tags.tags)} 個")
        print(f"   耗時：{tags.generation_time:.2f}s")
        print(f"   標籤：{', '.join(tags.tags[:5])}...")
        print(f"   ✅ 生成完成")

        return generator.to_dict(tags)

    async def run_full_pipeline(
        self, company: str, provider: str = "gemini_flash"
    ) -> Dict[str, Any]:
        """
        執行完整流程：搜尋 -> 彙整 -> 簡介 -> 標籤

        Args:
            company: 公司名稱
            provider: 使用的搜尋 provider（預設 gemini_flash）

        Returns:
            Dict: 完整流程結果
        """
        print(f"\n{'=' * 60}")
        print(f"公司：{company}")
        print(f"{'=' * 60}")

        queries = self.generate_queries(company)
        print(f"查詢數量：{len(queries)}")

        # Step 1: 搜尋
        print("\n🔍 搜尋階段")
        if provider == "gemini_flash":
            provider_result = await self.run_gemini_flash(queries)
        else:
            provider_result = await self.run_tavily(queries)

        # Step 2: 彙整
        summaries = self.run_summarization(provider_result.query_results)

        # Step 3: 簡介生成
        brief_result = self.run_brief_generation(company, summaries)

        # Step 4: 標籤生成
        tag_result = self.run_tag_generation(
            company, brief_result["content"], summaries
        )

        return {
            "company": company,
            "search": {
                "provider": provider,
                "total_time": provider_result.total_time,
                "success_count": provider_result.success_count,
            },
            "summaries": summaries,
            "brief": brief_result,
            "tags": tag_result,
        }

    async def run_provider_comparison(self, company: str) -> Dict[str, Any]:
        """
        比較兩個 Provider 的完整流程產出

        Args:
            company: 公司名稱

        Returns:
            Dict: 兩個 provider 的結果比較
        """
        print(f"\n{'=' * 60}")
        print(f"公司：{company} - 雙 Provider 比較")
        print(f"{'=' * 60}")

        queries = self.generate_queries(company)
        print(f"查詢數量：{len(queries)}")

        # 並行執行兩個 Provider
        print("\n🔍 雙 Provider 搜尋中...")
        tavily_result, gemini_result = await asyncio.gather(
            self.run_tavily(queries),
            self.run_gemini_flash(queries),
        )

        # 個別執行彙整、簡介、標籤
        results = {}

        for provider_name, provider_result in [
            ("tavily", tavily_result),
            ("gemini_flash", gemini_result),
        ]:
            print(f"\n📊 {provider_name.upper()} 處理中...")

            # 彙整
            summaries = self.run_summarization(provider_result.query_results)

            # 簡介
            brief = self.run_brief_generation(company, summaries)

            # 標籤
            tags = self.run_tag_generation(company, brief["content"], summaries)

            results[provider_name] = {
                "search_time": provider_result.total_time,
                "search_success": provider_result.success_count,
                "summaries": summaries,
                "brief": brief,
                "tags": tags,
            }

            print(
                f"   {provider_name}: 搜尋 {provider_result.total_time:.2f}s | 簡介 {brief['word_count']} 字 | 標籤 {len(tags['tags'])} 個"
            )

        # 比較結果
        comparison = self._compare_outputs(results)

        # 內容評估
        print("\n📈 內容品質評估中...")
        eval_result = self._evaluate_outputs(company, results)
        comparison["evaluation"] = eval_result

        return {
            "company": company,
            "tavily": results["tavily"],
            "gemini_flash": results["gemini_flash"],
            "comparison": comparison,
        }

    def _evaluate_outputs(
        self, company: str, results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        評估兩個 provider 的產出內容

        Args:
            company: 公司名稱
            results: 兩個 provider 的產出

        Returns:
            Dict: 評估結果
        """
        evaluator = ContentEvaluator()

        tavily = results["tavily"]
        gemini = results["gemini_flash"]

        # 比較評估
        comparison = evaluator.compare(
            company=company,
            tavily_brief=tavily["brief"]["content"],
            tavily_tags=tavily["tags"]["tags"],
            gemini_brief=gemini["brief"]["content"],
            gemini_tags=gemini["tags"]["tags"],
        )

        # 打印評估摘要
        print(f"\n   【內容品質評估】")
        print(f"   Tavily 總分:     {comparison['tavily']['overall_score']}")
        print(f"   Gemini Flash:    {comparison['gemini_flash']['overall_score']}")

        dim_comparison = comparison["dimension_comparison"]
        for dim_name, dim_data in dim_comparison.items():
            winner_emoji = "⬆️" if dim_data["winner"] == "tavily" else "⬇️"
            print(
                f"   {dim_name}: Tavily {dim_data['tavily']} vs Gemini {dim_data['gemini_flash']} {winner_emoji}"
            )

        print(
            f"\n   維度勝出統計: Tavily {comparison['winner_counts']['tavily']} vs Gemini {comparison['winner_counts']['gemini_flash']}"
        )
        print(f"   總分勝出: {comparison['overall_winner'].upper()}")

        return comparison

    def _compare_outputs(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """比較兩個 provider 的輸出"""
        tavily = results["tavily"]
        gemini = results["gemini_flash"]

        # 字數比較
        tavily_chars = sum(s["total_characters"] for s in tavily["summaries"].values())
        gemini_chars = sum(s["total_characters"] for s in gemini["summaries"].values())

        comparison = {
            "search": {
                "tavily_time": round(tavily["search_time"], 3),
                "gemini_flash_time": round(gemini["search_time"], 3),
                "winner": "tavily"
                if tavily["search_time"] < gemini["search_time"]
                else "gemini_flash",
                "improvement_percent": round(
                    abs(tavily["search_time"] - gemini["search_time"])
                    / max(tavily["search_time"], gemini["search_time"])
                    * 100,
                    1,
                ),
            },
            "content_volume": {
                "tavily_chars": tavily_chars,
                "gemini_flash_chars": gemini_chars,
                "winner": "tavily" if tavily_chars > gemini_chars else "gemini_flash",
            },
            "brief": {
                "tavily_words": tavily["brief"]["word_count"],
                "gemini_flash_words": gemini["brief"]["word_count"],
                "tavily_title": tavily["brief"]["title"],
                "gemini_flash_title": gemini["brief"]["title"],
            },
            "tags": {
                "tavily_count": len(tavily["tags"]["tags"]),
                "gemini_flash_count": len(gemini["tags"]["tags"]),
                "tavily_tags": tavily["tags"]["tags"],
                "gemini_flash_tags": gemini["tags"]["tags"],
            },
        }

        return comparison

    async def run_all(self, mode: str = "speed_test") -> Dict[str, Any]:
        """
        執行測試

        Args:
            mode: 測試模式
                - "speed_test": 只測速度（比較 Tavily vs Gemini Flash）
                - "full_pipeline": 完整流程（搜尋 + 彙整 + 簡介 + 標籤）
                - "brief_only": 只生成簡介（使用預設測試公司）
                - "compare": 比較兩個 provider 的產出品質
        """
        print("=" * 60)
        print("平行搜尋速度比較測試")
        print("=" * 60)
        print(f"測試公司：{self.companies}")
        print(f"每公司查詢數：{len(self.generate_queries(self.companies[0]))}")
        print(f"測試模式：{mode}")

        if mode == "speed_test":
            return await self._run_speed_test()
        elif mode == "full_pipeline":
            return await self._run_full_pipeline()
        elif mode == "brief_only":
            return await self._run_brief_only()
        elif mode == "compare":
            return await self._run_compare()
        else:
            raise ValueError(f"Unknown mode: {mode}")

    async def _run_speed_test(self) -> Dict[str, Any]:
        """執行速度比較測試"""
        results = []

        for company in self.companies:
            result = await self.compare_single_company(company)
            results.append(result)

        # 總結
        print("\n" + "=" * 60)
        print("測試總結")
        print("=" * 60)

        tavily_totals = [r["comparison"]["speed"]["tavily_total"] for r in results]
        gemini_totals = [
            r["comparison"]["speed"]["gemini_flash_total"] for r in results
        ]

        tavily_avg = sum(tavily_totals) / len(tavily_totals)
        gemini_avg = sum(gemini_totals) / len(gemini_totals)

        print(f"\n平均總耗時：")
        print(f"  Tavily:           {tavily_avg:.2f}s")
        print(f"  Gemini Flash Lite: {gemini_avg:.2f}s")

        if tavily_avg > gemini_avg:
            improvement = (tavily_avg - gemini_avg) / tavily_avg * 100
            print(f"\n✅ Gemini Flash Lite 較快，改善: {improvement:.1f}%")
        else:
            improvement = (gemini_avg - tavily_avg) / gemini_avg * 100
            print(f"\n✅ Tavily 較快，改善: {improvement:.1f}%")

        return {
            "timestamp": datetime.now().isoformat(),
            "mode": "speed_test",
            "companies": self.companies,
            "queries_per_company": len(self.generate_queries(self.companies[0])),
            "results": results,
            "summary": {
                "tavily_avg": round(tavily_avg, 3),
                "gemini_flash_avg": round(gemini_avg, 3),
                "winner": "tavily" if tavily_avg < gemini_avg else "gemini_flash",
            },
        }

    async def _run_full_pipeline(self) -> Dict[str, Any]:
        """執行完整流程測試"""
        results = []
        total_search_time = 0
        total_summarize_time = 0
        total_brief_time = 0
        total_tag_time = 0

        for company in self.companies:
            pipeline_result = await self.run_full_pipeline(company)

            total_search_time += pipeline_result["search"]["total_time"]
            total_summarize_time += 0.1  # 估算
            total_brief_time += pipeline_result["brief"]["generation_time"]
            total_tag_time += pipeline_result["tags"]["generation_time"]

            results.append(pipeline_result)

        # 總結
        print("\n" + "=" * 60)
        print("完整流程測試總結")
        print("=" * 60)
        print(f"\n各階段平均耗時：")
        print(f"  搜尋：  {total_search_time / len(results):.2f}s")
        print(f"  彙整：  {total_summarize_time:.2f}s（估算）")
        print(f"  簡介：  {total_brief_time / len(results):.2f}s")
        print(f"  標籤：  {total_tag_time / len(results):.2f}s")
        print(
            f"\n  總計：  {(total_search_time + total_summarize_time + total_brief_time + total_tag_time) / len(results):.2f}s/公司"
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "mode": "full_pipeline",
            "companies": self.companies,
            "results": results,
            "summary": {
                "avg_search_time": round(total_search_time / len(results), 2),
                "avg_brief_time": round(total_brief_time / len(results), 2),
                "avg_tag_time": round(total_tag_time / len(results), 2),
            },
        }

    async def _run_brief_only(self) -> Dict[str, Any]:
        """只生成簡介測試（快速驗證）"""
        # 只用第一個公司測試
        company = self.companies[0]
        result = await self.run_full_pipeline(company)

        return {
            "timestamp": datetime.now().isoformat(),
            "mode": "brief_only",
            "company": company,
            "result": result,
        }

    async def _run_compare(self) -> Dict[str, Any]:
        """比較兩個 Provider 的產出"""
        results = []

        for company in self.companies:
            result = await self.run_provider_comparison(company)
            results.append(result)

        # 總結
        print("\n" + "=" * 60)
        print("Provider 產出比較總結")
        print("=" * 60)

        tavily_search_avg = sum(
            r["comparison"]["search"]["tavily_time"] for r in results
        ) / len(results)
        gemini_search_avg = sum(
            r["comparison"]["search"]["gemini_flash_time"] for r in results
        ) / len(results)

        print(f"\n【搜尋速度】")
        print(f"  Tavily:           {tavily_search_avg:.2f}s")
        print(f"  Gemini Flash:     {gemini_search_avg:.2f}s")

        if tavily_search_avg > gemini_search_avg:
            improvement = (
                (tavily_search_avg - gemini_search_avg) / tavily_search_avg * 100
            )
            print(f"  勝出：Gemini Flash（快 {improvement:.1f}%）")
        else:
            improvement = (
                (gemini_search_avg - tavily_search_avg) / gemini_search_avg * 100
            )
            print(f"  勝出：Tavily（快 {improvement:.1f}%）")

        print(f"\n【內容字數】")
        for r in results:
            comp = r["comparison"]["content_volume"]
            print(f"  {r['company']}:")
            print(f"    Tavily: {comp['tavily_chars']} 字")
            print(f"    Gemini: {comp['gemini_flash_chars']} 字")

        print(f"\n【簡介產出】")
        for r in results:
            comp = r["comparison"]["brief"]
            print(f"  {r['company']}:")
            print(f"    Tavily:   {comp['tavily_words']} 字 - {comp['tavily_title']}")
            print(
                f"    Gemini:   {comp['gemini_flash_words']} 字 - {comp['gemini_flash_title']}"
            )

        return {
            "timestamp": datetime.now().isoformat(),
            "mode": "compare",
            "companies": self.companies,
            "results": results,
            "summary": {
                "avg_search_time": {
                    "tavily": round(tavily_search_avg, 3),
                    "gemini_flash": round(gemini_search_avg, 3),
                },
                "speed_winner": "tavily"
                if tavily_search_avg < gemini_search_avg
                else "gemini_flash",
            },
        }

    def save_results(self, results: Dict[str, Any], output_dir: str = None):
        """儲存結果"""
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), "results")

        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"comparison_{timestamp}.json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n結果已儲存：{output_file}")
        return output_file


async def main():
    """主程式"""
    runner = ParallelComparisonRunner()
    results = await runner.run_all()
    runner.save_results(results)

    # 打印摘要
    print("\n" + "=" * 60)
    print("JSON 格式摘要")
    print("=" * 60)
    print(json.dumps(results["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
