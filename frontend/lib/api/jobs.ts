import { fetchWithAuth } from "./candidates";

export async function getJobs(page = 1, pageSize = 20) {
  return fetchWithAuth(`/jobs?page=${page}&page_size=${pageSize}`);
}

export async function getJob(id: string) {
  return fetchWithAuth(`/jobs/${id}`);
}

export async function createJob(jobData: any, providedToken: string | null = null) {
  let token = providedToken;
  if (!token) {
    const { createClient } = await import("@/lib/supabase/client");
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    token = session?.access_token || null;
  }
  
  if (!token) throw new Error("Authentication failed. No token found.");

  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  const API_URL = BASE_URL.includes("/api/v1") ? BASE_URL : `${BASE_URL.replace(/\/$/, "")}/api/v1`;

  const headers = new Headers();
  headers.set("Content-Type", "application/json");
  headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_URL}/jobs`, {
    method: "POST",
    headers,
    body: JSON.stringify(jobData),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || `API Error: ${res.status}`);
  }

  return res.json();
}

export async function publishJob(jobId: string, providedToken: string | null = null) {
  let token = providedToken;
  if (!token) {
    const { createClient } = await import("@/lib/supabase/client");
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    token = session?.access_token || null;
  }
  
  if (!token) throw new Error("Authentication failed. No token found.");

  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  const API_URL = BASE_URL.includes("/api/v1") ? BASE_URL : `${BASE_URL.replace(/\/$/, "")}/api/v1`;

  const headers = new Headers();
  headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_URL}/jobs/${jobId}/publish`, {
    method: "PATCH",
    headers,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || `API Error: ${res.status}`);
  }

  return res.json();
}
