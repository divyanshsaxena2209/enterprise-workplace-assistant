import { createClient } from "@/lib/supabase/client";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const API_URL = BASE_URL.includes("/api/v1") ? BASE_URL : `${BASE_URL.replace(/\/$/, "")}/api/v1`;

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  // Convert any existing headers to a plain object
  const headers: Record<string, string> = {};
  if (options.headers) {
    const rawHeaders = new Headers(options.headers);
    rawHeaders.forEach((value, key) => {
      headers[key] = value;
    });
  }
  
  const isGuest = typeof document !== "undefined" && document.cookie.includes("guest_mode=true");

  console.log(`[fetchWithAuth] Starting request to ${endpoint}`);

  if (isGuest) {
    headers["Authorization"] = "Bearer guest";
  } else {
    try {
      let token: string | null = null;
      
      // Attempt fast synchronous retrieval to bypass deadlocks
      if (typeof window !== "undefined") {
        try {
          const url = new URL(process.env.NEXT_PUBLIC_SUPABASE_URL!);
          const projectRef = url.hostname.split('.')[0];
          const storageKey = `sb-${projectRef}-auth-token`;
          const storedSession = localStorage.getItem(storageKey);
          if (storedSession) {
            const parsed = JSON.parse(storedSession);
            if (parsed && parsed.access_token) {
              token = parsed.access_token;
            }
          }
        } catch (e) {
          console.warn("Fast token retrieval failed", e);
        }
      }
      
      // Fallback to getSession if not found
      if (!token) {
        console.log(`[fetchWithAuth] Fast retrieval missed. Getting Supabase session...`);
        const supabase = createClient();
        
        let sessionTimeoutId: any;
        const sessionPromise = supabase.auth.getSession();
        const sessionTimeout = new Promise<any>((resolve) => {
          sessionTimeoutId = setTimeout(() => resolve({ timeout: true, type: 'session' }), 3000);
        });
        
        const sessionResult = await Promise.race([sessionPromise, sessionTimeout]);
        clearTimeout(sessionTimeoutId);
        
        if (sessionResult?.timeout) {
          console.warn("[fetchWithAuth] Supabase getSession timed out.");
        } else {
          token = sessionResult?.data?.session?.access_token || null;
        }
      }
      
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      } else {
        // If we still don't have a token, we might actually be unauthenticated.
        // Don't throw an aggressive error unless it's a critical route, just proceed without it.
        // The backend will return 401 if it's required.
        console.warn("[fetchWithAuth] Proceeding without Authorization header.");
      }
    } catch (err) {
      console.error("[fetchWithAuth] Failed to retrieve supabase session", err);
    }
  }

  console.log(`[fetchWithAuth] Executing fetch...`);
  
  let fetchPromise;
  try {
    const fetchOptions: RequestInit = {
      method: options.method || 'GET',
      headers: headers,
      credentials: options.credentials || 'include',
    };
    if (options.body) fetchOptions.body = options.body;
    if (options.credentials) fetchOptions.credentials = options.credentials;
    if (options.cache) fetchOptions.cache = options.cache;
    if (options.mode) fetchOptions.mode = options.mode;
    if (options.signal) fetchOptions.signal = options.signal;
    if (options.redirect) fetchOptions.redirect = options.redirect;
    
    fetchPromise = fetch(`${API_URL}${endpoint}`, fetchOptions);
  } catch (err) {
    throw new Error("Unable to initialize fetch request. Ensure the URL is valid.");
  }
  
  let fetchTimeoutId: any;
  const fetchTimeout = new Promise<any>((resolve) => {
    fetchTimeoutId = setTimeout(() => resolve({ timeout: true, type: 'fetch' }), 10000);
  });
  
  let response: any;
  try {
    response = await Promise.race([fetchPromise, fetchTimeout]);
    clearTimeout(fetchTimeoutId);
  } catch (err: any) {
    clearTimeout(fetchTimeoutId);
    if (err.name === 'TypeError' && err.message === 'Failed to fetch') {
      throw new Error(`Unable to connect to the backend server. Please ensure the backend is running on ${BASE_URL}.`);
    }
    throw err;
  }
  
  if (response?.timeout) {
    throw new Error("Fetch timed out after 10s");
  }

  console.log(`[fetchWithAuth] Fetch completed with status:`, response.status);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || errorData.detail || `API Error: ${response.status}`);
  }

  const jsonPromise = response.json();
  let jsonTimeoutId: any;
  const jsonTimeout = new Promise<any>((resolve) => {
    jsonTimeoutId = setTimeout(() => resolve({ timeout: true, type: 'json' }), 5000);
  });
  const jsonResult = await Promise.race([jsonPromise, jsonTimeout]);
  clearTimeout(jsonTimeoutId);
  
  if (jsonResult?.timeout) {
    throw new Error("Response JSON parsing timed out after 5s");
  }
  return jsonResult;
}

export async function getCandidates(page = 1, pageSize = 20) {
  return fetchWithAuth(`/candidates?page=${page}&page_size=${pageSize}`);
}

export async function getCandidate(id: string) {
  return fetchWithAuth(`/candidates/${id}`);
}

export async function uploadResume(file: File) {
  const supabase = createClient();
  const { data: { session } } = await supabase.auth.getSession();

  const formData = new FormData();
  formData.append("file", file);

  const headers = new Headers();
  if (session?.access_token) {
    headers.set("Authorization", `Bearer ${session.access_token}`);
  }

  // NOTE: When using FormData, do NOT set the Content-Type header.
  // The browser will automatically set it to multipart/form-data with the correct boundary.
  const response = await fetch(`${API_URL}/resume/upload`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || errorData.detail || `Upload Failed: ${response.status}`);
  }

  return response.json();
}
