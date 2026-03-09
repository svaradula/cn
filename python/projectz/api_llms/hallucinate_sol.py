import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import time

load_dotenv()
client = genai.Client()


file_search_store = client.file_search_stores.create(
    config={"display_name": "company-policy-store"}
)

# Step 2: Upload the policy file into the File Search store
operation = client.file_search_stores.upload_to_file_search_store(
    file="policy.txt",
    file_search_store_name=file_search_store.name,
    config={"display_name": "company-return-policy"}
)

while not operation.done:
    time.sleep(5)
    operation = client.operations.get(operation)

# Step 4: Ask a question with File Search enabled
question = "Can I return opened electronics after 7 days?"

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=question,
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(
                file_search=types.FileSearch(
                    file_search_store_names=[file_search_store.name]
                )
            )
        ]
    )
)

print("=== Gemini + RAG Answer ===")
print(response.text)