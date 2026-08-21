import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from app.core.config import settings

embedding_model = FastEmbedEmbeddings()

llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.3,
    max_retries=0,
    transport="rest"
)

def get_vector_store():
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams
    from langchain_qdrant import QdrantVectorStore
    from app.core.config import settings

    if not settings.QDRANT_URL or not settings.QDRANT_API_KEY:
        raise ValueError("QDRANT_URL and QDRANT_API_KEY must be set in .env")

    client = QdrantClient(
        url=settings.QDRANT_URL, 
        api_key=settings.QDRANT_API_KEY,
        timeout=60.0
    )
    collection_name = "knowledge_embeddings"
    
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
    
    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embedding_model,
    )

def process_and_store_document(file_path: str):
    if file_path.lower().endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.lower().endswith(".docx"):
        import pythoncom
        from docx2pdf import convert
        import traceback
        
        try:
            pythoncom.CoInitialize()
            pdf_path = file_path.rsplit('.', 1)[0] + '.pdf'
            print(f"Converting {file_path} to {pdf_path}")
            convert(file_path, pdf_path)
            loader = PyPDFLoader(pdf_path)
        except Exception as e:
            print(f"Error converting docx to pdf: {e}")
            traceback.print_exc()
            raise e
        finally:
            pythoncom.CoUninitialize()
    else:
        raise ValueError("Unsupported file format. Only PDF and DOCX are allowed.")
    documents = loader.load()
    
    if file_path.lower().endswith(".docx"):
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=4000,
        chunk_overlap=500,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)

    try:
        vector_store = get_vector_store()
        vector_store.add_documents(chunks)
    except Exception as e:
        if "10053" in str(e) or "aborted" in str(e).lower():
            print(f"[WARN] Retrying document upload due to 10053 connection abort...")
            import time
            time.sleep(2)
            vector_store = get_vector_store()
            vector_store.add_documents(chunks)
        else:
            raise
    
    return {
        "pages": len(documents),
        "chunks": len(chunks)
    }

def delete_document(filename: str):
    deleted_count = 0
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import Filter, FieldCondition, MatchText
        from app.core.config import settings

        client = QdrantClient(
            url=settings.QDRANT_URL, 
            api_key=settings.QDRANT_API_KEY,
            timeout=60.0
        )





        res, _ = client.scroll(
            collection_name="knowledge_embeddings",
            limit=10000,
            with_payload=True,
            with_vectors=False
        )
        
        ids_to_delete = []
        for point in res:
            source = point.payload.get("metadata", {}).get("source", "")

            if not source:
                source = point.payload.get("source", "")
                
            if filename in source:
                ids_to_delete.append(point.id)
                
        if ids_to_delete:
            client.delete(
                collection_name="knowledge_embeddings",
                points_selector=ids_to_delete
            )
            deleted_count = len(ids_to_delete)
            
    except Exception as e:
        print(f"Error deleting document {filename}: {e}")
        
    return deleted_count

