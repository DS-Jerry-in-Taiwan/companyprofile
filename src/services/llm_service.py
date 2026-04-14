import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from src.schemas.llm_output import LLMOutput

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

    def _load_template(self, template_path: str) -> str:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()

    def generate(self, company_data: dict, word_limit: int = None) -> LLMOutput:
        template = self._load_template("generate_prompt_template.txt")
        prompt = template.format(**company_data)

        # 動態計算 max_output_tokens
        # 公式：min(word_limit * 2, 4096)
        if word_limit:
            max_tokens = min(word_limit * 2, 4096)
        else:
            max_tokens = 4096

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2, max_output_tokens=max_tokens
            ),
        )
        return self._parse_response(response.text)

    def optimize(
        self, original_brief: str, additional_data: dict, word_limit: int = None
    ) -> LLMOutput:
        template = self._load_template("optimize_prompt_template.txt")
        additional_data["original_brief"] = original_brief
        additional_data["additional_info"] = additional_data.get("description", "")
        prompt = template.format(**additional_data)

        # 動態計算 max_output_tokens
        # 公式：min(word_limit * 2, 4096)
        if word_limit:
            max_tokens = min(word_limit * 2, 4096)
        else:
            max_tokens = 4096

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2, max_output_tokens=max_tokens
            ),
        )
        return self._parse_response(response.text)

    def _parse_response(self, text: str) -> LLMOutput:
        import logging

        logger = logging.getLogger(__name__)

        json_str = text.strip()
        print(f"[DEBUG] Raw response:\n{json_str[:500]}\n")  # 限制輸出長度

        # 檢查是否為空回應
        if not json_str:
            raise ValueError("LLM returned empty response")

        # 檢查是否為空或非 JSON 回應
        if not json_str or "{" not in json_str:
            logger.warning(
                f"[Non-JSON Response] LLM 回應非 JSON 格式，長度: {len(json_str)}, 前200字: {json_str[:200]}"
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
                    f"[Non-JSON Response] 無法在回應中找到 JSON 區塊，嘗試提取的內容: {json_str[:200]}"
                )
                raise ValueError(f"Invalid response format: {json_str[:100]}")

        print(f"[DEBUG] Parsed JSON string:\n{json_str[:200]}...\n")

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
