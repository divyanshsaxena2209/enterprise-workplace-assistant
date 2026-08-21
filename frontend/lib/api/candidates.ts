import { createClient } from "@/lib/supabase/client";
const BASE_URL = process.env.NEXT_PUBLIC_API_URL;
if (!BASE_URL) throw new Error("NEXT_PUBLIC_API_URL is not set in the environment variables.");
const API_URL = BASE_URL.includes("/api/v1") ? BASE_URL : `${BASE_URL.replace(/\/$/, "")}/api/v1`;
let cachedAccessToken: string | null = null;
let tokenRefreshPromise: Promise<string> | null = null;
export async function fetchWithAuth(endpoint: string, options: RequestInit & { timeoutMs?: number } = {}) {
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
    if (typeof window !== "undefined") {
      if (!cachedAccessToken) {
        if (!tokenRefreshPromise) {
          tokenRefreshPromise = (async () => {
            const supabase = createClient();
            try {
              const { data, error } = await supabase.auth.getSession();
              if (error || !data?.session?.access_token) {
                throw new Error(error?.message || "User is not authenticated");
              }
              return data.session.access_token;
            } catch (err) {
              throw err;
            }
          })();
        }
        try {
          cachedAccessToken = await tokenRefreshPromise;
        } catch (err) {
          tokenRefreshPromise = null;
          throw err;
        } finally {
          tokenRefreshPromise = null;
        }
      }
      headers["Authorization"] = `Bearer ${cachedAccessToken}`;
    }
  }
  const hasContentType = Object.keys(headers).some(k => k.toLowerCase() === 'content-type');
  if (!hasContentType && typeof options.body === "string") {
    headers["Content-Type"] = "application/json";
  }
  console.log(`[fetchWithAuth] Executing fetch with headers:`, headers);
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
    const ms = options.timeoutMs || 60000;
    fetchTimeoutId = setTimeout(() => resolve({ timeout: true, type: 'fetch' }), ms);
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
    const ms = options.timeoutMs || 60000;
    throw new Error(`Fetch timed out after ${ms / 1000}s`);
  }
  console.log(`[fetchWithAuth] Fetch completed with status:`, response.status);
  if (!response.ok) {
    if (response.status === 401) {
      cachedAccessToken = null;
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || errorData.detail || `API Error: ${response.status}`);
  }
  const jsonPromise = response.json();
  let jsonTimeoutId: any;
  const jsonTimeout = new Promise<any>((resolve) => {
    jsonTimeoutId = setTimeout(() => resolve({ timeout: true, type: 'json' }), 30000);
  });
  const jsonResult = await Promise.race([jsonPromise, jsonTimeout]);
  clearTimeout(jsonTimeoutId);
  if (jsonResult?.timeout) {
    throw new Error("Response JSON parsing timed out after 30s");
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
  const formData = new FormData();
  formData.append("file", file);
  return fetchWithAuth("/resume/upload", {
    method: "POST",
    body: formData,
  });
}
