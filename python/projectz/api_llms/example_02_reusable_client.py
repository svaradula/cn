import os
from xml.parsers.expat import model
from dotenv import load_dotenv, find_dotenv
from google import genai

load_dotenv(find_dotenv())

class GeminiClient:
    def __init__(self, model: str = "gemini-2.5-flash"):
        if not os.getenv("GEMINI_API_KEY"):
            raise ValueError("GEMINI_API_KEY is not set.")
        self.model = model
        self.client = genai.Client()
    
    def ask(self, question: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=question
        )
        return response.text



if __name__ == "__main__":
    gemini = GeminiClient()
    userask = input("Ask a question to Gemini: ")
    print("Question from user is : ", userask)
    print("Asking Gemini...")
    answer = gemini.ask(userask)
    print(answer)
