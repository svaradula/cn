import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

question = "Can I return opened electronics after 7 days?"

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=question,
)

print("=== Plain Gemini Answer ===")
print(response.text)