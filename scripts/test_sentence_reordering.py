#!/usr/bin/env python3
"""
測試句子重組功能
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.functions.utils.content_diversifier import diversify_content
import re
import random


def test_sentence_reordering():
    """測試句子重組功能"""
    print("🔄 句子重組功能測試")
    print("=" * 60)

    # 測試純文本
    test_text = (
        "本公司成立於2020年。我們專注於AI技術研發。團隊擁有豐富經驗。客戶包括多家企業。"
    )

    print(f"原始文本: {test_text}")
    print()

    # 手動測試句子重組邏輯
    sentences = re.split(r"([。！？])", test_text)
    print(f"句子分割結果: {sentences}")
    print()

    # 將句子和標點配對
    sentence_pairs = []
    for i in range(0, len(sentences) - 1, 2):
        if sentences[i].strip():
            sentence_pairs.append(
                (
                    sentences[i].strip(),
                    sentences[i + 1] if i + 1 < len(sentences) else "",
                )
            )

    print(f"句子配對: {sentence_pairs}")
    print()

    # 測試重組
    if len(sentence_pairs) >= 3:
        first_sentence = sentence_pairs[0]
        other_sentences = sentence_pairs[1:]
        random.shuffle(other_sentences)
        shuffled_pairs = [first_sentence] + other_sentences

        print("重組後句子順序:")
        for i, (sentence, punct) in enumerate(shuffled_pairs):
            print(f"  句子{i + 1}: {sentence}{punct}")

        # 重新組合
        result = "".join([sentence + punct for sentence, punct in shuffled_pairs])
        print()
        print(f"重組結果: {result}")

    # 測試HTML內容
    print()
    print("🔧 測試HTML內容處理:")
    html_content = "<p>本公司成立於2020年。</p><p>我們專注於AI技術研發。</p><p>團隊擁有豐富經驗。</p><p>客戶包括多家企業。</p>"

    print(f"原始HTML: {html_content}")

    # 多次運行看變化
    print()
    print("多次運行結果:")
    for i in range(3):
        result = diversify_content(html_content)
        print(f"  運行{i + 1}: {result}")

    return True


if __name__ == "__main__":
    test_sentence_reordering()
