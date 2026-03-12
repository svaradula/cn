# --- Cell 1: Imports and Function Definition ---

import os
import asyncio
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

async def main():
    """
    Demonstrates non-blocking async streaming using astream().
    """
    load_dotenv()
    api_key = "AIzaSyBQ4ILuphdbP8ThhkADIEjXScWneSL1B7s"
    if not api_key:
        raise ValueError("Google API Key is missing.")

    print("---  Initializing Model with Async Streaming ---")

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.7,
        streaming=True,
        google_api_key=api_key
    )

    messages = [
        {"role": "user", "content": "Write a long, hopeful story about AI and humanity coexisting peacefully in the year 2077."}
    ]

    print("Generating async response...\n")

    try:
        async for chunk in llm.astream(messages):
            print(chunk.content, end="", flush=True)
    except Exception as e:
        print(f"\n\nAn error occurred: {e}")

    print("\n\nAsync Stream Complete.")

# --- Cell 2: Execute the async function ---

# Now, run your main function by awaiting it directly.
await main()