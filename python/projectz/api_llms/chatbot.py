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


chat = client.chats.create(
    model="gemini-2.5-flash",
    history=[],
    config={
        "system_instruction": system_instruction,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 10,
        "max_output_tokens": 1000
    }
)

while True:
    print()
    user_input = input("You: ")
    if user_input.lower() in ("exit", "quit"):
        print("Goodbye! Keep looking up at the stars! 🌟")
        break
    try:
        full_text = []
        print("Chatbot: ", end="", flush=True)
        for chunk in chat.send_message_stream(user_input):
            text = getattr(chunk, "text", None)
            if text:
                print(text, end="", flush=True)
                full_text.append(text)

        print()  # final newline 

    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(1)  # Wait a bit before trying again
