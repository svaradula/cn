# example_04_chat_session.py
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def main():
    client = genai.Client()

    chat = client.chats.create(model="gemini-2.5-flash")

    response1 = chat.send_message("My name is Manava. I am learning Python for GenAI.")
    print("Assistant:", response1.text)

    response2 = chat.send_message("Based on that, suggest 3 project ideas for me.")
    print("Assistant:", response2.text)

    print("\nConversation history:")
    for message in chat.get_history():
        try:
            print(f"{message.role}: {message.parts[0].text}")
        except Exception:
            print(f"{message.role}: [non-text message]")

if __name__ == "__main__":
    main()