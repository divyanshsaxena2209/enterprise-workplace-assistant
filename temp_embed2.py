import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/backend")

from google import genai
from app.core.config import settings

def test_embed():
    models = ["text-embedding-004", "gemini-embedding-2", "gemini-embedding-001", "embedding-001", "models/text-embedding-004"]
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    for m in models:
        try:
            print(f"Testing {m}...")
            response = client.models.embed_content(
                model=m,
                contents=["hello world"]
            )
            print(f"Success with {m}! Length of embedding: {len(response.embeddings[0].values)}")
            break
        except Exception as e:
            print(f"Error with {m}: {e}")

if __name__ == "__main__":
    test_embed()
