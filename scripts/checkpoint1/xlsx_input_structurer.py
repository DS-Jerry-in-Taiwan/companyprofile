#!/usr/bin/env python3
"""
1111 公司簡介測試數據 - Input 結構化腳本
================================================
將 Excel 測試數據轉換為標準化 Input 格式

使用方法:
  python3 xlsx_input_structurer.py

輸出:
  - test_inputs.json          (標準化測試輸入)
  - test_inputs_api.json      (API 測試格式)
  - test_summary.csv          (摘要表格)
"""

import pandas as pd
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import re


# ==================== 配置 ====================
class Config:
    INPUT_XLSX = Path(
        "/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1/1111_公司簡介生成優化.xlsx"
    )
    OUTPUT_DIR = Path(
        "/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1"
    )

    # 輸出文件
    OUTPUT_STANDARD = OUTPUT_DIR / "test_inputs.json"
    OUTPUT_API = OUTPUT_DIR / "test_inputs_api.json"
    OUTPUT_CSV = OUTPUT_DIR / "test_inputs_summary.csv"
    OUTPUT_MARKDOWN = OUTPUT_DIR / "test_inputs_report.md"


# ==================== 數據模型 ====================
class TestInput:
    """標準化測試輸入"""

    def __init__(self, case_id: int):
        self.case_id = case_id
        self.company_name: str = ""
        self.company_id: str = ""  # 統編
        self.industry_type: str = ""  # 產業類型
        self.industry_code: str = ""  # 產業代碼
        self.product_service: str = ""  # 產品/服務
        self.before_text: str = ""  # 原始公司簡介
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "company": {
                "name": self.company_name,
                "registration_id": self.company_id,
                "industry": {"type": self.industry_type, "code": self.industry_code},
            },
            "product_service": self.product_service,
            "input_text": self.before_text,
            "text_stats": {
                "char_count": len(self.before_text),
                "chinese_char_count": len(
                    re.findall(r"[\u4e00-\u9fff]", self.before_text)
                ),
                "line_count": len(self.before_text.split("\n")),
            },
            "metadata": self.metadata,
        }

    def to_api_format(self) -> Dict[str, Any]:
        """轉換為 API 請求格式 (符合 API 規範)"""
        return {
            "mode": "GENERATE",  # 必需: GENERATE
            "organ": self.company_name,  # 公司名稱
            "organNo": self.company_id,  # 統一編號 (必需)
            "brief": self.before_text,  # 公司簡介 (必需)
            "products": self.product_service,  # 產品/服務
            "trade": self.industry_type,  # 產業類型
            "optimization_mode": "STANDARD",  # 優化模式: STANDARD/CONCISE/DETAILED
            "word_limit": None,  # 字數限制 (可選)
        }


