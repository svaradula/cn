from langchain_google_genai import GoogleGenerativeAI
from dotenv import load_dotenv
import os
import asyncio
load_dotenv()

# Initialize the google generative model
llm = GoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    top_p=0.9,
    top_k=10,
    max_output_tokens=100000
)

batch_prompts = [
    "Introduction to Marvel Cinematic Universe",
    "What is the order of the movies in the Marvel Cinematic Universe?",
    "Who are the main characters in the Marvel Cinematic Universe?",
    "What are the major story arcs in the Marvel Cinematic Universe?",
]

async def run_abatch():
    print("🚀 Running abatch (async batch processing)...\n")
    responses = await llm.abatch(batch_prompts)

    # Display results
    for i, response in enumerate(responses):
        print(f"\n🔹 Prompt {i+1}: {batch_prompts[i]}")
        print(f"🧠 Response: {response}")

# Run the async function
if __name__ == "__main__":
    asyncio.run(run_abatch())