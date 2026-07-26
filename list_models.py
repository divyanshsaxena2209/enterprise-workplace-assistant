import os
from google import genai
import dotenv

dotenv.load_dotenv("backend/.env")
api_key = os.environ.get("GEMINI_API_KEY")

try:
    client = genai.Client(api_key=api_key)
    for model in client.models.list():
        print(model.name)
except Exception as e:
    print("Error:", e)
