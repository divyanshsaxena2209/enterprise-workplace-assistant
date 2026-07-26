import os
import chromadb
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from app.core.config import settings


from langchain_community.embeddings.fastembed import FastEmbedEmbeddings


embedding_model = FastEmbedEmbeddings()

llm = ChatGoogleGenerativeAI(
    model="gemma-4-31b-it",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.3,
)


try:
    chroma_client = chromadb.HttpClient(host="127.0.0.1", port=8080)
except Exception as e:
    print(f"[WARN] Failed to connect to ChromaDB: {e}")
    chroma_client = None

COLLECTION_NAME = "enterprise_knowledge_fastembed"

def get_vector_store():
    global chroma_client
    if not chroma_client:
        try:
            chroma_client = chromadb.HttpClient(host="127.0.0.1", port=8080)
            
            chroma_client.heartbeat()
        except Exception as e:
            raise Exception(f"ChromaDB is not available on port 8080. Detailed Error: {str(e)}")
            
    return Chroma(
        client=chroma_client,
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_model,
    )

def process_and_store_document(file_path: str):
    
    if file_path.lower().endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.lower().endswith(".docx"):
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError("Unsupported file format. Only PDF and DOCX are allowed.")
    documents = loader.load()
    
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    
    
    vector_store = get_vector_store()
    vector_store.add_documents(chunks)
    
    return {
        "pages": len(documents),
        "chunks": len(chunks)
    }

def delete_document(filename: str):
    vector_store = get_vector_store()
    collection = vector_store._collection
    
    sources_to_try = [
        f"uploads\\{filename}",
        f"uploads/{filename}"
    ]
    
    deleted_count = 0
    for source in sources_to_try:
        results = collection.get(where={"source": source})
        if results and results.get("ids"):
            collection.delete(ids=results["ids"])
            deleted_count += len(results["ids"])
            
    return deleted_count

def retrieve_and_answer(question: str, k: int = 3):
    vector_store = get_vector_store()
    
    
    results = vector_store.similarity_search(question, k=k)
    
    
    context = "\n\n".join([f"Source: {os.path.basename(doc.metadata.get('source', 'Unknown Document'))} (Page {doc.metadata.get('page', 0) + 1})\nContent:\n{doc.page_content}" for doc in results])
    prompt = f"""
You are KnowledgeHub AI, an intelligent Enterprise Knowledge Assistant.

Your task is to answer questions ONLY using the retrieved context provided below.

Instructions:
1. Use only the information found in the context.
2. Never invent, assume, or hallucinate facts.
3. If the answer cannot be found in the context, respond exactly:
   "I couldn't find that information in the uploaded documents."
4. Keep answers concise, clear, and professional.
5. When possible:
   - Present information using bullet points or numbered lists.
   - Include important values, dates, names, or figures exactly as written.
6. If the retrieved context contains conflicting information, mention the conflict.
7. Do not mention that you are an AI language model.
8. ALWAYS cite your sources in the answer based on the 'Source:' headers in the context (e.g., "According to [Document Name]...").

Retrieved Context:
-----------------
{context}

User Question:
{question}

Answer:
"""
    try:
        response = llm.invoke(prompt)
        answer = response.content
    except Exception as e:
        answer = f"Error: {str(e)}"
        
    return {
        "question": question,
        "answer": answer,
        "sources": [
            {
                "file": doc.metadata.get("source"),
                "page": doc.metadata.get("page", 0) + 1
            }
            for doc in results
        ]
    }