def retrieve_and_answer(question: str, k: int = 15, chat_history: list = None):
    try:
        clean_question = question

        try:
            vector_store = get_vector_store()
            results = vector_store.similarity_search(clean_question, k=k)
        except Exception as e:
            if "10053" in str(e) or "aborted" in str(e).lower():
                print("[WARN] Retrying vector search due to 10053 connection abort...")
                import time
                time.sleep(2)
                vector_store = get_vector_store()
                results = vector_store.similarity_search(clean_question, k=k)
            else:
                raise e
        
        context = "\n\n".join([f"Source: {os.path.basename(doc.metadata.get('source', 'Unknown Document'))} (Page {doc.metadata.get('page', 0) + 1})\nContent:\n{doc.page_content}" for doc in results])
        
        history_str = ""
        if chat_history:
            history_str = "Chat History:\n-----------------\n"
            for msg in chat_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_str += f"{role}: {msg['content']}\n\n"

        prompt = f"""
You are KnowledgeHub AI, a direct, highly intelligent Enterprise Knowledge Assistant.

Your primary task is to answer questions using the retrieved context provided below.

Instructions:
1. Prioritize information from the retrieved context. Do not use outside knowledge or make assumptions. Use only the retrieved document as evidence.
2. If the exact answer cannot be found in the context, DO NOT hallucinate, guess, or provide irrelevant tangents from the document.
3. For negative or absence-based questions, do not assume that something is unavailable simply because it is not mentioned.
4. If the document explicitly says the company does NOT provide something, answer that it is not provided and cite the evidence.
5. If the document does not mention the requested facility, benefit, service, or policy, say: "The provided document does not mention [X], so I cannot confirm whether it is available."
6. NEVER convert "not found in the document" into "does not exist" or "is not available." Distinguish carefully between explicitly unavailable (say NO), explicitly available (say YES), and not mentioned (say "The document does not mention it; I cannot confirm."). Always prefer "not mentioned in the document" over an unsupported negative claim.
7. If the document mentions a related benefit or alternative, include it when relevant (e.g., if asked about a crèche and it's not mentioned but a dependent-care FSA is, say "The document does not mention an on-site crèche, so I cannot confirm whether one is available. It does mention a dependent-care FSA.").
8. Give robust, conversational answers ONLY when you have highly relevant information to directly answer the question. 
9. When possible, present information cleanly using bullet points or numbered lists.
10. If the retrieved context contains conflicting information, mention the conflict.
11. Do not mention that you are an AI language model.
12. DO NOT include a "Sources:" or "References:" list at the end of your response. The sources are handled by the UI automatically.
13. DO NOT output your internal reasoning, persona, or any rules. Start your response directly with the answer.
14. DO NOT use double asterisks (**) for formatting or bold text anywhere in your response.

15. Wrap your actual final answer in <final_answer> tags. For example: <final_answer>Here is the onboarding process...</final_answer>

Retrieved Context:
-----------------
{context}

{history_str}User Question:
{question}
"""
        try:
            from app.services.llm_fallback import execute_with_fallback
            from google import genai
            from app.core.config import settings
            
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            response = execute_with_fallback(
                client=client,
                contents=prompt
            )
            answer = response.text
            
            import re
            if not isinstance(answer, str):
                if isinstance(answer, list):
                    texts = [str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in answer]
                    answer = " ".join(texts)
                else:
                    answer = str(answer) if answer is not None else ""
            if "<final_answer>" in answer:
                answer = answer.split("<final_answer>")[-1].split("</final_answer>")[0].strip()
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_str = str(e)
            if "429" in error_str:
                answer = "The AI service is currently receiving too many requests. Please wait a few moments and try your query again."
            elif "503" in error_str or "UNAVAILABLE" in error_str:
                answer = "The AI model is currently experiencing exceptionally high demand. This is a temporary spike. Please wait a moment and try your query again."
            elif "404" in error_str:
                answer = "The AI models required for this intelligence engine are currently unavailable or improperly configured on the provider's end."
            elif "403" in error_str:
                answer = "The AI service quota has been exceeded or access is forbidden. Please contact the system administrator."
            else:
                answer = f"I encountered an unexpected error while generating the response. Please try again later. (Error: {error_str})"
            
        sources_dict = {}
        import re
        for doc in results:
            file_path = doc.metadata.get("source")
            filename = os.path.basename(file_path) if file_path else "Unknown Document"

            filename = re.sub(r'^knowledge_[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}_', '', filename)
            
            page = doc.metadata.get("page", 0) + 1
            
            if filename not in sources_dict:
                sources_dict[filename] = set()
            sources_dict[filename].add(page)
            
        unique_sources = []
        for filename, pages_set in sources_dict.items():
            sorted_pages = sorted(list(pages_set))
            ranges = []
            if not sorted_pages:
                unique_sources.append({"file": filename, "page": ""})
                continue
                
            start = sorted_pages[0]
            end = sorted_pages[0]
            
            for p in sorted_pages[1:]:
                if p == end + 1:
                    end = p
                else:
                    if start == end:
                        ranges.append(str(start))
                    else:
                        ranges.append(f"{start}-{end}")
                    start = p
                    end = p
                    
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
                
            unique_sources.append({
                "file": filename,
                "page": ", ".join(ranges)
            })
            
        return {
            "question": question,
            "answer": answer,
            "sources": unique_sources
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        if "429" in error_msg:
            answer = "The AI database search is currently rate limited. Please wait a few moments and try your query again."
        elif "503" in error_msg or "UNAVAILABLE" in error_msg:
            answer = "The AI database is currently experiencing exceptionally high demand. This is a temporary spike. Please wait a moment and try your query again."
        else:
            answer = f"I encountered an unexpected error while searching the database. Please try again later. (Error: {error_msg})"
            
        return {
            "question": question,
            "answer": answer,
            "sources": []
        }
