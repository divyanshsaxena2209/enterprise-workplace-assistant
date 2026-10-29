import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

function clearCookies(response: NextResponse) {
  const secure = process.env.NODE_ENV === "production";
  for (const name of [
    "ewa_cognito_access_token",
    "ewa_cognito_id_token",
    "ewa_cognito_access_expires_at",
    "ewa_cognito_refresh_token",
    "ewa_cognito_oauth_state",
    "ewa_cognito_oauth_nonce",
    "ewa_cognito_pkce_verifier",
    "ewa_cognito_redirect_uri",
    "ewa_cognito_signup_profile",
  ]) {
    response.cookies.set(name, "", {
      httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: 0,
    });
  }
}

export async function GET(request: NextRequest) {
  const store = await cookies();
  const refreshToken = store.get("ewa_cognito_refresh_token")?.value;
  const domain = process.env.COGNITO_DOMAIN;
  const clientId = process.env.COGNITO_APP_CLIENT_ID || process.env.NEXT_PUBLIC_COGNITO_APP_CLIENT_ID;
  const signOutUri = process.env.COGNITO_SIGN_OUT_URI || process.env.COGNITO_REDIRECT_URI;
  if (refreshToken && domain && clientId) {
    try {
      const domainUrl = new URL(domain);
      if (domainUrl.protocol === "https:" && (domainUrl.pathname === "/" || domainUrl.pathname === "")) {
        await fetch(`${domainUrl.origin}/oauth2/revoke`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({ token: refreshToken, client_id: clientId }),
          cache: "no-store",
        });
      }
    } catch {
      // Local logout still clears the browser session if revocation is unavailable.
    }
  }

  let target = new URL("/login", request.nextUrl.origin);
  if (domain && clientId && signOutUri) {
    try {
      const domainUrl = new URL(domain);
      const signOutUrl = new URL(signOutUri);
      if (domainUrl.protocol === "https:" && signOutUrl.protocol === "https:") {
        target = new URL("/logout", domainUrl.origin);
        target.searchParams.set("client_id", clientId);
        target.searchParams.set("logout_uri", signOutUrl.toString());
      }
    } catch {
      // Fall back to the app login page.
    }
  }

  const response = NextResponse.redirect(target);
  clearCookies(response);
  response.headers.set("Cache-Control", "no-store");
  return response;
}
