import openai
import os

openai.api_key = os.environ.get("OPENAI_API_KEY", "dummy_key")

try:
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ],
    )
    print("API call successful!")
    print(response)
except Exception as e:
    print(f"API call failed: {e}")
