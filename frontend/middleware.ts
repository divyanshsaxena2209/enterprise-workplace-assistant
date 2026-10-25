import { type NextRequest, NextResponse } from "next/server";
import { updateSession } from "@/lib/supabase/middleware";

function canonicalizeCognitoEntry(request: NextRequest) {
  const { pathname } = request.nextUrl;
  // OAuth state and PKCE cookies are host-scoped. Vercel's per-deployment
  // preview URLs can differ from the Cognito callback host; start the flow on
  // the exact configured callback origin so the callback receives its cookies.
  if (pathname !== "/login" && pathname !== "/signup") return null;

  const callbackUri = process.env.COGNITO_REDIRECT_URI;
  if (!callbackUri) return null;

  try {
    const callbackUrl = new URL(callbackUri);
    if (callbackUrl.protocol !== "https:" || callbackUrl.pathname !== "/auth/callback") {
      return null;
    }
    if (request.nextUrl.origin === callbackUrl.origin) return null;

    const canonicalUrl = request.nextUrl.clone();
    canonicalUrl.protocol = callbackUrl.protocol;
    canonicalUrl.host = callbackUrl.host;
    const response = NextResponse.redirect(canonicalUrl);
    response.headers.set("Cache-Control", "no-store");
    return response;
  } catch {
    // Let the auth route show its existing configuration error if the URI is invalid.
    return null;
  }
}

function updateCognitoSessionGate(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isStaticOrApi =
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api/") ||
    pathname.includes(".");
  const isPublicRoute =
    pathname === "/" ||
    pathname === "/login" ||
    pathname === "/signup" ||
    pathname === "/auth/callback" ||
    pathname.startsWith("/auth/callback/");

  if (isStaticOrApi || isPublicRoute || request.cookies.get("guest_mode")?.value === "true") {
    return NextResponse.next();
  }

  // This is only a routing convenience, not an authorization decision. The API,
  // Supabase third-party JWT verification, and RLS policies remain authoritative.
  const hasCognitoSession =
    Boolean(request.cookies.get("ewa_cognito_access_token")?.value) ||
    Boolean(request.cookies.get("ewa_cognito_refresh_token")?.value);
  if (!hasCognitoSession) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  if (pathname === "/login" || pathname === "/signup") {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export async function middleware(request: NextRequest) {
  if (process.env.NEXT_PUBLIC_AUTH_PROVIDER === "cognito") {
    const canonicalEntry = canonicalizeCognitoEntry(request);
    if (canonicalEntry) return canonicalEntry;
    return updateCognitoSessionGate(request);
  }
  return await updateSession(request);
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
