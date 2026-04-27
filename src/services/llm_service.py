import os
import json
import re
import uuid
import time
import logging
import threading
from datetime import datetime, timezone
from google import genai
from google.genai import types
from dotenv import load_dotenv
from src.schemas.llm_output import LLMOutput
from src.storage.factory import StorageFactory

load_dotenv()


class LLMService:
    def __init__(self):
        # 支援新舊環境變數
        api_key = os.getenv("GOOGLE_GENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_GENAI_API_KEY or GEMINI_API_KEY not found in environment variables"
            )

        self.client = genai.Client(api_key=api_key)

        # 從環境變數取得模型名稱，預設為 gemini-2.5-flash
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.model_name = model_name

        # 初始化存储层（惰性加载）
        self._storage = None

    def _get_storage(self):
        """惰性初始化存储适配器"""
        if self._storage is None:
            try:
                config_path = os.path.join(
                    os.path.dirname(__file__), "..", "..", "config", "storage_config.json"
                )
                with open(config_path) as f:
                    cfg = json.load(f)
                env = cfg.get("default", "development")
                storage_cfg = cfg["storage"][env]
                self._storage = StorageFactory.create(storage_cfg)
            except Exception as e:
                logging.getLogger(__name__).warning(
                    f"[Storage] 存储初始化失败，存储功能已禁用: {e}"
                )
                self._storage = None
        return self._storage

    def _load_template(self, template_path: str) -> str:
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Prompt 模板檔案不存在: {template_path} (cwd={os.getcwd()})"
            )
        except IOError as e:
            raise IOError(f"讀取 Prompt 模板失敗 {template_path}: {e}")

    def generate(self, company_data: dict, word_limit: int = None) -> LLMOutput:
        template = self._load_template("generate_prompt_template.txt")
        try:
            prompt = template.format(**company_data)
        except KeyError as e:
            raise ValueError(f"Prompt 模板缺少必要欄位: {e}")
        except Exception as e:
            raise ValueError(f"Prompt 格式化失敗: {type(e).__name__}: {str(e)}")

        # 動態計算 max_output_tokens
        # 公式：min(word_limit * 2, 4096)
        if word_limit:
            max_tokens = min(word_limit * 2, 4096)
        else:
            max_tokens = 4096

        _start = time.time()
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2, max_output_tokens=max_tokens
            ),
        )
        _elapsed_ms = int((time.time() - _start) * 1000)

        # 先解析，再存储（这样才能拿到 is_json 和 response_processed）
        parsed = None
        parse_error = None
        try:
            parsed = self._parse_response(response.text)
        except Exception as e:
            parse_error = e

        self._try_save_response({
            "trace_id": f"t-{uuid.uuid4().hex[:16]}",
            "organ_no": company_data.get("organ_no", ""),
            "organ_name": company_data.get("organ", ""),
            "company_url": company_data.get("company_url", ""),
            "mode": "GENERATE",
            "user_input": json.dumps(company_data.get("user_input"), ensure_ascii=False) if company_data.get("user_input") else None,
            "prompt_raw": prompt,
            "response_raw": response.text,
            "is_json": 1 if parsed else 0,
            "word_count": len(re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+|\d+', response.text)),
            "model": self.model_name,
            "tokens_used": (
                response.usage_metadata.total_token_count
                if response.usage_metadata else None
            ),
            "latency_ms": _elapsed_ms,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        if parsed is not None:
            return parsed
        raise parse_error  # type: ignore[misc]

    def optimize(
        self, original_brief: str, additional_data: dict, word_limit: int = None
    ) -> LLMOutput:
        template = self._load_template("optimize_prompt_template.txt")
        additional_data["original_brief"] = original_brief
        additional_data["additional_info"] = additional_data.get("description", "")
        try:
            prompt = template.format(**additional_data)
        except KeyError as e:
            raise ValueError(f"Prompt 模板缺少必要欄位: {e}")
        except Exception as e:
            raise ValueError(f"Prompt 格式化失敗: {type(e).__name__}: {str(e)}")

        # 動態計算 max_output_tokens
        # 公式：min(word_limit * 2, 4096)
        if word_limit:
            max_tokens = min(word_limit * 2, 4096)
        else:
            max_tokens = 4096

        _start = time.time()
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2, max_output_tokens=max_tokens
            ),
        )
        _elapsed_ms = int((time.time() - _start) * 1000)

        # 先解析，再存储（这样才能拿到 is_json 和 response_processed）
        parsed = None
        parse_error = None
        try:
            parsed = self._parse_response(response.text)
        except Exception as e:
            parse_error = e

        self._try_save_response({
            "trace_id": f"t-{uuid.uuid4().hex[:16]}",
            "organ_no": additional_data.get("organ_no", ""),
            "organ_name": additional_data.get("organ", ""),
            "company_url": additional_data.get("company_url", ""),
            "mode": "OPTIMIZE",
            "user_input": json.dumps(additional_data.get("user_input"), ensure_ascii=False) if additional_data.get("user_input") else None,
            "prompt_raw": prompt,
            "response_raw": response.text,
            "is_json": 1 if parsed else 0,
            "word_count": len(re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+|\d+', response.text)),
            "model": self.model_name,
            "tokens_used": (
                response.usage_metadata.total_token_count
                if response.usage_metadata else None
            ),
            "latency_ms": _elapsed_ms,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        if parsed is not None:
            return parsed
        raise parse_error  # type: ignore[misc]

    def _try_save_response(self, item: dict) -> None:
        """异步保存 LLM 响应到存储层，不阻塞主流程"""
        storage = self._get_storage()
        if storage is None:
            logger = logging.getLogger(__name__)
            logger.warning("[Storage] 存储未初始化，跳过保存")
            return
        # 丢到后台线程执行，主线程立即返回
        threading.Thread(
            target=self._do_save,
            args=(storage, item),
            daemon=True,
        ).start()

    def _do_save(self, storage, item: dict) -> None:
        """后台线程执行实际的存储写入"""
        logger = logging.getLogger(__name__)
        try:
            storage.save_response(item)
        except Exception as e:
            logger.warning(f"[Storage] 保存 LLM 响应失败: {e}")

    def _parse_response(self, text: str) -> LLMOutput:
        logger = logging.getLogger(__name__)

        json_str = text.strip()
        logger.debug(f"[DEBUG] Raw response: {json_str[:500]}")

        # 檢查是否為空回應
        if not json_str:
            raise ValueError("LLM returned empty response")

        # 檢查是否為空或非 JSON 回應
        if not json_str or "{" not in json_str:
            logger.warning(
                f"[Non-JSON Response] LLM 回應非 JSON 格式，長度: {len(json_str)}, 內容: {json_str[:500]}"
            )
            # 回應非 JSON，可能是 LLM 拒絕回答或其他情況
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
                # 如果找不到 JSON，可能是回應被截斷
                logger.warning(
                    f"[Non-JSON Response] 無法在回應中找到 JSON 區塊，內容: {json_str[:500]}"
                )
                raise ValueError(f"Invalid response format: {json_str[:100]}")

        logger.debug(f"[DEBUG] Parsed JSON string: {json_str[:200]}")

        # JSON 解析失敗時的 fallback 處理
        try:
            data = json.loads(json_str)
            return LLMOutput(**data)
        except json.JSONDecodeError as e:
            logger.warning(f"[Non-JSON Response] JSON 解析失敗: {e}, 嘗試修復...")
            # 嘗試修復常見的 JSON 格式問題
            fixed_json = self._try_fix_json(json_str)
            if fixed_json:
                try:
                    data = json.loads(fixed_json)
                    logger.info(f"[Non-JSON Response] JSON 修復成功")
                    return LLMOutput(**data)
                except json.JSONDecodeError:
                    pass
            raise ValueError(
                f"JSON parse failed after repair attempt: {json_str[:100]}"
            )

    def _try_fix_json(self, json_str: str) -> str:
        """嘗試修復常見的 JSON 格式問題"""
        import re

        # 移除結尾可能存在的多餘文字
        if '"' in json_str:
            # 找到最後一個完整的 JSON 屬性
            patterns = [
                r'\{[^{}]*"[^{}]*[}]*$',  # 簡單物件
            ]
            for pattern in patterns:
                match = re.search(pattern, json_str)
                if match:
                    return match.group(0)
        return None
