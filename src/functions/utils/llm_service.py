import os
import sys
import json
import re
import uuid
import time
import threading
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging

# 確保 src 目錄在 Python 路徑中
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv()

logger = logging.getLogger(__name__)

# ── 儲存層：從全域入口取得 ──────────────────────────


def _get_storage():
    """從全域入口取得 storage instance（不再自己初始化）"""
    try:
        from src.storage import get_storage
        return get_storage()
    except Exception as e:
        logger.warning(f"[Storage] 取得 storage 失敗: {e}")
        return None


def _try_save_response(item: dict) -> None:
    """非同步儲存 LLM 回應到資料庫，不阻塞主流程"""
    storage = _get_storage()
    if storage is None:
        logger.warning("[Storage] 儲存未初始化，跳過寫入")
        return

    logger.info(
        f"[Storage] 非同步寫入 trace_id={item.get('trace_id')}, "
        f"template={item.get('prompt_template_name')}, "
        f"mode={item.get('mode')}"
    )

    def _do_save():
        try:
            storage.save_response(item)
            logger.info(f"[Storage] 寫入成功 trace_id={item.get('trace_id')}")
        except Exception as e:
            logger.warning(f"[Storage] 儲存 LLM 回應失敗: {e}")

    threading.Thread(target=_do_save, daemon=True).start()


# ─────────────────────────────────────────────────────

# 嘗試導入 LangChain 錯誤處理
try:
    from src.langchain.error_handlers import with_retry, RetryableError
    from src.langchain.retry_config import get_retry_config

    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangChain error handling not available: {e}")
    LANGCHAIN_AVAILABLE = False


def _parse_response(text: str):
    """解析 LLM 回傳的文字，提取 JSON 轉為 dict（原 LLMService._parse_response）
    
    Args:
        text: LLM 回傳的原始文字（可能含 ```json 標記）
    
    Returns:
        dict: 解析後的結構化輸出（含 title, body_html, summary 等欄位）
    
    Raises:
        ValueError: 無法解析為有效 JSON
    """
    from src.schemas.llm_output import LLMOutput

    json_str = text.strip()
    if not json_str:
        raise ValueError("LLM returned empty response")

    if "{" not in json_str:
        logger.warning(
            f"[Non-JSON Response] LLM 回應非 JSON 格式，長度: {len(json_str)}"
        )
        raise ValueError(f"LLM did not return valid JSON: {json_str[:100]}")

    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0].strip()
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0].strip()
    else:
        start = json_str.find("{")
        end = json_str.rfind("}") + 1
        if start != -1 and end > start:
            json_str = json_str[start:end]
        else:
            logger.warning(
                f"[Non-JSON Response] 無法在回應中找到 JSON 區塊，內容: {json_str[:500]}"
            )
            raise ValueError(f"Invalid response format: {json_str[:100]}")

    try:
        data = json.loads(json_str)
        return LLMOutput(**data)
    except json.JSONDecodeError as e:
        logger.warning(f"[Non-JSON Response] JSON 解析失敗: {e}, 嘗試修復...")
        fixed_json = _try_fix_json(json_str)
        if fixed_json:
            try:
                data = json.loads(fixed_json)
                logger.info(f"[Non-JSON Response] JSON 修復成功")
                return LLMOutput(**data)
            except json.JSONDecodeError:
                pass
        raise ValueError(f"JSON parse failed after repair attempt: {json_str[:100]}")


def _try_fix_json(json_str: str) -> str:
    """嘗試修復常見的 JSON 格式問題（原 LLMService._try_fix_json）"""
    import re

    if '"' in json_str:
        patterns = [
            r'\{[^{}]*"[^{}]*[}]*$',
        ]
        for pattern in patterns:
            match = re.search(pattern, json_str)
            if match:
                return match.group(0)
    return None


def _extract_company_name(prompt) -> str:
    """從 prompt 字串中提取公司名稱"""
    company_name = "公司"
    if isinstance(prompt, str):
        for line in prompt.split("\n"):
            if "公司名稱" in line:
                parts = line.split("：")
                if len(parts) > 1:
                    company_name = parts[1].strip()
                    break
    return company_name


