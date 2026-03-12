# customer_feedback_system_using_core_python.py

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from a .env file
load_dotenv()

# Configure the Gemini API key
api_key = "AIzaSyBQ4ILuphdbP8ThhkADIEjXScWneSL1B7s"
if not api_key:
    raise ValueError("Missing GOOGLE_API_KEY in environment. Please set it.")
genai.configure(api_key=api_key)

# Initialize the generative model
# This is the updated, recommended way to initialize the model.
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

def classify_and_respond(feedback: str) -> dict:
    """
    Sends user feedback to Gemini for classification and response generation.
    """
    prompt = f"""
You are a customer support assistant. Your task is to classify the following feedback
into one of three categories: complaint, suggestion, or praise. After classifying,
compose a polite and helpful response.

Feedback: "{feedback}"

Please format your output strictly as follows:
Category: <one word>
Response: <your reply>
"""

    # Generate content using the model
    response = model.generate_content(prompt)

    # Parse the model's structured text output
    try:
        text_parts = response.text.strip().split("\n")
        category = text_parts[0].split(":", 1)[1].strip()
        reply = text_parts[1].split(":", 1)[1].strip()
        result = {"category": category, "response": reply}
    except (IndexError, AttributeError) as e:
        print(f"Error parsing model response: {e}\nResponse text: {response.text}")
        result = {"category": "parsing_error", "response": "Could not parse the model's output."}
        
    return result

if __name__ == "__main__":
    print("--- Customer Feedback Analysis (Core SDK) ---\n")
    test_feedback = [
        "I absolutely love the new user interface!",
        "Your application crashes every time I try to open it on my tablet.",
        "It would be really great if you could add a dark mode option."
    ]

    for fb in test_feedback:
        output = classify_and_respond(fb)
        print(f"Feedback: {fb}")
        print(f"→ Category: {output['category']}")
        print(f"→ Response: {output['response']}\n")