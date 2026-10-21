import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

const temporaryCookieNames = [
  "ewa_cognito_oauth_state",
  "ewa_cognito_oauth_nonce",
  "ewa_cognito_pkce_verifier",
  "ewa_cognito_redirect_uri",
  "ewa_cognito_signup_profile",
];

function redirectUriFromEnv() {
  const redirectUri = process.env.COGNITO_REDIRECT_URI;
  if (!redirectUri) throw new Error("Cognito callback URL is not configured.");
  const url = new URL(redirectUri);
  if (url.protocol !== "https:" || url.pathname !== "/auth/callback" || url.hash) {
    throw new Error("Invalid Cognito callback URL configuration.");
  }
  return url.toString();
}

function loginError(request: NextRequest, code: string) {
  const configuredUri = process.env.COGNITO_REDIRECT_URI;
  const origin = configuredUri ? new URL(configuredUri).origin : request.nextUrl.origin;
  return NextResponse.redirect(new URL(`/login?error=${encodeURIComponent(code)}`, origin));
}

function clearTemporaryCookies(response: NextResponse) {
  const secure = process.env.NODE_ENV === "production";
  for (const name of temporaryCookieNames) {
    response.cookies.set(name, "", {
      httpOnly: true,
      secure,
      sameSite: "lax",
      path: "/",
      maxAge: 0,
    });
  }
}

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const returnedState = request.nextUrl.searchParams.get("state");
  const oauthError = request.nextUrl.searchParams.get("error");
  const store = await cookies();
  const expectedState = store.get("ewa_cognito_oauth_state")?.value;
  const nonce = store.get("ewa_cognito_oauth_nonce")?.value;
  const verifier = store.get("ewa_cognito_pkce_verifier")?.value;
  const savedRedirectUri = store.get("ewa_cognito_redirect_uri")?.value;
  const pendingProfileEncoded = store.get("ewa_cognito_signup_profile")?.value;

  if (oauthError || !code || !returnedState || !expectedState || returnedState !== expectedState ||
      !nonce || !verifier || !savedRedirectUri) {
    const response = loginError(request, oauthError ? "cognito_signin_cancelled" : "cognito_callback_invalid");
    clearTemporaryCookies(response);
    return response;
  }

  let cfg: { domain: string; clientId: string; redirectUri: string; appOrigin: string };
  try {
    const domain = process.env.COGNITO_DOMAIN;
    const clientId = process.env.COGNITO_APP_CLIENT_ID || process.env.NEXT_PUBLIC_COGNITO_APP_CLIENT_ID;
    const redirectUri = redirectUriFromEnv();
    if (!domain || !clientId || savedRedirectUri !== redirectUri) throw new Error("Cognito OAuth configuration mismatch.");
    const domainUrl = new URL(domain);
    if (domainUrl.protocol !== "https:" || (domainUrl.pathname !== "/" && domainUrl.pathname !== "")) {
      throw new Error("Invalid Cognito domain configuration.");
    }
    cfg = { domain: domainUrl.origin, clientId, redirectUri, appOrigin: new URL(redirectUri).origin };
  } catch {
    const response = loginError(request, "cognito_not_configured");
    clearTemporaryCookies(response);
    return response;
  }

  let tokenResponse: {
    access_token?: string;
    id_token?: string;
    refresh_token?: string;
    expires_in?: number;
    token_type?: string;
    error?: string;
  };
  try {
    const form = new URLSearchParams({
      grant_type: "authorization_code",
      client_id: cfg.clientId,
      code,
      redirect_uri: cfg.redirectUri,
      code_verifier: verifier,
    });
    const tokenHttpResponse = await fetch(`${cfg.domain}/oauth2/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
      cache: "no-store",
    });
    tokenResponse = await tokenHttpResponse.json();
    if (!tokenHttpResponse.ok || !tokenResponse.access_token || !tokenResponse.id_token) {
      throw new Error("Cognito token exchange failed.");
    }
  } catch {
    const response = loginError(request, "cognito_token_exchange_failed");
    clearTemporaryCookies(response);
    return response;
  }

  const linkEndpoint = process.env.COGNITO_LINK_API_URL;
  if (!linkEndpoint) {
    const response = loginError(request, "cognito_staging_backend_not_configured");
    clearTemporaryCookies(response);
    return response;
  }

  try {
    const linkUrl = new URL(linkEndpoint);
    if (linkUrl.protocol !== "https:") throw new Error("Cognito link endpoint must use HTTPS.");
    let profile: Record<string, string> | undefined;
    if (pendingProfileEncoded) {
      const parsed: unknown = JSON.parse(Buffer.from(pendingProfileEncoded, "base64url").toString("utf8"));
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("Invalid signup profile.");
      profile = parsed as Record<string, string>;
    }
    const linkResponse = await fetch(linkUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_token: tokenResponse.id_token, nonce, ...(profile ? { profile } : {}) }),
      cache: "no-store",
    });
    if (!linkResponse.ok) {
      // Do not include backend response bodies, user attributes, or tokens in logs or URLs.
      const response = loginError(request, linkResponse.status === 404 ? "profile_not_found" : "cognito_account_link_failed");
      clearTemporaryCookies(response);
      return response;
    }
  } catch {
    const response = loginError(request, "cognito_account_link_failed");
    clearTemporaryCookies(response);
    return response;
  }

  const expiresIn = Math.min(Math.max(Number(tokenResponse.expires_in) || 3600, 60), 86400);
  const refreshMaxAge = Math.min(
    Math.max(Number(process.env.COGNITO_REFRESH_TOKEN_MAX_AGE_SECONDS) || 2592000, 3600),
    31536000,
  );
  const secure = process.env.NODE_ENV === "production";
  const response = NextResponse.redirect(new URL("/dashboard", cfg.appOrigin));
  response.cookies.set("ewa_cognito_access_token", tokenResponse.access_token!, {
    httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: expiresIn,
  });
  response.cookies.set("ewa_cognito_id_token", tokenResponse.id_token!, {
    httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: expiresIn,
  });
  response.cookies.set("ewa_cognito_access_expires_at", String(Math.floor(Date.now() / 1000) + expiresIn), {
    httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: expiresIn,
  });
  if (tokenResponse.refresh_token) {
    response.cookies.set("ewa_cognito_refresh_token", tokenResponse.refresh_token, {
      httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: refreshMaxAge,
    });
  }
  clearTemporaryCookies(response);
  response.headers.set("Cache-Control", "no-store");
  return response;
}
