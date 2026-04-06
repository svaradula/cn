import os
import asyncio
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.callbacks import StreamingStdOutCallbackHandler


load_dotenv()

def main():
    batch_prompts = [
        "Define AI in simple terms.",
        "What is GenAI and how does it differ from traditional AI?",
        "What are some common applications of GenAI?",
        "What are the ethical considerations surrounding GenAI?",
    ]

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        top_p=0.9,
        top_k=10,
        max_output_tokens=1500)
    
    responses = llm.batch(batch_prompts)

    for i, response in enumerate(responses):
        print(f"Prompt {i+1}: {batch_prompts[i]}")
        print(f"Response {i+1}: {response.content}\n")
    
if __name__ == "__main__":
    main()