import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/backend")

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings

def test_embed():
    models = ["models/text-embedding-004", "models/embedding-001"]
    for m in models:
        try:
            print(f"Testing {m} without transport=rest...")
            embedder = GoogleGenerativeAIEmbeddings(
                model=m,
                google_api_key=settings.GEMINI_API_KEY
            )
            res = embedder.embed_documents(["hello world"])
            print(f"Success with {m}! Length of embedding: {len(res[0])}")
        except Exception as e:
            print(f"Error with {m}: {e}")

if __name__ == "__main__":
    test_embed()
