# prompt_builder.py
"""
Prompt Builder
- 組裝 LLM Prompt
"""
def build_generate_prompt(organ, content):
    return f"請根據以下內容為 {organ} 生成公司簡介：\n{content}"

def build_optimize_prompt(organ, brief):
    return f"請優化 {organ} 的公司簡介如下：\n{brief}"