def call_llm(
    prompt,
    organ_no=None,
    organ=None,
    user_input=None,
    mode="GENERATE",
    structure_key=None,
    opening_key=None,
    sentence_key=None,
    template_name=None,
    fewshot_styles=None,
    search_tokens=None,
) -> dict:
    """
    呼叫 LLM API 生成公司簡介（帶重試機制）

    Args:
        prompt: 公司資料 (dict) 或 prompt 字串 (str)
        organ_no: 統一編號（可選，用於儲存查詢）
        organ: 公司名稱（可選，用於儲存）
        user_input: 使用者輸入資料（可選，用於儲存）
        mode: 模式（預設 GENERATE）
        structure_key: 文章框架 key（Phase 23，可選）
        opening_key: 開頭情境 key（Phase 23，可選）
        sentence_key: 句型 key（Phase 23，可選）
        template_name: 模板名稱（可選）
        fewshot_styles: 選取的模組化範例風格（Phase 32，可選）
        search_tokens: 搜尋階段的 token 用量 dict（Phase 33，可選）

    Returns:
        dict: 包含 title, body_html, summary 的字典
    """
    if LANGCHAIN_AVAILABLE:
        return _call_llm_with_retry(
            prompt, organ_no, organ, user_input, mode,
            structure_key, opening_key, sentence_key, template_name,
            fewshot_styles=fewshot_styles, search_tokens=search_tokens,
        )
    else:
        return _call_llm_original(
            prompt, organ_no, organ, user_input, mode,
            structure_key, opening_key, sentence_key, template_name,
            fewshot_styles=fewshot_styles, search_tokens=search_tokens,
        )


def _call_llm_with_retry(
    prompt, organ_no=None, organ=None, user_input=None, mode="GENERATE",
    structure_key=None, opening_key=None, sentence_key=None, template_name=None,
    fewshot_styles=None, search_tokens=None, system_instruction=None,
) -> dict:
    """使用重試機制的 LLM 呼叫"""
    from src.langchain.error_handlers import RetryableError, NonRetryableError

    try:
        retry_config = get_retry_config()

        @with_retry(retry_config, "llm_call")
        def llm_call_with_retry(inputs):
            # 解包 inputs 字典以支援裝飾器的單參數設計
            prompt_data = inputs.get("prompt")
            organ_no_val = inputs.get("organ_no")
            organ_val = inputs.get("organ")
            user_input_val = inputs.get("user_input")
            mode_val = inputs.get("mode", "GENERATE")
            sk = inputs.get("structure_key")
            ok = inputs.get("opening_key")
            sent_k = inputs.get("sentence_key")
            tn = inputs.get("template_name")
            fs = inputs.get("fewshot_styles")
            st = inputs.get("search_tokens")
            si = inputs.get("system_instruction")
            return _call_llm_core(prompt_data, organ_no_val, organ_val, user_input_val, mode_val,
                                  sk, ok, sent_k, tn, fewshot_styles=fs, search_tokens=st,
                                  system_instruction=si)

        # 將參數打包為字典傳遞給裝飾後的函數
        return llm_call_with_retry({
            "prompt": prompt,
            "organ_no": organ_no,
            "organ": organ,
            "user_input": user_input,
            "mode": mode,
            "structure_key": structure_key,
            "opening_key": opening_key,
            "sentence_key": sentence_key,
            "template_name": template_name,
            "fewshot_styles": fewshot_styles,
            "search_tokens": search_tokens,
            "system_instruction": system_instruction,
        })

    except NonRetryableError as e:
        # 不可重試的錯誤，直接上拋
        logger.error(f"LLM call failed (non-retryable): {e.error_type} - {str(e)}")
        raise
    except RetryableError as e:
        # 可重試的錯誤，但已用盡重試次數
        logger.error(f"LLM call failed (retryable, exhausted): {e.error_type} - {str(e)}")
        raise
    except Exception as e:
        # 未知錯誤，不應該吃掉的異常
        logger.error(f"LLM call failed (unexpected): {type(e).__name__} - {str(e)}")
        from src.langchain.error_handlers import NonRetryableError
        from src.functions.utils.error_handler import ErrorCode
        raise NonRetryableError(f"Unexpected LLM error: {type(e).__name__}", ErrorCode.LLM_008.code, e)


def _call_llm_original(
    prompt, organ_no=None, organ=None, user_input=None, mode="GENERATE",
    structure_key=None, opening_key=None, sentence_key=None, template_name=None,
    fewshot_styles=None, search_tokens=None, system_instruction=None,
) -> dict:
    """原始 LLM 呼叫邏輯"""
    try:
        return _call_llm_core(prompt, organ_no, organ, user_input, mode,
                              structure_key, opening_key, sentence_key, template_name,
                              fewshot_styles=fewshot_styles, search_tokens=search_tokens,
                              system_instruction=system_instruction)
    except Exception as e:
        logger.error(f"LLM API call failed: {str(e)}")
        return _get_default_response(prompt)