# ==================== Excel 解析器 ====================
class ExcelParser:
    """Excel 測試數據解析器"""

    def __init__(self, xlsx_path: Path):
        self.xlsx_path = xlsx_path
        self.df: Optional[pd.DataFrame] = None
        self.inputs: List[TestInput] = []

    def load(self) -> bool:
        """載入 Excel 文件"""
        try:
            self.df = pd.read_excel(self.xlsx_path)
            print(f"✅ Excel 載入成功: {len(self.df)} 行, {len(self.df.columns)} 欄位")
            return True
        except Exception as e:
            print(f"❌ Excel 載入失敗: {e}")
            return False

    def parse(self) -> List[TestInput]:
        """解析測試輸入數據"""
        if self.df is None:
            return []

        # 清理數據
        df = self.df.fillna("")

        current_input = None

        for idx, row in df.iterrows():
            # 檢查是否為新案例（案例欄位有值且非0）
            if row["案例"] != "" and row["案例"] != 0:
                # 解析公司信息（格式：公司名\n統編）
                company_info = str(row["廠商名稱 & 編號"]).split("\n")
                company_name = company_info[0].strip() if len(company_info) > 0 else ""
                company_id = company_info[1].strip() if len(company_info) > 1 else ""

                # 解析產業信息（格式：產業類型\n產業代碼）
                industry_info = str(row["產業類型 & 代碼"]).split("\n")
                industry_type = (
                    industry_info[0].strip() if len(industry_info) > 0 else ""
                )
                industry_code = (
                    industry_info[1].strip() if len(industry_info) > 1 else ""
                )

                # 創建新的 TestInput
                case_id = int(row["案例"])
                current_input = TestInput(case_id)
                current_input.company_name = company_name
                current_input.company_id = company_id
                current_input.industry_type = industry_type
                current_input.industry_code = industry_code
                current_input.product_service = str(row["產品/服務"]).strip()
                current_input.before_text = str(row["公司簡介 - before"]).strip()

                # 添加元數據
                current_input.metadata = {
                    "row_index": idx,
                    "excel_file": str(self.xlsx_path.name),
                }

                self.inputs.append(current_input)

        print(f"✅ 解析完成: {len(self.inputs)} 個測試輸入案例")
        return self.inputs

    def get_summary(self) -> Dict[str, Any]:
        """獲取數據摘要"""
        if not self.inputs:
            return {}

        total_chars = sum(len(inp.before_text) for inp in self.inputs)
        total_chinese = sum(
            len(re.findall(r"[\u4e00-\u9fff]", inp.before_text)) for inp in self.inputs
        )

        return {
            "total_cases": len(self.inputs),
            "companies": [inp.company_name for inp in self.inputs],
            "industries": list(set(inp.industry_type for inp in self.inputs)),
            "avg_text_length": total_chars / len(self.inputs) if self.inputs else 0,
            "avg_chinese_chars": total_chinese / len(self.inputs) if self.inputs else 0,
            "total_chinese_chars": total_chinese,
        }


# ==================== 報告生成器 ====================
def generate_reports(inputs: List[TestInput], summary: Dict[str, Any]):
    """生成各種格式的報告"""

    # 1. 標準 JSON 格式
    standard_output = {
        "document": "1111_公司簡介測試輸入",
        "generated_at": datetime.now().isoformat(),
        "source_file": str(Config.INPUT_XLSX.name),
        "summary": {
            "total_cases": len(inputs),
            "avg_text_length": summary.get("avg_text_length", 0),
            "avg_chinese_chars": summary.get("avg_chinese_chars", 0),
        },
        "test_inputs": [inp.to_dict() for inp in inputs],
    }

    with open(Config.OUTPUT_STANDARD, "w", encoding="utf-8") as f:
        json.dump(standard_output, f, ensure_ascii=False, indent=2)
    print(f"✅ 標準 JSON: {Config.OUTPUT_STANDARD}")

    # 2. API 測試格式
    api_output = {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "test_cases": [
            {"case_id": inp.case_id, "request": inp.to_api_format()} for inp in inputs
        ],
    }

    with open(Config.OUTPUT_API, "w", encoding="utf-8") as f:
        json.dump(api_output, f, ensure_ascii=False, indent=2)
    print(f"✅ API 格式 JSON: {Config.OUTPUT_API}")

    # 3. CSV 摘要
    with open(Config.OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "案例ID",
                "廠商名稱",
                "統編",
                "產業類型",
                "產業代碼",
                "產品服務摘要",
                "輸入字數",
                "中文字數",
            ]
        )

        for inp in inputs:
            chinese_count = len(re.findall(r"[\u4e00-\u9fff]", inp.before_text))
            product_summary = (
                inp.product_service[:30] + "..."
                if len(inp.product_service) > 30
                else inp.product_service
            )

            writer.writerow(
                [
                    inp.case_id,
                    inp.company_name,
                    inp.company_id,
                    inp.industry_type,
                    inp.industry_code,
                    product_summary,
                    len(inp.before_text),
                    chinese_count,
                ]
            )
    print(f"✅ CSV 摘要: {Config.OUTPUT_CSV}")

    # 4. Markdown 報告
    md_content = f"""# 1111 公司簡介測試輸入數據報告

## 📊 數據摘要

| 指標 | 數值 |
|------|------|
| 總案例數 | {len(inputs)} |
| 平均輸入長度 | {summary.get("avg_text_length", 0):.1f} 字符 |
| 平均中文字數 | {summary.get("avg_chinese_chars", 0):.1f} 字 |
| 總中文字數 | {summary.get("total_chinese_chars", 0)} 字 |

## 🏭 產業分佈

"""

    # 統計產業分佈
    industry_count = {}
    for inp in inputs:
        industry = inp.industry_type or "未知"
        industry_count[industry] = industry_count.get(industry, 0) + 1

    for industry, count in sorted(
        industry_count.items(), key=lambda x: x[1], reverse=True
    ):
        md_content += f"- {industry}: {count} 家\n"

    md_content += "\n## 📋 案例詳細列表\n\n"
    md_content += "| ID | 廠商名稱 | 統編 | 產業 | 輸入字數 |\n"
    md_content += "|----|----------|------|------|----------|\n"

    for inp in inputs:
        name = (
            inp.company_name[:20] + "..."
            if len(inp.company_name) > 20
            else inp.company_name
        )
        industry = (
            inp.industry_type[:10] + "..."
            if len(inp.industry_type) > 10
            else inp.industry_type
        )
        chinese_count = len(re.findall(r"[\u4e00-\u9fff]", inp.before_text))
        md_content += f"| {inp.case_id} | {name} | {inp.company_id} | {industry} | {chinese_count} |\n"

    md_content += """
## 📝 使用方式

### 1. 標準 JSON 格式
```python
import json

with open('test_inputs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
for case in data['test_inputs']:
    case_id = case['case_id']
    company_name = case['company']['name']
    input_text = case['input_text']
    # 進行測試...
```

### 2. API 測試格式
```python
import json

with open('test_inputs_api.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
for test_case in data['test_cases']:
    case_id = test_case['case_id']
    request_data = test_case['request']
    # 發送 API 請求...
    # response = requests.post(API_URL, json=request_data)
```

## 📁 輸出文件

1. **test_inputs.json** - 完整的標準化輸入數據
2. **test_inputs_api.json** - 適合 API 測試的格式
3. **test_inputs_summary.csv** - Excel 可讀的摘要表格

---

*Generated at: {datetime.now().isoformat()}*
"""

    with open(Config.OUTPUT_MARKDOWN, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"✅ Markdown 報告: {Config.OUTPUT_MARKDOWN}")


