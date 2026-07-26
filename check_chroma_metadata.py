import os
import chromadb

try:
    client = chromadb.HttpClient(host="127.0.0.1", port=8080)
    collection = client.get_collection("enterprise_knowledge_fastembed")
    results = collection.get(limit=10)
    for meta in results['metadatas']:
        print("Metadata:", meta)
except Exception as e:
    print("Error:", e)