def _call_llm_core(
    prompt, organ_no=None, organ=None, user_input=None, mode="GENERATE",
    structure_key=None, opening_key=None, sentence_key=None, template_name=None,
    fewshot_styles=None, search_tokens=None, system_instruction=None,
) -> dict:
    """核心 LLM 呼叫邏輯 - 直接使用傳入的 Prompt（包含 Few-shot）"""
    try:
        from src.services.llm_provider import get_llm_provider

        # 使用預設的 max_output_tokens
        max_tokens = 4096

        # Phase 39: system_instruction 由 caller (llm_service) 提供，不再寫死在 provider
        if system_instruction is None:
            system_instruction = [
                "你是一個公司簡介作者。",
                "只輸出最終結果，不要輸出任何推理過程、檢查過程或驗證說明。",
            ]

        # 透過 Provider 呼叫 LLM
        provider = get_llm_provider()
        result = provider.generate(
            prompt,
            system_instruction=system_instruction,
            temperature=0.2,
            max_output_tokens=max_tokens,
        )

        response_text = result.text
        _elapsed_ms = int(result.latency_ms)

        # 嘗試解析為 JSON，並記錄解析結果
        parsed = None
        provider_name = type(provider).__name__
        if provider_name == "GeminiProvider":
            # response_schema 確保 JSON，直接解析
            from src.schemas.llm_output import LLMOutput
            try:
                data = json.loads(response_text)
                parsed = LLMOutput(**data)
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Gemini structured output 解析失敗（不應發生）: {e}")
                parsed = None
        else:
            # Bedrock: 保留現有 _parse_response 路徑
            try:
                parsed = _parse_response(response_text)
            except (ValueError, Exception):
                logger.info("LLM 返回非 JSON，使用純文字回退")

        # ── 非同步儲存（不阻塞主流程） ────────────────
        # 序列化 user_input 為 JSON 字串
        user_input_str = json.dumps(user_input, ensure_ascii=False) if user_input else None

        # Phase 33: 合併搜尋階段的 token 用量
        _search_tk = search_tokens or {}

        _try_save_response({
            "trace_id": f"t-{uuid.uuid4().hex[:16]}",
            "organ_no": organ_no or "",
            "organ_name": organ or "",
            "company_url": "",
            "mode": "GENERATE",  # 統一為 GENERATE，搜尋 token 合併在此
            "user_input": user_input_str,
            "prompt_raw": str(prompt),
            "prompt_structure_key": structure_key,
            "prompt_opening_key": opening_key,
            "prompt_sentence_key": sentence_key,
            "prompt_template_name": template_name,
            "prompt_fewshot_styles": fewshot_styles,
            "optimization_mode": template_name,
            "response_raw": response_text,
            "is_json": 1 if parsed else 0,
            "word_count": len(re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+|\d+', response_text)),
            "model": result.model_name,
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            # 搜尋階段 token（合併在同一筆）
            "search_prompt_tokens": _search_tk.get("prompt"),
            "search_completion_tokens": _search_tk.get("completion"),
            "search_model": _search_tk.get("model"),
            "search_latency_ms": _search_tk.get("latency_ms"),
            # 整筆請求總耗時 = (搜尋+摘要時間) + 生成 API 時間
            "total_latency_ms": (_search_tk.get("total_latency_ms") or 0) + _elapsed_ms,
            "latency_ms": _elapsed_ms,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        # ──────────────────────────────────────────────

        # 回傳解析結果或 fallback
        if parsed:
            return {
                "title": parsed.title,
                "body_html": parsed.body_html,
                "summary": parsed.summary,
            }
        else:
            company_name = _extract_company_name(prompt)
            return {
                "title": f"{company_name} - 企業簡介",
                "body_html": f"<p>{response_text}</p>",
                "summary": response_text[:100] + "..."
                if len(response_text) > 100
                else response_text,
            }

    except Exception as e:
        if LANGCHAIN_AVAILABLE:
            # 將錯誤包裝為可重試的錯誤
            raise RetryableError(f"LLM API call failed: {str(e)}", "LLMError", e)
        else:
            raise RuntimeError(f"LLM API call failed: {str(e)}")


def _get_default_response(prompt) -> dict:
    """當所有重試都失敗時的預設回應"""
    company_name = "公司"

    if isinstance(prompt, str):
        # 嘗試從字串中提取公司名稱
        lines = prompt.split("\n")
        for line in lines:
            if "公司名稱" in line or "company_name" in line.lower():
                parts = line.split("：") or line.split(":")
                if len(parts) > 1:
                    company_name = parts[1].strip()
                    break
    elif isinstance(prompt, dict):
        company_name = prompt.get("company_name", prompt.get("organ", "公司"))

    logger.warning(f"返回 {company_name} 的預設回應")

    return {
        "title": f"{company_name} - 企業簡介",
        "body_html": f"<p>{company_name} 是一家專業的企業，致力於提供優質的產品和服務。</p>",
        "summary": f"{company_name} - 專業企業，提供優質產品和服務。",
    }
