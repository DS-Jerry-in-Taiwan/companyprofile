import google.generativeai as genai
import openai
import os

# Configure Google Generative AI
try:
    google_api_key = os.getenv("GEMINI_API_KEY")
    if google_api_key:
        genai.configure(api_key=google_api_key)
        # Test with a simple prompt
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = model.generate_content("Hello!")
        print("Google Generative AI connection successful.")
        print(f"Response: {response.text}")
    else:
        print("GEMINI_API_KEY not found. Skipping Google Generative AI test.")
except Exception as e:
    print(f"Google Generative AI connection failed: {e}")

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
