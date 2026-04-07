from google import genai
from google.genai import types
import openai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Google Gen AI
try:
    google_api_key = os.getenv("GOOGLE_GENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if google_api_key:
        client = genai.Client(api_key=google_api_key)
        # Test with a simple prompt
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Hello!",
            config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=2048),
        )
        print("Google Gen AI connection successful.")
        print(f"Response: {response.text}")
    else:
        print(
            "GOOGLE_GENAI_API_KEY or GEMINI_API_KEY not found. Skipping Google Gen AI test."
        )
except Exception as e:
    print(f"Google Gen AI connection failed: {e}")

# Configure OpenAI
try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        openai.api_key = openai_api_key
        # Test with a simple prompt
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
            ],
        )
        print("OpenAI connection successful.")
        print(f"Response: {response.choices[0].message.content}")
    else:
        print("OPENAI_API_KEY not found. Skipping OpenAI test.")
except Exception as e:
    print(f"OpenAI connection failed: {e}")
