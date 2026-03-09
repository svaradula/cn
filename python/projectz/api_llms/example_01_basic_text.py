# example_01_basic_text.py
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def main():
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY is not set.")

    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Explain what an API is in simple English for a software engineer."
    )

    print(response.text)

if __name__ == "__main__":
    main()