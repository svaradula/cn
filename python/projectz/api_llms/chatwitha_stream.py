import os
import asyncio
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.callbacks import StreamingStdOutCallbackHandler # Import this


load_dotenv()

async def main():
    # Initialize the google generative model
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        top_p=0.9,
        top_k=10,
        streaming=True,
        max_output_tokens=7000
    )

    print("🚀 Running chat with async stream...\n")
    messages = [
        {"role": "user", "content": "Give me the list of Marvel "
        "movies in the order of release date."}
    ]

    print("Thinking...\n")

    try: 
        async for chunk in llm.astream(messages):
            print(chunk.content, end='', flush=True)
    except Exception as e:
        print(f"❌ An error occurred: {e}")

    print("\n✅ Finished processing.")

print("This program demonstrates how to use the ChatGoogleGenerativeAI with async streaming. It will print the response from the model as it is generated, allowing for a more interactive experience.")
if __name__ == "__main__":
    asyncio.run(main())
    