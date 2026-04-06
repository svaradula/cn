from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def main():
    llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            top_p=0.9,
            top_k=10,
            max_output_tokens=1500)

    prompts = [
        "Explain Python in 3 lines.",
        "Explain LangChain in 3 lines.",
        "Explain RAG in 3 lines."
    ]

    for i, prompt in enumerate(prompts, start=1):
        print(f"\n\n--- Streaming response for Prompt {i} ---")
        print(f"Prompt: {prompt}\n")
        
        for chunk in llm.stream(prompt):
            print(chunk.content, end="", flush=True)

        print("\n")

if __name__ == "__main__":
    main()