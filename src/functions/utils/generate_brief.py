# generate_brief.py
"""
Generate Brief Module
- 網頁搜尋、擷取、前處理、Prompt 組裝、呼叫 LLM
"""
from .web_search import web_search
from .web_scraper import extract_main_content
from .text_preprocessor import preprocess_text
from .prompt_builder import build_generate_prompt
from .llm_service import call_llm
from .post_processing import post_process
from .error_handler import ExternalServiceError

def generate_brief(data):
    company_url = data['companyUrl']
    organ = data['organ']

    # Step 1: query URL candidates (MVP fallback keeps direct url usage)
    url_candidates = web_search(organ, company_url)
    target_url = url_candidates[0] if url_candidates else company_url

    # Step 2: extract content from target URL
    try:
        raw_content = extract_main_content(target_url)
    except Exception as exc:
        raise ExternalServiceError('failed to fetch company website content') from exc

    # 3. 前處理
    clean_text = preprocess_text(raw_content)
    # 4. Prompt 組裝
    prompt = build_generate_prompt(organ, clean_text)
    # 5. 呼叫 LLM
    llm_result = call_llm(prompt)
    # 6. 後處理
    return post_process(llm_result)
