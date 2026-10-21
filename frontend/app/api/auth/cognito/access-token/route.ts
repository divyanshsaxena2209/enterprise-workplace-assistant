import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

const COOKIE_NAMES = [
  "ewa_cognito_access_token",
  "ewa_cognito_id_token",
  "ewa_cognito_access_expires_at",
  "ewa_cognito_refresh_token",
];

function json(body: unknown, status = 200) {
  return NextResponse.json(body, { status, headers: { "Cache-Control": "no-store", Pragma: "no-cache" } });
}

function clearCognitoCookies(response: NextResponse) {
  const secure = process.env.NODE_ENV === "production";
  for (const name of COOKIE_NAMES) {
    response.cookies.set(name, "", {
      httpOnly: true,
      secure,
      sameSite: "lax",
      path: "/",
      maxAge: 0,
    });
  }
}

export async function GET() {
  const store = await cookies();
  const accessToken = store.get("ewa_cognito_access_token")?.value;
  const expiresAt = Number(store.get("ewa_cognito_access_expires_at")?.value || 0);
  if (accessToken && expiresAt > Math.floor(Date.now() / 1000) + 60) {
    return json({ access_token: accessToken, expires_at: expiresAt });
  }

  const refreshToken = store.get("ewa_cognito_refresh_token")?.value;
  const domain = process.env.COGNITO_DOMAIN;
  const clientId = process.env.COGNITO_APP_CLIENT_ID || process.env.NEXT_PUBLIC_COGNITO_APP_CLIENT_ID;
  if (!refreshToken || !domain || !clientId) {
    const response = json({ message: "Your Cognito session has expired. Please sign in again." }, 401);
    clearCognitoCookies(response);
    return response;
  }

  try {
    const domainUrl = new URL(domain);
    if (domainUrl.protocol !== "https:" || (domainUrl.pathname !== "/" && domainUrl.pathname !== "")) {
      throw new Error("Invalid Cognito domain.");
    }
    const tokenHttpResponse = await fetch(`${domainUrl.origin}/oauth2/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "refresh_token",
        client_id: clientId,
        refresh_token: refreshToken,
      }),
      cache: "no-store",
    });
    const data = await tokenHttpResponse.json();
    if (!tokenHttpResponse.ok || typeof data.access_token !== "string") {
      const response = json({ message: "Your Cognito session has expired. Please sign in again." }, 401);
      clearCognitoCookies(response);
      return response;
    }

    const expiresIn = Math.min(Math.max(Number(data.expires_in) || 3600, 60), 86400);
    const nextExpiresAt = Math.floor(Date.now() / 1000) + expiresIn;
    const secure = process.env.NODE_ENV === "production";
    const response = json({ access_token: data.access_token, expires_at: nextExpiresAt });
    response.cookies.set("ewa_cognito_access_token", data.access_token, {
      httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: expiresIn,
    });
    response.cookies.set("ewa_cognito_access_expires_at", String(nextExpiresAt), {
      httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: expiresIn,
    });
    if (typeof data.id_token === "string") {
      response.cookies.set("ewa_cognito_id_token", data.id_token, {
        httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: expiresIn,
      });
    }
    if (typeof data.refresh_token === "string") {
      const refreshMaxAge = Math.min(
        Math.max(Number(process.env.COGNITO_REFRESH_TOKEN_MAX_AGE_SECONDS) || 2592000, 3600),
        31536000,
      );
      response.cookies.set("ewa_cognito_refresh_token", data.refresh_token, {
        httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: refreshMaxAge,
      });
    }
    return response;
  } catch {
    const response = json({ message: "Unable to refresh your Cognito session. Please sign in again." }, 401);
    clearCognitoCookies(response);
    return response;
  }
}
