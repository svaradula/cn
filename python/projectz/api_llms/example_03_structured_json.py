# example_03_structured_json.py
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def main():
    client = genai.Client()

    prompt = """
    Read this job description and return:
    - role
    - seniority
    - required_skills
    - optional_skills

    Job Description:
    We are hiring a Senior Python Backend Engineer with experience in FastAPI,
    PostgreSQL, Docker, Redis, and cloud deployments on AWS.
    Nice to have: Kubernetes and CI/CD.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "object",
                "properties": {
                    "role": {"type": "string"},
                    "seniority": {"type": "string"},
                    "required_skills": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "optional_skills": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["role", "seniority", "required_skills", "optional_skills"]
            }
        )
    )

    data = json.loads(response.text)
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()