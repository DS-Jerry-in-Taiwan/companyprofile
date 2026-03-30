import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from src.schemas.llm_output import LLMOutput

load_dotenv()


class LLMService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-flash-latest")

    def _load_template(self, template_path: str) -> str:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()

    def generate(self, company_data: dict) -> LLMOutput:
        template = self._load_template("generate_prompt_template.txt")
        prompt = template.format(**company_data)
        response = self.model.generate_content(prompt)
        return self._parse_response(response.text)

    def optimize(self, original_brief: str, additional_data: dict) -> LLMOutput:
        template = self._load_template("optimize_prompt_template.txt")
        additional_data["original_brief"] = original_brief
        prompt = template.format(**additional_data)
        response = self.model.generate_content(prompt)
        return self._parse_response(response.text)

    def _parse_response(self, text: str) -> LLMOutput:
        json_str = text.strip()
        print(f"[DEBUG] Raw response:\n{json_str}\n")
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
        else:
            start = json_str.find("{")
            end = json_str.rfind("}") + 1
            if start != -1 and end > start:
                json_str = json_str[start:end]
        print(f"[DEBUG] Parsed JSON string:\n{json_str}\n")
        data = json.loads(json_str)
        return LLMOutput(**data)
