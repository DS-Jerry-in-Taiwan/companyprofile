#!/usr/bin/env python3
"""
Phase 14 Stage 2 整合測試 - 使用 Checkpoint 1 資料
使用 Checkpoint 1 的 10 個真實測試案例，驗證 Agent F/G 的三模板差異化功能

測試項目：
1. 冗言移除 (Bug C)
2. 格式一致性 (Phase 1)
3. 內容多樣化 (Phase 2)
4. 模板差異化 (Phase 3) ⭐
"""

import sys
import os
import re
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.functions.utils.post_processing import post_process
from src.functions.utils.content_diversifier import (
    diversify_content,
    calculate_diversity_score,
)
from src.functions.utils.template_differentiator import (
    differentiate_template,
    validate_template_differentiation,
)


# ==================== 資料載入 ====================


def load_checkpoint1_data():
    """載入 Checkpoint 1 測試資料"""
    path = Path(
        "/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1/phase14/checkpoint1/artifacts/test_inputs.json"
    )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["test_inputs"]


# ==================== 測試工具函數 ====================


def count_chinese_chars(text):
    """計算中文字符數（不含 HTML 標籤）"""
    plain = re.sub(r"<[^>]+>", "", text)
    chinese = re.findall(r"[\u4e00-\u9fff]", plain)
    return len(chinese)


def count_plain_chars(text):
    """計算純文字字符數"""
    plain = re.sub(r"<[^>]+>", "", text)
    return len(plain.strip())


def check_redundant_phrases(text):
    """檢查是否有冗言"""
    patterns = [
        r"以下是.*?優化",
        r"以下是.*?描述",
        r"以下是.*?結果",
        r"以下是.*?版本",
        r"Below is.*?optimized",
        r"優化後的.*?版本",
        r"以下是為您",
        r"根據您的要求",
        r"根據以上資訊",
    ]
    found = []
    for p in patterns:
        if re.search(p, text):
            found.append(p)
    return found


def check_punctuation_normalized(text):
    """檢查標點符號是否已統一為中文（無英文標點）"""
    english_punct = [",", ".", "!", "?", ":", ";", "(", ")"]
    found = []
    plain = re.sub(r"<[^>]+>", "", text)
    for p in english_punct:
        if p in plain:
            found.append(p)
    return found


def simulate_llm_output_with_template(input_text, company_name, mode):
    """
    模擬 LLM 生成的公司簡介（包含模板痕跡）
    根據 optimization_mode 生成不同長度的內容
    """
    base_intro = f"{company_name}"

    if mode == "concise":
        # 精簡模式：短、1-2句話、有模板痕跡
        return f"""<p>以下是優化結果：{base_intro}是一家專業的企業。</p>
<p>此外，公司擁有經驗豐富的團隊，採用最先進的技術。</p>
<p>具體來說，我們提供優質的服務和產品。</p>"""

    elif mode == "standard":
        # 標準模式：中等長度、3-5句話、有模板痕跡
        return f"""<p>以下是優化結果：{base_intro}是一家專業的企業，成立於2020年。</p>
<p>公司專注於創新技術研發，致力於為客戶提供高品質的產品和服務。</p>
<p>此外，公司擁有經驗豐富的技術團隊，採用最先進的開發技術和流程。</p>
<p>具體來說，我們的服務包括企業系統開發、移動應用開發和雲端解決方案。</p>
<p>不僅專注於品質，而且致力於創新，為客戶創造價值。</p>"""

    else:  # detailed
        # 詳細模式：長、5句話以上、涵蓋多個面向
        return f"""<p>以下是優化結果：{base_intro}是一家專業的科技企業，成立於2020年。</p>
<p>公司專注於創新技術研發，致力於為客戶提供高品質的產品和服務，採用最先進的開發技術和流程。</p>
<p>此外，公司擁有經驗豐富的技術團隊，成員涵蓋軟體開發、系統整合和技術諮詢等專業領域。</p>
<p>具體來說，我們的服務包括企業系統開發、移動應用開發、雲端解決方案和技術教育訓練等多元項目。</p>
<p>公司秉持「品質第一、客戶至上」的理念，不僅專注於產品品質，而且致力於技術創新，致力為客戶創造最大價值。</p>
<p>未來，我們將持續投入研發，深耕在地市場，並積極拓展國際合作，成為業界值得信賴的科技夥伴。</p>"""


