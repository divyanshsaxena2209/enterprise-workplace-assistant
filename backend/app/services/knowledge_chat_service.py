from app.db.supabase import get_supabase_client
from app.schemas.knowledge_chat import ChatSession, ChatMessage
import uuid
import json
import time

def retry_execute(query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return query.execute()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            if "10053" in str(e) or "aborted" in str(e).lower() or "timeout" in str(e).lower():
                time.sleep(1)
            else:
                raise e

def get_user_sessions(user_id: str):
    client = get_supabase_client()
    res = retry_execute(client.table("knowledge_chat_sessions").select("*").eq("user_id", user_id).order("updated_at", desc=True))
    return res.data

def create_session(user_id: str, title: str):
    client = get_supabase_client()
    session_id = str(uuid.uuid4())
    res = retry_execute(client.table("knowledge_chat_sessions").insert({
        "id": session_id,
        "user_id": user_id,
        "title": title
    }))
    return res.data[0] if res.data else None

def rename_session(session_id: str, user_id: str, new_title: str):
    client = get_supabase_client()
    res = retry_execute(client.table("knowledge_chat_sessions").update({
        "title": new_title,
        "updated_at": "now()"
    }).eq("id", session_id).eq("user_id", user_id))
    return True

def get_session_messages(session_id: str, user_id: str):
    client = get_supabase_client()
    print(f"[DEBUG] get_session_messages called with session_id='{session_id}', user_id='{user_id}'")

    session = retry_execute(client.table("knowledge_chat_sessions").select("id").eq("id", session_id).eq("user_id", user_id))
    if not session.data:
        print(f"[DEBUG] get_session_messages FAILED ownership check for session_id='{session_id}'. Data returned: {session.data}")
        raise Exception("Session not found or unauthorized")
        
    res = retry_execute(client.table("knowledge_chat_messages").select("*").eq("session_id", session_id).order("created_at"))
    return res.data

def delete_session(session_id: str, user_id: str):
    client = get_supabase_client()
    res = retry_execute(client.table("knowledge_chat_sessions").delete().eq("id", session_id).eq("user_id", user_id))
    return True

def add_message(session_id: str, role: str, content: str, sources: list = None):
    client = get_supabase_client()
    msg_id = str(uuid.uuid4())
    retry_execute(client.table("knowledge_chat_messages").insert({
        "id": msg_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "sources": sources or []
    }))

    retry_execute(client.table("knowledge_chat_sessions").update({
        "updated_at": "now()"
    }).eq("id", session_id))
    
    return msg_id
