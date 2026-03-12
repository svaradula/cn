import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

def main():
    """
    Main function to demonstrate streaming with LangChain and Gemini.
    """
    # Load environment variables (optional if key is hardcoded)
    load_dotenv()
    
    # Your API key
    api_key = "AIzaSyBQ4ILuphdbP8ThhkADIEjXScWneSL1B7s"
    if not api_key:
        raise ValueError("Google API Key is missing.")

    print("--- 🚀 Initializing Model for Streaming ---")
    
    # Initialize model, passing the API key directly
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.7,
        streaming=True,
        google_api_key=api_key # <-- This was the missing parameter
    )

    # Input message (as a list of messages)
    messages = [
        {"role": "user", "content": "Explain black holes in simple terms in about 200 words."}
    ]

    # Stream the response directly from the model
    print("🤖 Generating response...\n")

    try:
        for chunk in llm.stream(messages):
            print(chunk.content, end="", flush=True)

    except Exception as e:
        print(f"\n\nAn error occurred: {e}")

    print("\n\n✅ Stream Complete.")
    print("This line runs only after the entire stream is finished.")

if __name__ == "__main__":
    main()