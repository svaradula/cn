import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

def main():
    """
    Demonstrates how Gemini responds without streaming.
    """
    # Load environment variables (optional if key is hardcoded)
    load_dotenv()

    # Your API key
    api_key = "AIzaSyBQ4ILuphdbP8ThhkADIEjXScWneSL1B7s"
    if not api_key:
        raise ValueError("Google API Key is missing.")

    print("--- 🚀 Initializing Model (No Streaming) ---")

    # Initialize model, passing the API key directly
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.7,
        google_api_key=api_key  # The API key is now correctly passed here
    )

    # Input message
    messages = [
        {"role": "user", "content": "Explain black holes in simple terms."}
    ]

    print("🤖 Generating response...\n")

    try:
        # Use .invoke() instead of .stream()
        response = llm.invoke(messages)

        # Print the full response at once
        print(response.content)

    except Exception as e:
        print(f"\n\nAn error occurred: {e}")

    print("\n\n✅ Response Complete.")

if __name__ == "__main__":
    main()