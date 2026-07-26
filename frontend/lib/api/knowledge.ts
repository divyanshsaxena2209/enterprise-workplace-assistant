import { fetchWithAuth } from "./candidates";
import { createClient } from "@/lib/supabase/client";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL;
const API_URL = BASE_URL?.includes("/api/v1") ? BASE_URL : `${BASE_URL?.replace(/\/$/, "")}/api/v1`;

export async function uploadKnowledgeDocument(file: File) {
  const supabase = createClient();
  const { data: { session } } = await supabase.auth.getSession();

  const formData = new FormData();
  formData.append("file", file);

  const headers = new Headers();
  if (session?.access_token) {
    headers.set("Authorization", `Bearer ${session.access_token}`);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 60000); 

  try {
    const response = await fetch(`${API_URL}/knowledge/upload`, {
      method: "POST",
      headers,
      body: formData,
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || errorData.detail || `Upload Failed: ${response.status}`);
    }

    return response.json();
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error("Upload timed out after 60 seconds.");
    }
    throw error;
  }
}

export async function queryKnowledgeBase(question: string) {
  return fetchWithAuth("/knowledge/query", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
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
