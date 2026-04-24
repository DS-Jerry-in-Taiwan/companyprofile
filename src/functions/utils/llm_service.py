import os
import sys
import json
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

# ── 儲存層（惰性初始化，模組層級快取） ─────────────────
_storage_instance = None


def _get_storage():
    """惰性初始化儲存配接器（模組層級快取）"""
    global _storage_instance
    if _storage_instance is None:
        try:
            from src.storage.factory import StorageFactory

            config_path = os.path.join(
                PROJECT_ROOT, "config", "storage_config.json"
            )
            with open(config_path) as f:
                cfg = json.load(f)
            env = cfg.get("default", "development")
            storage_cfg = cfg["storage"][env]
            _storage_instance = StorageFactory.create(storage_cfg)
        except Exception as e:
            logger.warning(f"[Storage] 儲存初始化失敗，儲存功能已禁用: {e}")
            _storage_instance = None
    return _storage_instance


def _try_save_response(item: dict) -> None:
    """非同步儲存 LLM 回應到資料庫，不阻塞主流程"""
    storage = _get_storage()
    if storage is None:
        logger.warning("[Storage] 儲存未初始化，跳過寫入")
        return

    logger.info(
        f"[Storage] 非同步寫入 request_id={item.get('request_id')}, "
        f"template={item.get('prompt_template_name')}, "
        f"mode={item.get('mode')}"
    )

    def _do_save():
        try:
            storage.save_response(item)
            logger.info(f"[Storage] 寫入成功 request_id={item.get('request_id')}")
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


def get_llm_service():
    """取得 LLM Service 實例"""
    from src.services.llm_service import LLMService

    return LLMService()


def call_llm(
    prompt,
    word_limit=None,
    organ_no=None,
    mode="GENERATE",
    structure_key=None,
    opening_key=None,
    sentence_key=None,
    template_name=None,
) -> dict:
    """
    呼叫 LLM API 生成公司簡介（帶重試機制）

    Args:
        prompt: 公司資料 (dict) 或 prompt 字串 (str)
        word_limit: 字數限制（可選）
        organ_no: 統一編號（可選，用於儲存查詢）
        mode: 模式（預設 GENERATE）
        structure_key: 文章框架 key（Phase 23，可選）
        opening_key: 開頭情境 key（Phase 23，可選）
        sentence_key: 句型 key（Phase 23，可選）
        template_name: 模板名稱（可選）

    Returns:
        dict: 包含 title, body_html, summary 的字典
    """
    if LANGCHAIN_AVAILABLE:
        return _call_llm_with_retry(
            prompt, word_limit, organ_no, mode,
            structure_key, opening_key, sentence_key, template_name,
        )
    else:
        return _call_llm_original(
            prompt, word_limit, organ_no, mode,
            structure_key, opening_key, sentence_key, template_name,
        )


def _call_llm_with_retry(
    prompt, word_limit=None, organ_no=None, mode="GENERATE",
    structure_key=None, opening_key=None, sentence_key=None, template_name=None,
) -> dict:
    """使用重試機制的 LLM 呼叫"""
    from src.langchain.error_handlers import RetryableError, NonRetryableError

    try:
        retry_config = get_retry_config()

        @with_retry(retry_config, "llm_call")
        def llm_call_with_retry(inputs):
            # 解包 inputs 字典以支援裝飾器的單參數設計
            prompt_data = inputs.get("prompt")
            wl = inputs.get("word_limit")
            organ_no_val = inputs.get("organ_no")
            mode_val = inputs.get("mode", "GENERATE")
            sk = inputs.get("structure_key")
            ok = inputs.get("opening_key")
            sent_k = inputs.get("sentence_key")
            tn = inputs.get("template_name")
            return _call_llm_core(prompt_data, wl, organ_no_val, mode_val,
                                  sk, ok, sent_k, tn)

        # 將參數打包為字典傳遞給裝飾後的函數
        return llm_call_with_retry({
            "prompt": prompt,
            "word_limit": word_limit,
            "organ_no": organ_no,
            "mode": mode,
            "structure_key": structure_key,
            "opening_key": opening_key,
            "sentence_key": sentence_key,
            "template_name": template_name,
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
    prompt, word_limit=None, organ_no=None, mode="GENERATE",
    structure_key=None, opening_key=None, sentence_key=None, template_name=None,
) -> dict:
    """原始 LLM 呼叫邏輯"""
    try:
        return _call_llm_core(prompt, word_limit, organ_no, mode,
                              structure_key, opening_key, sentence_key, template_name)
    except Exception as e:
        logger.error(f"LLM API call failed: {str(e)}")
        return _get_default_response(prompt)


def _call_llm_core(
    prompt, word_limit=None, organ_no=None, mode="GENERATE",
    structure_key=None, opening_key=None, sentence_key=None, template_name=None,
) -> dict:
    """核心 LLM 呼叫邏輯 - 直接使用傳入的 Prompt（包含 Few-shot）"""
    try:
        from google.genai import types

        service = get_llm_service()

        # 動態計算 max_output_tokens
        # 公式：min(word_limit * 2, 4096)
        if word_limit:
            max_tokens = min(word_limit * 2, 4096)
        else:
            max_tokens = 4096

        # 計時開始
        _start = time.time()

        # 直接使用 service 的 Gemini API 呼叫，傳入我們的 prompt
        response = service.client.models.generate_content(
            model=service.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2, max_output_tokens=max_tokens
            ),
        )

        _elapsed_ms = int((time.time() - _start) * 1000)

# 獲取回應文字
        response_text = response.text.strip()

        # 嘗試解析為 JSON，並記錄解析結果
        parsed = None
        try:
            result = service._parse_response(response_text)
            parsed = result
        except (ValueError, Exception):
            logger.info(f"LLM 返回純文字回應，直接使用")

        # 總處理時間（API call + parsing）
        _duration_ms = int((time.time() - _start) * 1000)

        # ── 非同步儲存（不阻塞主流程） ────────────────
        _try_save_response({
            "request_id": str(uuid.uuid4()),
            "trace_id": str(uuid.uuid4()),
            "organ_no": organ_no or "",
            "mode": mode,
            "prompt_raw": str(prompt),
            "prompt_structure_key": structure_key,
            "prompt_opening_key": opening_key,
            "prompt_sentence_key": sentence_key,
            "prompt_template_name": template_name,
            "response_raw": response_text,
            "response_processed": parsed.model_dump_json() if parsed else None,
            "is_json": 1 if parsed else 0,
            "word_count": len(response_text.split()),
            "model": service.model_name,
            "tokens_used": (
                response.usage_metadata.total_token_count
                if response.usage_metadata else None
            ),
            "latency_ms": _elapsed_ms,
            "duration_ms": _duration_ms,
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
            # 從 prompt 中提取公司名稱
            company_name = "公司"
            if isinstance(prompt, str):
                for line in prompt.split("\n"):
                    if "公司名稱" in line:
                        parts = line.split("：")
                        if len(parts) > 1:
                            company_name = parts[1].strip()
                            break

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
