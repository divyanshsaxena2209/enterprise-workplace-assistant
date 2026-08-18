import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/backend")

from google import genai
from app.core.config import settings
from typing import List

class CustomGenAIEmbeddings:
    def __init__(self, model_name="gemini-embedding-2", api_key=None):
        self.client = genai.Client(api_key=api_key or settings.GEMINI_API_KEY)
        self.model_name = model_name
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Batched or loop
        res = []
        for i in range(0, len(texts), 10):
            batch = texts[i:i+10]
            resp = self.client.models.embed_content(
                model=self.model_name,
                contents=batch
            )
            for emb in resp.embeddings:
                res.append(emb.values)
        return res
        
    def embed_query(self, text: str) -> List[float]:
        resp = self.client.models.embed_content(
            model=self.model_name,
            contents=text
        )
        return resp.embeddings[0].values

def test():
    emb = CustomGenAIEmbeddings()
    val = emb.embed_documents(["hello", "world", "this is a longer sentence to test out the connection to gemini embeddings 2"])
    print(f"Len of val: {len(val)}, Dim: {len(val[0])}")

if __name__ == "__main__":
    test()
