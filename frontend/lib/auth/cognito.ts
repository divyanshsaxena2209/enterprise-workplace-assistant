"use client";

type CognitoAccessTokenResponse = {
  access_token?: unknown;
  expires_at?: unknown;
};

let cachedToken: string | null = null;
let cachedExpiresAt = 0;
let pendingRequest: Promise<string> | null = null;

/**
 * Fetch a short-lived Cognito access token from a same-origin route.
 * Tokens remain in HttpOnly cookies; this function holds a token only in memory
 * so Supabase's accessToken callback and API requests can authenticate.
 */
export async function getCognitoAccessToken(): Promise<string> {
  if (cachedToken && cachedExpiresAt > Math.floor(Date.now() / 1000) + 45) {
    return cachedToken;
  }
  if (pendingRequest) return pendingRequest;

  pendingRequest = (async () => {
    const response = await fetch("/api/auth/cognito/access-token", {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    const body = (await response.json().catch(() => ({}))) as CognitoAccessTokenResponse;
    if (!response.ok || typeof body.access_token !== "string" || typeof body.expires_at !== "number") {
      cachedToken = null;
      cachedExpiresAt = 0;
      throw new Error("Cognito session is missing or expired. Please sign in again.");
    }
    cachedToken = body.access_token;
    cachedExpiresAt = body.expires_at;
    return cachedToken;
  })();

  try {
    return await pendingRequest;
  } finally {
    pendingRequest = null;
  }
}

export function clearCognitoAccessTokenCache() {
  cachedToken = null;
  cachedExpiresAt = 0;
}