# ==================== 主程式 ====================
def main():
    print("=" * 70)
    print("1111 公司簡介測試數據 - Input 結構化工具")
    print("=" * 70)
    print()

    # 檢查輸入文件
    if not Config.INPUT_XLSX.exists():
        print(f"❌ 找不到輸入文件: {Config.INPUT_XLSX}")
        return 1

    # 初始化解析器
    parser = ExcelParser(Config.INPUT_XLSX)

    # 載入 Excel
    if not parser.load():
        return 1

    # 解析數據
    print("\n📋 正在解析測試輸入數據...")
    inputs = parser.parse()

    if not inputs:
        print("❌ 未找到有效的測試輸入數據")
        return 1

    # 獲取摘要
    summary = parser.get_summary()

    # 生成報告
    print("\n📝 正在生成報告...")
    generate_reports(inputs, summary)

    # 顯示摘要
    print("\n" + "=" * 70)
    print("📊 數據摘要")
    print("=" * 70)
    print(f"\n總案例數: {len(inputs)}")
    print(f"產業類別: {len(summary.get('industries', []))} 種")
    print(f"平均輸入長度: {summary.get('avg_text_length', 0):.1f} 字符")
    print(f"平均中文字數: {summary.get('avg_chinese_chars', 0):.1f} 字")

    print("\n📋 案例列表:")
    for inp in inputs:
        chinese_count = len(re.findall(r"[\u4e00-\u9fff]", inp.before_text))
        name = (
            inp.company_name[:25] + "..."
            if len(inp.company_name) > 25
            else inp.company_name
        )
        print(
            f"  Case {inp.case_id:2d}: {name:30} | {inp.industry_type[:15]:15} | {chinese_count:3d} 字"
        )

    print("\n" + "=" * 70)
    print("✅ 完成！輸出文件:")
    print("=" * 70)
    print(f"  📄 {Config.OUTPUT_STANDARD}")
    print(f"  📄 {Config.OUTPUT_API}")
    print(f"  📄 {Config.OUTPUT_CSV}")
    print(f"  📄 {Config.OUTPUT_MARKDOWN}")

    return 0


if __name__ == "__main__":
    exit(main())
