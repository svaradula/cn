
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.callbacks import StreamingStdOutCallbackHandler # Import this

load_dotenv()

def main(): 
    # Initialize the google generative model
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        top_p=0.9,
        top_k=10,
        streaming=True,
        callbacks=[StreamingStdOutCallbackHandler()],
        max_output_tokens=7000
    )

    print("🚀 Running chat with stream...\n")
    messages = [
        {"role": "user", "content": "Explain black holes in simple terms in not more than 1500 words."}
    ]

    print("Thinking...\n")

    try: 
        llm.invoke(messages)
        # for chunk in llm.stream(messages):
        #     print(chunk.content, end='', flush=True)
    except Exception as e:
        print(f"❌ An error occurred: {e}")

    print("\n✅ Finished processing.")


if __name__ == "__main__":
    main()