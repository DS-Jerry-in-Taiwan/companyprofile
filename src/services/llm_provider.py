"""
LLM Provider 抽象介面與實作

提供統一的 LLM 呼叫介面，支援 Gemini / Bedrock 等後端無痛切換。
Provider 選擇由 config/llm_config.json 控制，環境變數可覆蓋。

Typical usage:
    from src.services.llm_provider import get_llm_provider
    provider = get_llm_provider()
    result = provider.generate("你好")
    print(result.text)
"""

import os
import time
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, Protocol

logger = logging.getLogger(__name__)


# ===== Config 載入 =====


_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "config", "llm_config.json"
)


def _load_llm_config() -> dict:
    """讀取 LLM 配置檔 config/llm_config.json"""
    try:
        with open(_CONFIG_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"LLM config not found at {_CONFIG_PATH}, using defaults")
        return {"provider": "gemini", "gemini": {"model": "gemini-2.5-flash"}}
    except json.JSONDecodeError:
        logger.error(f"Invalid LLM config at {_CONFIG_PATH}, using defaults")
        return {"provider": "gemini", "gemini": {"model": "gemini-2.5-flash"}}


# ===== 資料類型 =====


@dataclass
class LLMResponse:
    """統一的 LLM 回傳格式"""

    text: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    model_name: str = ""
    latency_ms: float = 0.0


# ===== 抽象介面 =====


class LLMProvider(Protocol):
    """LLM Provider 抽象介面"""

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[list[str]] = None,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> LLMResponse:
        """純文字生成"""
        ...

    # generate_with_search 已移除（Phase 36: 搜尋與生成完全分離）
    # 搜尋階段固定由 search_config.json 控制，不經由 Provider


# ===== Gemini Provider =====


class GeminiProvider:
    """Gemini API Provider - 包裝現有 genai.Client 呼叫"""

    def __init__(self, config: dict = None):
        from google import genai
        from google.genai import types

        if config is None:
            config = _load_llm_config()
        gemini_cfg = config.get("gemini", {})

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiProvider")
        self._genai = genai
        self._types = types
        self.client = genai.Client(api_key=api_key)
        self.model = os.getenv("GEMINI_MODEL") or gemini_cfg.get("model", "gemini-2.5-flash")

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[list[str]] = None,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> LLMResponse:
        _start = time.time()

        # 從現有 Pydantic model 動態產生 response_schema，避免重複定義
        from src.schemas.llm_output import LLMOutput
        _llm_schema = LLMOutput.model_json_schema()

        # 建立 config，只有 system_instruction 有值時才加入
        config_kwargs = {
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "response_mime_type": "application/json",
            "response_schema": _llm_schema,
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self._types.GenerateContentConfig(**config_kwargs),
        )
        _elapsed = time.time() - _start
        raw = response.text
        if isinstance(raw, list):
            raw = " ".join([str(p) for p in raw])
        return LLMResponse(
            text=raw.strip() if raw else "",
            prompt_tokens=(
                response.usage_metadata.prompt_token_count
                if response.usage_metadata
                else None
            ),
            completion_tokens=(
                response.usage_metadata.candidates_token_count
                if response.usage_metadata
                else None
            ),
            model_name=self.model,
            latency_ms=int(_elapsed * 1000),
        )

    # generate_with_search 已移除（Phase 36）
    # 搜尋階段由 search_config.json 控制，不經由 Provider


# ===== Bedrock Provider =====


class BedrockProvider:
    """AWS Bedrock Provider - 使用 Amazon Nova 模型"""

    MODEL_IDS = {
        "nova-micro": "amazon.nova-micro-v1:0",
        "nova-lite": "amazon.nova-lite-v1:0",
        "nova-pro": "amazon.nova-pro-v1:0",
    }

    def __init__(self, config: dict = None):
        import boto3

        if config is None:
            config = _load_llm_config()
        bedrock_cfg = config.get("bedrock", {})

        self.model_key = os.getenv("BEDROCK_MODEL") or bedrock_cfg.get("model", "nova-lite")
        self.model_id = self.MODEL_IDS.get(self.model_key, self.model_key)
        region = bedrock_cfg.get("region", "ap-northeast-1")
        self.client = boto3.client("bedrock-runtime", region_name=region)

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[list[str]] = None,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> LLMResponse:
        _start = time.time()

        # Amazon Nova Messages API 格式
        body = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            "inferenceConfig": {
                "max_new_tokens": max_output_tokens,
                "temperature": temperature,
            },
        })

        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        _elapsed = time.time() - _start
        result = json.loads(response["body"].read())

        text = result["output"]["message"]["content"][0]["text"]
        usage = result.get("usage", {})
        input_tokens = usage.get("inputTokens", 0)
        output_tokens = usage.get("outputTokens", 0)

        return LLMResponse(
            text=text,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            model_name=self.model_id,
            latency_ms=int(_elapsed * 1000),
        )

    # generate_with_search 已移除（Phase 36）
    # 搜尋階段由 search_config.json 控制，不經由 Provider


# ===== 工廠函數 =====

_provider = None


def get_llm_provider() -> LLMProvider:
    """取得 LLM Provider 實例（優先使用環境變數，其次 config 檔）"""
    global _provider
    if _provider is not None:
        return _provider
    
    config = _load_llm_config()
    
    # 環境變數優先（用於 Lambda 臨時覆蓋）
    provider_type = os.getenv("LLM_PROVIDER") or config.get("provider", "gemini")
    provider_type = provider_type.lower()
    
    logger.info(f"[LLMProvider] 初始化 Provider: {provider_type}")
    if provider_type == "bedrock":
        _provider = BedrockProvider(config=config)
    else:
        _provider = GeminiProvider(config=config)
    return _provider


def reset_llm_provider():
    """重置 Provider（測試用）"""
    global _provider
    _provider = None