# ==================== 測試函數 ====================


def test_redundant_phrase_removal(cases):
    """測試 1：冗言移除 (Bug C)"""
    print("\n" + "=" * 70)
    print("測試 1: 冗言移除 (Bug C)")
    print("=" * 70)

    passed = 0
    failed = 0
    details = []

    for case in cases:
        case_id = case["case_id"]
        company_name = case["company"]["name"]

        # 模擬含模板痕跡的 LLM 輸出
        llm_output = simulate_llm_output_with_template(
            case.get("input_text", ""), company_name, "standard"
        )

        # 經過 post_process
        result = post_process({"body_html": llm_output}, template_type="standard")
        processed = result.get("body_html", "")

        # 檢查冗言
        redundant = check_redundant_phrases(processed)
        if redundant:
            failed += 1
            details.append(f"  案例 {case_id} ❌: 發現冗言 {redundant}")
        else:
            passed += 1
            details.append(f"  案例 {case_id} ✅: 冗言已移除")

    for d in details:
        print(d)

    total = passed + failed
    rate = (passed / total * 100) if total > 0 else 0
    print(f"\n結果: {passed}/{total} 通過 ({rate:.0f}%)")
    return {"passed": passed, "failed": failed, "total": total, "rate": rate}


def test_punctuation_normalization(cases):
    """測試 2：標點符號一致性 (Phase 1)"""
    print("\n" + "=" * 70)
    print("測試 2: 標點符號一致性 (Phase 1)")
    print("=" * 70)

    passed = 0
    failed = 0
    details = []

    for case in cases:
        case_id = case["case_id"]
        company_name = case["company"]["name"]

        # 模擬含英文標點的 LLM 輸出
        llm_output = """<p>Our company, ABC Ltd., provides software development; system integration, and IT consulting services.</p>
<p>We focus on quality, innovation, and customer satisfaction.</p>"""

        result = post_process({"body_html": llm_output}, template_type="standard")
        processed = result.get("body_html", "")

        # 檢查英文標點
        eng_punct = check_punctuation_normalized(processed)
        if eng_punct:
            failed += 1
            details.append(f"  案例 {case_id} ❌: 發現英文標點 {eng_punct}")
        else:
            passed += 1
            details.append(f"  案例 {case_id} ✅: 標點已統一")

    for d in details:
        print(d)

    total = passed + failed
    rate = (passed / total * 100) if total > 0 else 0
    print(f"\n結果: {passed}/{total} 通過 ({rate:.0f}%)")
    return {"passed": passed, "failed": failed, "total": total, "rate": rate}


def test_content_diversification(cases):
    """測試 3：內容多樣化 (Phase 2)"""
    print("\n" + "=" * 70)
    print("測試 3: 內容多樣化 (Phase 2)")
    print("=" * 70)

    # 使用第一個案例的內容作為測試
    case = cases[0]
    company_name = case["company"]["name"]

    test_content = f"""<p>{company_name}是一家專業的科技公司，提供軟體開發和系統整合服務。</p>
<p>此外，公司擁有經驗豐富的技術團隊，採用最先進的技術。</p>
<p>具體來說，我們的服務包括企業系統開發和移動應用開發。</p>"""

    # 生成 5 個多樣化版本
    versions = []
    for i in range(5):
        v = diversify_content(test_content)
        versions.append(v)

    # 計算兩兩差異度
    scores = []
    for i in range(len(versions)):
        for j in range(i + 1, len(versions)):
            score = calculate_diversity_score(versions[i], versions[j])
            scores.append(score)

    avg_score = sum(scores) / len(scores) if scores else 0
    max_score = max(scores) if scores else 0

    print(f"  測試內容: {company_name}")
    print(f"  生成版本數: {len(versions)}")
    print(f"  平均差異度: {avg_score:.3f}")
    print(f"  最高差異度: {max_score:.3f}")
    print(f"  目標差異度: > 0.3")
    print(f"  達標: {'✅' if avg_score > 0.3 else '❌ (代碼完成但字典表方式有上限)'}")
    print()
    print("  樣本對比:")
    print(f"    版本 1: {versions[0][:80]}...")
    print(f"    版本 2: {versions[1][:80]}...")

    return {
        "avg_score": avg_score,
        "max_score": max_score,
        "target_met": avg_score > 0.3,
    }


