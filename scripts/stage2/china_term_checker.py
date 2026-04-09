#!/usr/bin/env python3
"""
Phase 14 Stage 2 - 中國用語檢測與修正
========================================

功能:
  1. 檢測生成內容中的中國用語
  2. 提供台灣用語對照
  3. 評估中國用語嚴重程度

用法:
  python3 china_term_checker.py [--text "文本內容"] [--file 文件路徑]

輸出:
  - 檢測報告
  - 建議修正
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any

# 中國用語對照表
CHINA_TERMS_DICT = {
    # 網路/科技相關
    "網絡": "網路",
    "網站": "網站",
    "軟件": "軟體",
    "硬件": "硬體",
    "程序": "程式",
    "代碼": "代碼",
    "服務器": "伺服器",
    "網頁": "網頁",
    "鏈接": "連結",
    "絡": "路",
    # 商業/企業相關
    "公司": "公司",  # 中性詞，通常不需要改
    "企業": "企業",  # 中性詞
    "集團": "集團",
    "總部": "總部",
    "分公司": "分公司",
    "子公司": "子公司",
    # 時間相關
    "週": "週",  # 台灣也用
    "禮拜": "週",  # 口語化
    # 其他常見中國用語
    "質量": "品質",
    "價格": "價格",  # 中性
    "市場": "市場",  # 中性
    "客戶": "客戶",  # 中性
    "用戶": "使用者",  # 台灣較常用「使用者」
    "項目": "專案",  # 或「項目」，視語境
    "方案": "方案",  # 中性
    "系統": "系統",  # 中性
    "平臺": "平台",
    "信息": "資訊",
    "數據": "資料",
    # 動作相關
    "進行": "進行",  # 中性
    "開展": "展開",
    "推動": "推動",  # 中性
    "實施": "實施",  # 中性
    # 形容詞
    "優質": "優質",  # 中性
    "先進": "先進",  # 中性
    "專業": "專業",  # 中性
}

# 高風險中國用語（必須修正）
HIGH_RISK_TERMS = {
    "軟件": "軟體",
    "硬件": "硬體",
    "程序": "程式",
    "服務器": "伺服器",
    "絡": "路",
    "平臺": "平台",
    "信息": "資訊",
    "數據": "資料",
    "用戶": "使用者",
    "項目": "專案",
}

# 中國簡體字對照（如果系統誤用簡體）
SIMPLIFIED_TRADITIONAL = {
    "软": "軟",
    "硬": "硬",
    "件": "體",
    "程": "程",
    "序": "序",
    "码": "碼",
    "网": "網",
    "络": "絡",
    "链": "鏈",
    "结": "結",
    "构": "構",
    "设": "設",
    "计": "計",
    "务": "務",
    "气": "氣",
    "质": "質",
    "户": "戶",
    "备": "備",
}


class ChinaTermChecker:
    """中國用語檢測器"""

    def __init__(self):
        self.terms_dict = CHINA_TERMS_DICT
        self.high_risk_terms = HIGH_RISK_TERMS
        self.simplified_dict = SIMPLIFIED_TRADITIONAL

    def check_text(self, text: str) -> Dict[str, Any]:
        """
        檢測文本中的中國用語

        Returns:
            {
                "found_terms": List[Dict],  # 發現的用語列表
                "high_risk_count": int,      # 高風險用語數量
                "medium_risk_count": int,    # 中風險用語數量
                "simplified_chars": List,    # 簡體字列表
                "total_issues": int,         # 總問題數
                "risk_level": str,           # 風險等級
                "suggestions": List[str],    # 修正建議
            }
        """
        if not text:
            return {
                "found_terms": [],
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "simplified_chars": [],
                "total_issues": 0,
                "risk_level": "none",
                "suggestions": [],
            }

        found_terms = []
        high_risk_count = 0
        medium_risk_count = 0

        # 檢測中國用語
        for china_term, taiwan_term in self.terms_dict.items():
            if china_term in text:
                # 檢查是否為高風險
                is_high_risk = china_term in self.high_risk_terms

                # 計算出現次數
                count = text.count(china_term)

                term_info = {
                    "term": china_term,
                    "suggestion": taiwan_term,
                    "count": count,
                    "risk": "high" if is_high_risk else "medium",
                    "contexts": self._get_contexts(text, china_term),
                }

                found_terms.append(term_info)

                if is_high_risk:
                    high_risk_count += count
                else:
                    medium_risk_count += count

        # 檢測簡體字
        simplified_chars = self._check_simplified(text)

        # 計算總問題數
        total_issues = high_risk_count + medium_risk_count + len(simplified_chars)

        # 確定風險等級
        if high_risk_count > 0:
            risk_level = "high"
        elif medium_risk_count > 0 or len(simplified_chars) > 0:
            risk_level = "medium"
        else:
            risk_level = "none"

        # 生成建議
        suggestions = self._generate_suggestions(found_terms, simplified_chars)

        return {
            "found_terms": found_terms,
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "simplified_chars": simplified_chars,
            "total_issues": total_issues,
            "risk_level": risk_level,
            "suggestions": suggestions,
        }

    def _get_contexts(self, text: str, term: str, context_chars: int = 10) -> List[str]:
        """獲取包含該詞的上下文"""
        contexts = []
        start = 0

        while True:
            idx = text.find(term, start)
            if idx == -1:
                break

            # 提取上下文
            context_start = max(0, idx - context_chars)
            context_end = min(len(text), idx + len(term) + context_chars)
            context = text[context_start:context_end]

            contexts.append(context)
            start = idx + 1

        return contexts

    def _check_simplified(self, text: str) -> List[Dict]:
        """檢測簡體字"""
        found = []

        for char in text:
            if char in self.simplified_dict:
                found.append(
                    {
                        "char": char,
                        "traditional": self.simplified_dict[char],
                    }
                )

        return found

    def _generate_suggestions(
        self, found_terms: List[Dict], simplified_chars: List[Dict]
    ) -> List[str]:
        """生成修正建議"""
        suggestions = []

        # 中國用語建議
        for term_info in found_terms:
            if term_info["risk"] == "high":
                suggestions.append(
                    f"⚠️ 高風險: 將『{term_info['term']}』修正為『{term_info['suggestion']}』"
                    f"（出現 {term_info['count']} 次）"
                )
            else:
                suggestions.append(
                    f"💡 建議: 考慮將『{term_info['term']}』改為『{term_info['suggestion']}』"
                    f"（出現 {term_info['count']} 次）"
                )

        # 簡體字建議
        if simplified_chars:
            unique_simplified = set([item["char"] for item in simplified_chars])
            for char in unique_simplified:
                traditional = self.simplified_dict[char]
                suggestions.append(f"🔤 簡體字: 將『{char}』改為『{traditional}』")

        return suggestions

    def generate_report(
        self, check_result: Dict[str, Any], text_preview: str = ""
    ) -> str:
        """生成檢測報告"""
        lines = []
        lines.append("=" * 80)
        lines.append("中國用語檢測報告")
        lines.append("=" * 80)

        if text_preview:
            lines.append(f"\n文本預覽: {text_preview[:100]}...")

        lines.append(f"\n📊 檢測摘要")
        lines.append("-" * 80)
        lines.append(f"高風險用語: {check_result['high_risk_count']} 個")
        lines.append(f"中風險用語: {check_result['medium_risk_count']} 個")
        lines.append(f"簡體字: {len(check_result['simplified_chars'])} 個")
        lines.append(f"總問題數: {check_result['total_issues']} 個")

        # 風險等級
        risk_level = check_result["risk_level"]
        risk_icon = (
            "✅" if risk_level == "none" else "⚠️" if risk_level == "medium" else "❌"
        )
        lines.append(f"風險等級: {risk_icon} {risk_level.upper()}")

        # 詳細發現
        if check_result["found_terms"]:
            lines.append(f"\n🔍 發現的中國用語")
            lines.append("-" * 80)
            for term_info in check_result["found_terms"]:
                risk_icon = "❌" if term_info["risk"] == "high" else "⚠️"
                lines.append(
                    f"\n{risk_icon} {term_info['term']} → {term_info['suggestion']}"
                )
                lines.append(f"   出現次數: {term_info['count']}")
                lines.append(f"   風險等級: {term_info['risk']}")
                if term_info["contexts"]:
                    lines.append(f"   上下文: ...{term_info['contexts'][0]}...")

        # 簡體字
        if check_result["simplified_chars"]:
            lines.append(f"\n🔤 發現的簡體字")
            lines.append("-" * 80)
            unique = {}
            for item in check_result["simplified_chars"]:
                unique[item["char"]] = item["traditional"]
            for simp, trad in unique.items():
                lines.append(f"  {simp} → {trad}")

        # 修正建議
        if check_result["suggestions"]:
            lines.append(f"\n💡 修正建議")
            lines.append("-" * 80)
            for suggestion in check_result["suggestions"]:
                lines.append(f"  {suggestion}")
        else:
            lines.append(f"\n✅ 未發現中國用語問題！")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="中國用語檢測工具")
    parser.add_argument("--text", help="要檢測的文本")
    parser.add_argument("--file", help="要檢測的文件路徑")
    parser.add_argument("--json", action="store_true", help="輸出 JSON 格式")
    args = parser.parse_args()

    # 獲取文本
    text = ""
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        # 測試文本
        text = """
        這是一家專業的軟件開發公司，我們的服務器運行穩定。
        為客戶提供優質的信息服務，幫助用戶解決問題。
        我們的產品質量很好，價格合理。
        """

    # 檢測
    checker = ChinaTermChecker()
    result = checker.check_text(text)

    # 輸出結果
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(checker.generate_report(result, text[:200]))

    # 返回退出碼
    return 0 if result["risk_level"] == "none" else 1


if __name__ == "__main__":
    exit(main())
