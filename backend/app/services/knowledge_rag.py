import uuid
import chromadb
from google import genai
from app.core.config import settings
from app.schemas.knowledge import ReferenceItem, RAGQueryResponse

genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Initialize ChromaDB Persistent Client
chroma_client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)
# Get or create default collection
rag_collection = chroma_client.get_or_create_collection(
    name="enterprise_knowledge",
    metadata={"hnsw:space": "cosine"}
)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    Splits plain text into overlapping chunks of defined size.
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_length:
            break
        start += (chunk_size - overlap)
        
    return chunks

def get_gemini_embedding(text: str) -> list[float]:
    """
    Generates embedding vector for text using text-embedding-004.
    """
    response = genai_client.models.embed_content(
        model="text-embedding-004",
        contents=text
    )
    return response.embeddings[0].values

def index_document_in_chroma(document_id: str, title: str, file_path: str, text: str):
    """
    Chunks document text, embeddings each chunk, and registers in ChromaDB.
    """
    chunks = chunk_text(text)
    if not chunks:
        return

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        chunk_id = f"{document_id}_chunk_{i}"
        vector = get_gemini_embedding(chunk)
        
        ids.append(chunk_id)
        embeddings.append(vector)
        documents.append(chunk)
        metadatas.append({
            "document_id": document_id,
            "title": title,
            "file_path": file_path,
            "chunk_index": i
        })

    # Add in batches to Chroma DB
    rag_collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )

def query_rag_knowledge(query_text: str) -> RAGQueryResponse:
    """
    Queries ChromaDB vector store, retrieves top matches, synthesizes response using Gemini.
    """
    # 1. Embed query
    query_vector = get_gemini_embedding(query_text)

    # 2. Query Chroma collection
    results = rag_collection.query(
        query_embeddings=[query_vector],
        n_results=4
    )

    # Extract matches
    references = []
    retrieved_texts = []
    
    if results and results["documents"] and len(results["documents"][0]) > 0:
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        
        for doc_text, meta in zip(docs, metas):
            references.append(ReferenceItem(
                document_title=meta.get("title", "Unknown Policy"),
                file_path=meta.get("file_path", ""),
                matched_text=doc_text
            ))
            retrieved_texts.append(f"Source: {meta.get('title')}\nExcerpt: {doc_text}")

    # 3. Formulate Prompt and Synthesize Contextual Answer
    context_str = "\n\n---\n\n".join(retrieved_texts) if retrieved_texts else "No specific policies matched."
    
    system_prompt = """
    You are an expert Enterprise Workplace Assistant bot.
    Your goal is to answer employee questions regarding company policies, guidelines, and SOPs accurately and professionally.
    
    GUIDELINES:
    1. Base your answer strictly on the provided context sections.
    2. If the context does not contain enough information to answer the question, state politely: "I cannot find this information in the uploaded company policies. Please consult HR."
    3. Cite the documents you retrieve to give workers full clarity on what guidelines apply.
    4. Keep the tone helpful, professional, and corporate.
    """

    user_prompt = f"""
    CONTEXT FROM COMPANY DOCUMENTS:
    {context_str}

    EMPLOYEE QUESTION:
    {query_text}

    Provide your detailed synthesized response citing references from the sources:
    """

    try:
        prompt = f"System Instruction: {system_prompt}\n\n{user_prompt}"
        completion = genai_client.models.generate_content(
            model="gemma-4-31b-it",
            contents=prompt
        )
        answer_text = completion.text
    except Exception as e:
        answer_text = f"An error occurred while generating the response: {str(e)}"

    return RAGQueryResponse(
        answer_text=answer_text,
        references=references
    )
