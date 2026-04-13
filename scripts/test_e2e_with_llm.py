#!/usr/bin/env python3
"""
Phase 14 Stage 2 端到端測試
實際呼叫 API + LLM (Gemini)，使用 Checkpoint 1 資料
驗證三模板（CONCISE / STANDARD / DETAILED）差異化

用法:
  python3 test_e2e_with_llm.py
"""

import sys
import os
import re
import json
import time
import csv
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==================== 設定 ====================

API_URL = "http://localhost:5000/v1/company/profile/process"
TIMEOUT = 60  # 秒
TEST_CASES = None  # 測試全部 10 個案例

OUTPUT_DIR = Path(
    "/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1/phase14/stage2/artifacts"
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==================== 工具函數 ====================


def load_checkpoint1_data():
    """載入 Checkpoint 1 測試資料"""
    path = Path(
        "/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1/phase14/checkpoint1/artifacts/test_inputs.json"
    )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["test_inputs"]


def strip_html(text):
    """去除 HTML 標籤"""
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n\n+", "\n", text)
    return text.strip()


def count_chinese(text):
    return len(re.findall(r"[\u4e00-\u9fff]", strip_html(text)))


def call_api(case_id, company_name, organ_no, brief, mode, trade=None, products=None):
    """呼叫 API"""
    payload = {
        "mode": "GENERATE",
        "organ": company_name,
        "organNo": organ_no,
        "brief": brief,
        "optimization_mode": mode,  # CONCISE / STANDARD / DETAILED
    }
    if trade:
        payload["trade"] = trade
    if products:
        payload["products"] = products

    try:
        start = time.time()
        resp = requests.post(API_URL, json=payload, timeout=TIMEOUT)
        elapsed = time.time() - start

        if resp.status_code == 200:
            data = resp.json()
            body_html = data.get("body_html", "")
            plain = strip_html(body_html)
            chinese = count_chinese(body_html)
            return {
                "success": True,
                "case_id": case_id,
                "mode": mode,
                "body_html": body_html,
                "plain_text": plain,
                "chinese_count": chinese,
                "elapsed": elapsed,
                "error": None,
            }
        else:
            return {
                "success": False,
                "case_id": case_id,
                "mode": mode,
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                "elapsed": time.time() - start,
            }
    except Exception as e:
        return {
            "success": False,
            "case_id": case_id,
            "mode": mode,
            "error": str(e),
            "elapsed": time.time() - start,
        }


# ==================== 主程式 ====================


def main():
    print("=" * 70)
    print("Phase 14 Stage 2 端到端測試（實際呼叫 LLM）")
    print("=" * 70)
    print()

    # 載入資料
    all_cases = load_checkpoint1_data()
    cases = all_cases[: TEST_CASES[-1]] if TEST_CASES else all_cases
    print(f"📂 載入 {len(all_cases)} 個測試案例，將測試前 {len(cases)} 個")
    print(f"🌐 API URL: {API_URL}")
    print()

    MODES = ["CONCISE", "STANDARD", "DETAILED"]
    MODE_NAMES = {"CONCISE": "精簡", "STANDARD": "標準", "DETAILED": "詳細"}

    # 測試結果
    results = {}  # {case_id: {mode: result}}
    all_results = []

    for case in cases:
        case_id = case["case_id"]
        company_name = case["company"]["name"]
        organ_no = case["company"].get("registration_id", "")
        brief = case.get("input_text", "")
        trade = case["company"].get("industry", {}).get("type", "")
        products = case.get("product_service", "")

        print("-" * 70)
        print(f"案例 {case_id}: {company_name}")
        print(f"  統一編號: {organ_no}")
        print(f"  輸入長度: {len(brief)} 字")
        print()

        results[case_id] = {}

        for mode in MODES:
            print(f"  [{mode}] 呼叫中...", end=" ", flush=True)
            r = call_api(case_id, company_name, organ_no, brief, mode, trade, products)
            results[case_id][mode] = r

            if r["success"]:
                print(f"✅ {r['chinese_count']} 字 ({r['elapsed']:.1f}s)")
                print(f"     {r['plain_text']}")
            else:
                print(f"❌ {r['error'][:60]}")

        print()

    # ===== 結果分析 =====
    print("=" * 70)
    print("📊 結果分析")
    print("=" * 70)
    print()

    success_count = 0
    total_calls = 0
    summary_rows = []

    for case in cases:
        case_id = case["case_id"]
        cname = case["company"]["name"]
        row = {"案例": case_id, "公司": cname}

        print(f"案例 {case_id}: {cname}")
        row_data = []

        for mode in MODES:
            r = results[case_id].get(mode, {})
            total_calls += 1
            if r.get("success"):
                success_count += 1
                char_count = r["chinese_count"]
                row[f"{mode}_字數"] = char_count
                row[f"{mode}_狀態"] = "✅"
                print(f"  {MODE_NAMES[mode]:4s}: {char_count:3d} 字")
                row_data.append(char_count)
            else:
                row[f"{mode}_字數"] = "-"
                row[f"{mode}_狀態"] = f"❌ {r.get('error', '')[:30]}"
                print(f"  {MODE_NAMES[mode]:4s}: ❌")
                row_data.append(None)

        # 差異分析
        if all(v is not None for v in row_data):
            c, s, d = row_data
            concise_ok = c <= 110
            standard_ok = s <= 210
            detailed_ok = d > c
            diff_pct = (d - c) / c * 100 if c > 0 else 0

            row["c_s差"] = s - c
            row["s_d差"] = d - s
            row["差異%"] = f"{diff_pct:.0f}%"
            row["差異達標"] = "✅" if detailed_ok else "❌"
            row["concise達標"] = "✅" if concise_ok else "❌"
            row["standard達標"] = "✅" if standard_ok else "❌"

            print(f"  差異: concise={c} / standard={s} / detailed={d}")
            print(f"  concise→standard: {s - c:+d} 字")
            print(f"  standard→detailed: {d - s:+d} 字")
            print(f"  增幅: {diff_pct:.0f}% {'✅' if detailed_ok else '❌'}")
        else:
            row["c_s差"] = "-"
            row["s_d差"] = "-"
            row["差異%"] = "-"
            row["差異達標"] = "❌"
            row["concise達標"] = "-"
            row["standard達標"] = "-"

        print()
        summary_rows.append(row)

    # ===== 總結 =====
    print("=" * 70)
    print("📋 總結")
    print("=" * 70)
    print()

    total = len(cases)
    diff_ok = sum(1 for r in summary_rows if r.get("差異達標") == "✅")
    concise_ok = sum(1 for r in summary_rows if r.get("concise達標") == "✅")
    standard_ok = sum(1 for r in summary_rows if r.get("standard達標") == "✅")

    avg_c = sum(r.get(f"CONCISE_字數", 0) or 0 for r in summary_rows) / total
    avg_s = sum(r.get(f"STANDARD_字數", 0) or 0 for r in summary_rows) / total
    avg_d = sum(r.get(f"DETAILED_字數", 0) or 0 for r in summary_rows) / total

    print(
        f"API 呼叫成功率: {success_count}/{total_calls} ({success_count / total_calls * 100:.0f}%)"
    )
    print()
    print(f"平均字數:")
    print(f"  CONCISE:  {avg_c:.1f} 字 (目標 ≤110)")
    print(f"  STANDARD: {avg_s:.1f} 字 (目標 ≤210)")
    print(f"  DETAILED: {avg_d:.1f} 字")
    print()
    print(f"達標情況:")
    print(f"  concise ≤110 字:  {concise_ok}/{total} ({concise_ok / total * 100:.0f}%)")
    print(f"  detailed > concise: {diff_ok}/{total} ({diff_ok / total * 100:.0f}%)")
    print()

    # ===== 產出報告 =====
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUTPUT_DIR / f"stage2_e2e_results_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.now().isoformat(),
                "api_url": API_URL,
                "data_source": "Checkpoint 1",
                "tested_cases": len(cases),
                "total_calls": total_calls,
                "success_rate": f"{success_count / total_calls * 100:.0f}%",
                "summary": {
                    "avg_concise": round(avg_c, 1),
                    "avg_standard": round(avg_s, 1),
                    "avg_detailed": round(avg_d, 1),
                    "concise_ok": concise_ok,
                    "standard_ok": standard_ok,
                    "all_different": diff_ok,
                },
                "results": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"✅ JSON 報告: {json_path.name}")

    # ===== Checkpoint 結論 =====
    print()
    print("=" * 70)
    print("📋 Phase 14 Stage 2 Checkpoint 標準")
    print("=" * 70)
    print()
    print("| 標準 | 目標 | 實際 | 狀態 |")
    print("|---------|------|------|------|")
    print(
        f"| concise 字數 | ≤110 | {avg_c:.1f} | {'✅ PASS' if concise_ok == total else f'⚠️ {concise_ok}/{total}'} |"
    )
    print(
        f"| standard 字數 | ≤210 | {avg_s:.1f} | {'✅ PASS' if standard_ok == total else f'⚠️ {standard_ok}/{total}'} |"
    )
    print(
        f"| 三模板差異 | detailed > concise | +{(avg_d - avg_c):.0f} ({avg_d / avg_c * 100:.0f}%) | {'✅ PASS' if diff_ok == total else f'⚠️ {diff_ok}/{total}'} |"
    )
    print()

    if success_count == total_calls and concise_ok == total and diff_ok == total:
        print("✅✅✅ Stage 2 Checkpoint 通過 ✅✅✅")
    else:
        print("⚠️  部分標準未達標，需分析原因")

    # ===== 生成 Excel 報告 =====
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = OUTPUT_DIR / f"stage2_e2e_full_{timestamp}.xlsx"

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        # Sheet 1: 三模板對比
        rows = []
        for case in cases:
            cid = case["case_id"]
            cname = case["company"]["name"]
            for mode in ["CONCISE", "STANDARD", "DETAILED"]:
                r = results[cid][mode]
                if r["success"]:
                    rows.append(
                        {
                            "案例": cid,
                            "公司名稱": cname,
                            "模式": mode,
                            "中文字數": r["chinese_count"],
                            "耗時(秒)": round(r["elapsed"], 1),
                            "內容預覽": r["plain_text"],
                        }
                    )
        df_comp = pd.DataFrame(rows)
        df_comp.to_excel(writer, sheet_name="三模板對比", index=False)
        ws = writer.sheets["三模板對比"]
        ws.column_dimensions["A"].width = 8
        ws.column_dimensions["B"].width = 28
        ws.column_dimensions["C"].width = 12
        ws.column_dimensions["D"].width = 12
        ws.column_dimensions["E"].width = 12
        ws.column_dimensions["F"].width = 60

        # Sheet 2: 摘要
        sum_rows = []
        for case in cases:
            cid = case["case_id"]
            cname = case["company"]["name"]
            row = {"案例": cid, "公司": cname}
            for mode in ["CONCISE", "STANDARD", "DETAILED"]:
                r = results[cid][mode]
                row[f"{mode}_字數"] = r["chinese_count"] if r["success"] else "-"
            sum_rows.append(row)
        df_sum = pd.DataFrame(sum_rows)
        df_sum.to_excel(writer, sheet_name="摘要", index=False)
        ws2 = writer.sheets["摘要"]
        ws2.column_dimensions["A"].width = 8
        ws2.column_dimensions["B"].width = 28
        ws2.column_dimensions["C"].width = 12
        ws2.column_dimensions["D"].width = 12
        ws2.column_dimensions["E"].width = 12

        # Sheet 3: 測試摘要
        ts = pd.DataFrame(
            [
                ["測試日期", datetime.now().strftime("%Y-%m-%d %H:%M")],
                ["資料來源", "Checkpoint 1 (10 個真實案例)"],
                ["總案例數", total],
                [
                    "API成功率",
                    f"{success_count}/{total_calls} ({success_count / total_calls * 100:.0f}%)",
                ],
                [
                    "concise達標",
                    f"{concise_ok}/{total} ({concise_ok / total * 100:.0f}%)",
                ],
                [
                    "standard達標",
                    f"{standard_ok}/{total} ({standard_ok / total * 100:.0f}%)",
                ],
                ["三模板差異", f"{diff_ok}/{total} ({diff_ok / total * 100:.0f}%)"],
                ["平均CONCISE", f"{avg_c:.1f} 字"],
                ["平均STANDARD", f"{avg_s:.1f} 字"],
                ["平均DETAILED", f"{avg_d:.1f} 字"],
                [
                    "Checkpoint結論",
                    "✅ PASS"
                    if (
                        concise_ok == total
                        and standard_ok == total
                        and diff_ok == total
                    )
                    else "⚠️",
                ],
            ]
        )
        ts.to_excel(writer, sheet_name="測試摘要", index=False, header=False)
        ws3 = writer.sheets["測試摘要"]
        ws3.column_dimensions["A"].width = 20
        ws3.column_dimensions["B"].width = 30

    print(f"✅ Excel 報告: {excel_path.name}")


if __name__ == "__main__":
    main()