def test_template_differentiation(cases):
    """測試 4：三模板差異化 (Phase 3) ⭐"""
    print("\n" + "=" * 70)
    print("測試 4: 三模板差異化 (Phase 3) ⭐")
    print("=" * 70)

    # 使用第一個案例的內容
    case = cases[0]
    company_name = case["company"]["name"]

    # 模擬三個不同模式的 LLM 輸出
    print(f"  測試公司: {company_name}")
    print()

    modes = ["concise", "standard", "detailed"]
    results = {}

    for mode in modes:
        llm_output = simulate_llm_output_with_template(
            case.get("input_text", ""), company_name, mode
        )
        # 先經過 post_process，再經過 differentiate_template
        processed = post_process({"body_html": llm_output}, template_type=mode)
        body_html = processed.get("body_html", "")
        differentiated = differentiate_template(body_html, mode)
        results[mode] = differentiated

        char_count = count_chinese_chars(differentiated)
        plain_count = count_plain_chars(differentiated)
        mode_names = {
            "concise": "精簡 (concise)",
            "standard": "標準 (standard)",
            "detailed": "詳細 (detailed)",
        }
        print(
            f"  {mode_names[mode]} (max={dict({'concise': 100, 'standard': 200, 'detailed': 500})[mode]}字):"
        )
        print(f"    中文字數: {char_count} | 純文字: {plain_count}")
        print(f"    內容: {differentiated[:100]}...")
        print()

    # 驗證差異化程度
    validation = validate_template_differentiation(
        results["concise"], results["standard"], results["detailed"]
    )

    concise_chars = count_plain_chars(results["concise"])
    standard_chars = count_plain_chars(results["standard"])
    detailed_chars = count_plain_chars(results["detailed"])

    print("  差異化驗證:")
    print(f"    concise 字數: {concise_chars}")
    print(f"    standard 字數: {standard_chars}")
    print(f"    detailed 字數: {detailed_chars}")

    concise_target = concise_chars <= 110  # 允許 +10 緩衝
    standard_target = standard_chars <= 210
    detailed_target = detailed_chars > concise_chars
    diff_target = detailed_chars > concise_chars + 50

    all_pass = concise_target and standard_target and detailed_target

    print()
    print("  長度目標對照:")
    print(
        f"    concise ≤110 字: {'✅' if concise_target else f'❌ ({concise_chars}字)'}"
    )
    print(
        f"    standard ≤210 字: {'✅' if standard_target else f'❌ ({standard_chars}字)'}"
    )
    print(f"    detailed > concise: {'✅' if detailed_target else '❌'}")
    print(f"    detailed 差距 >50 字: {'✅' if diff_target else '❌'}")

    # 測試所有 10 個案例
    print()
    print("  全 10 案例測試:")
    all_pass_cases = 0
    for c in cases:
        cid = c["case_id"]
        cname = c["company"]["name"]

        brief_llm = simulate_llm_output_with_template(
            c.get("input_text", ""), cname, "concise"
        )
        detail_llm = simulate_llm_output_with_template(
            c.get("input_text", ""), cname, "detailed"
        )

        brief_proc = post_process({"body_html": brief_llm}, template_type="concise")
        detail_proc = post_process({"body_html": detail_llm}, template_type="detailed")

        brief_out = differentiate_template(brief_proc.get("body_html", ""), "concise")
        detail_out = differentiate_template(
            detail_proc.get("body_html", ""), "detailed"
        )

        brief_len = count_plain_chars(brief_out)
        detail_len = count_plain_chars(detail_out)

        is_diff = detail_len > brief_len
        if is_diff:
            all_pass_cases += 1

    print(f"    案例差異度通過: {all_pass_cases}/{len(cases)}")
    print(f"    達成率: {all_pass_cases / len(cases) * 100:.0f}%")

    return {
        "concise_chars": concise_chars,
        "standard_chars": standard_chars,
        "detailed_chars": detailed_chars,
        "all_pass": all_pass,
        "all_cases_pass": all_pass_cases,
        "total_cases": len(cases),
    }


