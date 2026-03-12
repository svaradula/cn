import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load API Key
load_dotenv()
api_key = "AIzaSyBQ4ILuphdbP8ThhkADIEjXScWneSL1B7s"
if not api_key:
    raise ValueError("Google API Key not found. Set it in your .env file.")

# Initialize the Gemini Model
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)

# Create a list of prompts
prompts = [
    "Summarize the history of the internet in 3 lines.",
    "Explain what blockchain is for a beginner.",
    "What are the main components of a neural network?",
    "Give three use-cases of artificial intelligence in education.",
    "Describe the importance of data privacy in healthcare systems."
]

# Invoke one-by-one
for i, prompt in enumerate(prompts):
    response = llm.invoke(prompt)
    print(f"\n🔹 Prompt {i+1}: {prompt}")
    print(f"🧠 Response: {response.content}")