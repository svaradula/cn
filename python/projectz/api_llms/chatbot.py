import os
from dotenv import load_dotenv
from google import genai
import time

load_dotenv()
client = genai.Client()

system_instruction = (
    "You are a space researcher who is very friendly and explains complex space-related topics "
    "in simple and poetic language. You make learning about space fun and easy for someone who is not a scientist "
    "but is very curious to learn. Keep your responses concise and lyrical, around 30-50 words."
)

user_input = ""

model = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=user_input, 
    config={
        "system_instruction": system_instruction,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 50,
        "max_output_tokens": 100
    }
)


print("🚀 SpaceBot ready! Ask anything about space. Type 'exit' to quit.\n")