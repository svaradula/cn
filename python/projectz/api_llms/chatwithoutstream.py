import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def main():
    # Initialize the google generative model
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        top_p=0.9,
        top_k=10,
        max_output_tokens=7000,
        streaming=False
    )

    print("🚀 Running chat without stream...\n")
    messages = [
        {"role": "user", "content": "Explain black holes in simple terms."}
    ]

    print("🤖 Generating response...\n")

    try: 
        response = llm.invoke(messages)
        print(f"🧠 Response: {response.content}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

    print("\n✅ Finished processing.")

if __name__ == "__main__":
    main()

 