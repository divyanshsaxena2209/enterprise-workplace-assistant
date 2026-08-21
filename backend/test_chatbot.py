import asyncio
import os
from app.services.knowledge_rag import retrieve_and_answer

async def test_chatbot():
    print("Testing chatbot...")
    question = "What is the policy on taking time off according to the Basecamp employee handbook?"
    print(f"Question: {question}")

    result = await asyncio.to_thread(retrieve_and_answer, question, k=5, chat_history=[])
    
    print("\nAnswer:")
    print(result.get("answer", "No answer found"))
    print("\nSources:")
    for source in result.get("sources", []):
        print(f"- {source.get('file')} (Page {source.get('page')})")

if __name__ == "__main__":
    asyncio.run(test_chatbot())