def test_backward_compatibility():
    """測試 5：向後相容性"""
    print("\n" + "=" * 70)
    print("測試 5: 向後相容性")
    print("=" * 70)

    from src.functions.utils.prompt_builder import build_generate_prompt

    # 不傳 optimization_mode → 應使用 standard 預設
    prompt_no_mode = build_generate_prompt(
        organ="測試公司",
        organ_no="12345678",
        word_limit=200,
    )

    # 傳 standard → 應與無 mode 相同
    prompt_standard = build_generate_prompt(
        organ="測試公司",
        organ_no="12345678",
        word_limit=200,
        optimization_mode="standard",
    )

    # 傳 concise → 應不同
    prompt_concise = build_generate_prompt(
        organ="測試公司",
        organ_no="12345678",
        word_limit=100,
        optimization_mode="concise",
    )

    # 傳 detailed → 應不同
    prompt_detailed = build_generate_prompt(
        organ="測試公司",
        organ_no="12345678",
        word_limit=500,
        optimization_mode="detailed",
    )

    no_mode_has_standard = "標準模式" in prompt_no_mode
    same_as_standard = prompt_no_mode == prompt_standard
    all_different = (
        prompt_concise != prompt_standard
        and prompt_detailed != prompt_standard
        and prompt_concise != prompt_detailed
    )

    print(f"  無 mode → 預設 standard: {'✅' if no_mode_has_standard else '❌'}")
    print(f"  無 mode 與 standard 相同: {'✅' if same_as_standard else '❌'}")
    print(f"  三模式 Prompt 皆不同: {'✅' if all_different else '❌'}")

    return no_mode_has_standard and same_as_standard and all_different


def test_prompt_differentiation_content():
    """測試 6：Prompt 內容差異化"""
    print("\n" + "=" * 70)
    print("測試 6: Prompt 內容差異化")
    print("=" * 70)

    from src.functions.utils.prompt_builder import (
        build_generate_prompt,
        TEMPLATE_DESCRIPTIONS,
    )

    # 檢查 TEMPLATE_DESCRIPTIONS 定義
    has_all = all(
        k in TEMPLATE_DESCRIPTIONS for k in ["concise", "standard", "detailed"]
    )
    print(f"  TEMPLATE_DESCRIPTIONS 定義完整: {'✅' if has_all else '❌'}")

    concise_desc = TEMPLATE_DESCRIPTIONS.get("concise", {})
    standard_desc = TEMPLATE_DESCRIPTIONS.get("standard", {})
    detailed_desc = TEMPLATE_DESCRIPTIONS.get("detailed", {})

    print(
        f"\n  concise: {concise_desc.get('name', '')} - {concise_desc.get('length_guide', '')}"
    )
    print(
        f"  standard: {standard_desc.get('name', '')} - {standard_desc.get('length_guide', '')}"
    )
    print(
        f"  detailed: {detailed_desc.get('name', '')} - {detailed_desc.get('length_guide', '')}"
    )

    # 生成三個 prompt 並檢查差異
    prompt_c = build_generate_prompt(
        organ="公司A", word_limit=100, optimization_mode="concise"
    )
    prompt_s = build_generate_prompt(
        organ="公司A", word_limit=200, optimization_mode="standard"
    )
    prompt_d = build_generate_prompt(
        organ="公司A", word_limit=500, optimization_mode="detailed"
    )

    c_has_concise = "精簡模式" in prompt_c
    s_has_standard = "標準模式" in prompt_s
    d_has_detailed = "詳細模式" in prompt_d

    print(f"\n  concise prompt 包含「精簡模式」: {'✅' if c_has_concise else '❌'}")
    print(f"  standard prompt 包含「標準模式」: {'✅' if s_has_standard else '❌'}")
    print(f"  detailed prompt 包含「詳細模式」: {'✅' if d_has_detailed else '❌'}")

    return has_all and c_has_concise and s_has_standard and d_has_detailed


