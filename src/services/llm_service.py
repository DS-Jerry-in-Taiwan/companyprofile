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

    def generate(self, company_data: dict) -> LLMOutput:
        template = self._load_template("generate_prompt_template.txt")
        prompt = template.format(**company_data)
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=4096),
        )
        return self._parse_response(response.text)

    def optimize(self, original_brief: str, additional_data: dict) -> LLMOutput:
        template = self._load_template("optimize_prompt_template.txt")
        additional_data["original_brief"] = original_brief
        additional_data["additional_info"] = additional_data.get("description", "")
        prompt = template.format(**additional_data)
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=4096),
        )
        return self._parse_response(response.text)

    def _parse_response(self, text: str) -> LLMOutput:
        json_str = text.strip()
        print(f"[DEBUG] Raw response:\n{json_str[:500]}\n")  # 限制輸出長度

        # 檢查是否為空回應
        if not json_str:
            raise ValueError("LLM returned empty response")

        # 檢查是否為空或非 JSON 回應
        if not json_str or "{" not in json_str:
            print(f"[WARNING] Non-JSON response: {json_str[:200]}")
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
                print(f"[WARNING] Could not find JSON in response: {json_str[:200]}")
                raise ValueError(f"Invalid response format: {json_str[:100]}")

        print(f"[DEBUG] Parsed JSON string:\n{json_str[:200]}...\n")
        data = json.loads(json_str)
        return LLMOutput(**data)
