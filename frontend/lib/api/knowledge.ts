import { fetchWithAuth } from "./candidates";
import { createClient } from "@/lib/supabase/client";
const BASE_URL = process.env.NEXT_PUBLIC_API_URL;
const API_URL = BASE_URL?.includes("/api/v1") ? BASE_URL : `${BASE_URL?.replace(/\/$/, "")}/api/v1`;
export async function uploadKnowledgeDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const controller = new AbortController();
  try {
    return await fetchWithAuth("/knowledge/upload", {
      method: "POST",
      body: formData,
      signal: controller.signal,
      timeoutMs: 300000, 
    });
  } catch (error: any) {
    if (error.name === 'AbortError') {
      throw new Error("Upload timed out after 5 minutes.");
    }
    throw error;
  }
}
export async function queryKnowledgeBase(question: string, session_id?: string, signal?: AbortSignal) {
  return fetchWithAuth("/knowledge/query", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question, session_id }),
    timeoutMs: 300000,
    signal,
  });
}
export async function deleteKnowledgeDocument(filename: string, file_url?: string) {
  return fetchWithAuth("/knowledge/document", {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ filename, file_url }),
  });
}
export async function getChatSessions() {
  return fetchWithAuth("/knowledge/sessions", {
    method: "GET",
  });
}
export async function createChatSession(title: string, signal?: AbortSignal) {
  return fetchWithAuth("/knowledge/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
    signal,
  });
}
export async function getChatSessionMessages(sessionId: string) {
  if (!sessionId || sessionId === "undefined") return [];
  return fetchWithAuth(`/knowledge/sessions/${sessionId}/messages`, {
    method: "GET",
  });
}
export async function deleteChatSession(sessionId: string) {
  if (!sessionId || sessionId === "undefined") return { success: false };
  return fetchWithAuth(`/knowledge/sessions/${sessionId}`, {
    method: "DELETE",
  });
}
export async function renameChatSession(sessionId: string, newTitle: string) {
  return fetchWithAuth(`/knowledge/sessions/${sessionId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title: newTitle }),
  });
}