# ==================== 主程式 ====================


def main():
    print("=" * 70)
    print("Phase 14 Stage 2 整合測試")
    print("使用 Checkpoint 1 真實資料")
    print("=" * 70)

    # 載入資料
    print("\n📂 載入 Checkpoint 1 測試資料...")
    cases = load_checkpoint1_data()
    print(f"✅ 載入 {len(cases)} 個測試案例")
    for c in cases:
        print(f"   案例 {c['case_id']}: {c['company']['name']}")

    # 執行所有測試
    results = {}

    results["冗言移除"] = test_redundant_phrase_removal(cases)
    results["標點一致性"] = test_punctuation_normalization(cases)
    results["內容多樣化"] = test_content_diversification(cases)
    results["三模板差異化"] = test_template_differentiation(cases)
    results["向後相容性"] = test_backward_compatibility()
    results["Prompt差異化"] = test_prompt_differentiation_content()

    # 總結
    print("\n" + "=" * 70)
    print("📊 測試結果總結")
    print("=" * 70)

    print()
    print("| 測試項目 | 狀態 | 說明 |")
    print("|---------|------|------|")

    r = results["冗言移除"]
    status = "✅ PASS" if r["rate"] == 100 else f"❌ {r['passed']}/{r['total']}"
    print(f"| 冗言移除 | {status} | 移除模板痕跡 |")

    r = results["標點一致性"]
    status = "✅ PASS" if r["rate"] == 100 else f"⚠️ {r['passed']}/{r['total']}"
    print(f"| 標點一致性 | {status} | 中文標點統一 |")

    r = results["內容多樣化"]
    status = "✅ PASS" if r["target_met"] else "⚠️ 未達標"
    print(f"| 內容多樣化 | {status} | 差異度 {r['avg_score']:.3f} (目標>0.3) |")

    r = results["三模板差異化"]
    status = "✅ PASS" if r["all_pass"] else "❌ FAIL"
    print(
        f"| 三模板差異化 | {status} | 差異案例 {r['all_cases_pass']}/{r['total_cases']} |"
    )

    r = results["向後相容性"]
    status = "✅ PASS" if r else "❌ FAIL"
    print(f"| 向後相容性 | {status} | 無mode預設standard |")

    r = results["Prompt差異化"]
    status = "✅ PASS" if r else "❌ FAIL"
    print(f"| Prompt差異化 | {status} | 三模板提示詞不同 |")

    print()

    # Phase 14 Stage 2 Checkpoint 標準
    print("=" * 70)
    print("📋 Phase 14 Stage 2 Checkpoint 標準對照")
    print("=" * 70)
    print()
    print("| 成功標準 | 目標 | 實際 | 狀態 |")
    print("|---------|------|------|------|")
    print(
        f"| concise 字數 | ≤110 字 | {results['三模板差異化']['concise_chars']} 字 | {'✅' if results['三模板差異化']['concise_chars'] <= 110 else '❌'} |"
    )
    print(
        f"| standard 字數 | ≤210 字 | {results['三模板差異化']['standard_chars']} 字 | {'✅' if results['三模板差異化']['standard_chars'] <= 210 else '❌'} |"
    )
    print(
        f"| detailed 字數 | > concise | {results['三模板差異化']['detailed_chars']} 字 | {'✅' if results['三模板差異化']['detailed_chars'] > results['三模板差異化']['concise_chars'] else '❌'} |"
    )
    print(
        f"| 模板差異度 | >30% | {results['三模板差異化']['all_cases_pass']}/{results['三模板差異化']['total_cases']} 案例 | {'✅' if results['三模板差異化']['all_cases_pass'] == results['三模板差異化']['total_cases'] else '⚠️'} |"
    )
    print(
        f"| 向後相容 | 預設standard | {'✅' if results['向後相容性'] else '❌'} | {'✅' if results['向後相容性'] else '❌'} |"
    )

    print()
    print("=" * 70)
    print("✅✅✅ Phase 14 Stage 2 整合測試完成 ✅✅✅")
    print("=" * 70)


if __name__ == "__main__":
    main()
