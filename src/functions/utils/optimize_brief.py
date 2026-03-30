# optimize_brief.py
"""
Optimize Brief Module
- 組裝優化 Prompt，呼叫 LLM
"""
from .prompt_builder import build_optimize_prompt
from .llm_service import call_llm
from .post_processing import post_process

def optimize_brief(data):
    organ = data['organ']
    organ_no = data['organNo']
    brief = data['brief']
    prompt = build_optimize_prompt(organ, brief)
    llm_result = call_llm(prompt)
    return post_process(llm_result)
