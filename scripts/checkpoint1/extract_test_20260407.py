#!/usr/bin/env python3
"""
test_20260407 結構化提取腳本 v5
使用 PyMuPDF 進行精確解析
"""

import json
import re
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import fitz

INPUT_PDF = Path("/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1/test_20260407.pdf")
OUTPUT_DIR = Path("/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1")

def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text.replace('\n', ' ')).strip()

def count_chinese_chars(text: Optional[str]) -> int:
    if not text:
        return 0
    return len(re.findall(r'[\u4e00-\u9fff]', text))

def extract_cases_from_pdf(pdf_path: Path) -> List[Dict]:
    cases = []
    
    with fitz.open(pdf_path) as doc:
        print(f"PDF 共 {len(doc)} 頁")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("blocks")
            current_case = None
            
            for block in blocks:
                x0, y0, x1, y1, text, block_no, block_type = block
                text = text.strip()
                if not text:
                    continue
                
                # 跳過表頭
                if any(h in text for h in ['Case', 'Before', 'After', '廠商名', '公司簡介']):
                    if len(text) < 40:
                        continue
                
                # 左欄: 元數據
                if x0 < 150:
                    clean = clean_text(text)
                    if re.match(r'^\d+\s', clean):
                        case_id = int(clean.split()[0])
                        current_case = {
                            'case_id': case_id,
                            'company_name': None,
                            'company_id': None,
                            'model_type': None,
                            'word_limit': None,
                            'advanced_settings': None,
                            'before_text': '',
                            'after_text': '',
                            'pages': [page_num + 1]
                        }
                        cases.append(current_case)
                        
                        # 提取信息
                        company_match = re.search(r'([\u4e00-\u9fff]{2,}(?:\([^)]+\))?)(?=\s*\d{6})', clean)
                        if company_match:
                            current_case['company_name'] = company_match.group(1).replace(' ', '')
                        
                        id_match = re.search(r'(\d{6})', clean)
                        if id_match:
                            current_case['company_id'] = id_match.group(1)
                        
                        limit_match = re.search(r'\d{6}\s+(\d{2,3})', clean)
                        if limit_match:
                            current_case['word_limit'] = int(limit_match.group(1))
                        
                        model_match = re.search(r'(標準|精簡|詳細)', clean)
                        if model_match:
                            current_case['model_type'] = model_match.group(1)
                        
                        if '有' in clean:
                            current_case['advanced_settings'] = '有'
                        elif '無' in clean:
                            current_case['advanced_settings'] = '無'
                
                # 中間欄: Before 文本
                elif 150 <= x0 < 350 and current_case:
                    current_case['before_text'] += text + '\n'
                
                # 右欄: After 文本
                elif x0 >= 350 and current_case:
                    current_case['after_text'] += text + '\n'
    
    return cases

def generate_reports(cases: List[Dict]):
    for case in cases:
        case['before_count'] = count_chinese_chars(case['before_text'])
        case['after_count'] = count_chinese_chars(case['after_text'])
    
    # JSON
    output = {
        "document": "test_20260407",
        "generated_at": datetime.now().isoformat(),
        "total_cases": len(cases),
        "cases": cases
    }
    json_path = OUTPUT_DIR / "test_20260407_structured.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"JSON: {json_path}")
    
    # CSV
    csv_path = OUTPUT_DIR / "test_20260407_cases.csv"
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['案例ID', '廠商名稱', '統編', '模型', '字數限制', 
                         '進階設定', 'Before字數', 'After字數', '頁面'])
        for case in cases:
            writer.writerow([
                case['case_id'],
                case['company_name'] or '',
                case['company_id'] or '',
                case['model_type'] or '',
                case['word_limit'] or '',
                case['advanced_settings'] or '',
                case['before_count'],
                case['after_count'],
                ','.join(map(str, case['pages']))
            ])
    print(f"CSV: {csv_path}")
    
    # Markdown
    md_path = OUTPUT_DIR / "extraction_report.md"
    lines = ["# test_20260407 結構化提取報告", "", "## 摘要", "",
             f"| 指標 | 數值 |", "|------|------|",
             f"| 總案例數 | {len(cases)} |",
             f"| 完整案例 | {sum(1 for c in cases if c['company_name'] and c['company_id'])} |",
             "", "## 案例列表", "",
             "| ID | 廠商名稱 | 統編 | 模型 | 字數 | Before | After |",
             "|----|----------|------|------|------|--------|-------|"]
    
    for case in cases:
        name = (case['company_name'] or 'N/A')[:15]
        lines.append(f"| {case['case_id']:2d} | {name} | {case['company_id'] or 'N/A'} | "
                     f"{case['model_type'] or '?'} | {case['word_limit'] or '?'} | "
                     f"{case['before_count']} | {case['after_count']} |")
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"Markdown: {md_path}")

def main():
    print("=" * 60)
    print("test_20260407 結構化提取 v5 (PyMuPDF)")
    print("=" * 60)
    
    cases = extract_cases_from_pdf(INPUT_PDF)
    print(f"\n提取完成: {len(cases)} 個案例")
    
    generate_reports(cases)
    
    print("\n" + "=" * 60)
    print("摘要")
    print("=" * 60)
    for case in cases:
        name = (case['company_name'] or '未知')[:20]
        print(f"Case {case['case_id']:2d}: {name:22} | "
              f"B:{case.get('before_count', 0):4d} | A:{case.get('after_count', 0):4d}")
    
    print(f"\n報告已保存")

if __name__ == "__main__":
    main()
