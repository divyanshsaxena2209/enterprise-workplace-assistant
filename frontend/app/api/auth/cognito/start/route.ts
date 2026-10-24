import { createHash, randomBytes } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

type SignupProfile = {
  full_name: string;
  department: string;
  job_title: string;
  phone?: string;
  location?: string;
  bio?: string;
  avatar_url?: string;
};

function config() {
  const rawDomain = process.env.COGNITO_DOMAIN;
  const clientId = process.env.COGNITO_APP_CLIENT_ID || process.env.NEXT_PUBLIC_COGNITO_APP_CLIENT_ID;
  const redirectUri = process.env.COGNITO_REDIRECT_URI;
  if (!rawDomain || !clientId || !redirectUri) {
    throw new Error("Cognito domain, app client ID, and callback URL must be configured.");
  }
  const domainUrl = new URL(rawDomain);
  const redirectUrl = new URL(redirectUri);
  if (domainUrl.protocol !== "https:" || domainUrl.pathname !== "/" && domainUrl.pathname !== "") {
    throw new Error("COGNITO_DOMAIN must be an HTTPS origin with no path.");
  }
  if (redirectUrl.protocol !== "https:" || redirectUrl.pathname !== "/auth/callback" || redirectUrl.hash) {
    throw new Error("COGNITO_REDIRECT_URI must be the HTTPS /auth/callback URL.");
  }
  return { domain: domainUrl.origin, clientId, redirectUri: redirectUrl.toString(), appOrigin: redirectUrl.origin };
}

const secure = process.env.NODE_ENV === "production";
const cookieOptions = {
  httpOnly: true,
  secure,
  sameSite: "lax" as const,
  path: "/",
  maxAge: 300,
};

function buildAuthorizationUrl(request: NextRequest, profile?: SignupProfile) {
  const cfg = config();
  const verifier = randomBytes(32).toString("base64url");
  const challenge = createHash("sha256").update(verifier).digest("base64url");
  const state = randomBytes(32).toString("base64url");
  const nonce = randomBytes(32).toString("base64url");
  const url = new URL("/oauth2/authorize", cfg.domain);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("client_id", cfg.clientId);
  url.searchParams.set("redirect_uri", cfg.redirectUri);
  url.searchParams.set("scope", "openid email");
  url.searchParams.set("state", state);
  url.searchParams.set("nonce", nonce);
  url.searchParams.set("code_challenge_method", "S256");
  url.searchParams.set("code_challenge", challenge);

  const response = NextResponse.json({ authorization_url: url.toString() });
  response.cookies.set("ewa_cognito_oauth_state", state, cookieOptions);
  response.cookies.set("ewa_cognito_oauth_nonce", nonce, cookieOptions);
  response.cookies.set("ewa_cognito_pkce_verifier", verifier, cookieOptions);
  response.cookies.set("ewa_cognito_redirect_uri", cfg.redirectUri, cookieOptions);
  if (profile) {
    response.cookies.set(
      "ewa_cognito_signup_profile",
      Buffer.from(JSON.stringify(profile), "utf8").toString("base64url"),
      cookieOptions,
    );
  } else {
    response.cookies.set("ewa_cognito_signup_profile", "", { ...cookieOptions, maxAge: 0 });
  }
  response.headers.set("Cache-Control", "no-store");
  return response;
}

function parseSignupProfile(value: unknown): SignupProfile {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Signup profile is required.");
  }
  const raw = value as Record<string, unknown>;
  const required = (key: string, max: number) => {
    const item = raw[key];
    if (typeof item !== "string" || item.trim().length < 1 || item.trim().length > max) {
      throw new Error("Please complete the required employee profile fields.");
    }
    return item.trim();
  };
  const optional = (key: string, max: number) => {
    const item = raw[key];
    if (item === undefined || item === null || item === "") return undefined;
    if (typeof item !== "string" || item.length > max) {
      throw new Error("An optional employee profile field is invalid.");
    }
    return item.trim();
  };
  // Deliberately don't read or accept a role/permission field from the browser.
  return {
    full_name: required("full_name", 128),
    department: required("department", 100),
    job_title: required("job_title", 100),
    phone: optional("phone", 30),
    location: optional("location", 128),
    bio: optional("bio", 500),
    avatar_url: optional("avatar_url", 1024),
  };
}

export async function GET(request: NextRequest) {
  try {
    const response = buildAuthorizationUrl(request);
    const body = await response.json();
    const redirect = NextResponse.redirect(body.authorization_url);
    response.cookies.getAll().forEach((cookie) => redirect.cookies.set(cookie.name, cookie.value, cookie));
    redirect.headers.set("Cache-Control", "no-store");
    return redirect;
  } catch {
    const cfgRedirect = process.env.COGNITO_REDIRECT_URI;
    const base = cfgRedirect ? new URL(cfgRedirect).origin : request.nextUrl.origin;
    return NextResponse.redirect(new URL("/login?error=cognito_not_configured", base));
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const profile = parseSignupProfile(body?.profile);
    return buildAuthorizationUrl(request, profile);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to start Cognito signup.";
    return NextResponse.json({ message }, { status: 400, headers: { "Cache-Control": "no-store" } });
  }
}
