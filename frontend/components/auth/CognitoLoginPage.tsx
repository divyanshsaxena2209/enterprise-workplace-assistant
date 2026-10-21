"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { LockKeyhole, ShieldCheck, Sparkles } from "lucide-react";

const LOGIN_ERRORS: Record<string, string> = {
  cognito_not_configured: "Cognito staging is not configured yet. Please try again after setup is complete.",
  cognito_signin_cancelled: "Sign-in was cancelled. You can try again.",
  cognito_callback_invalid: "The sign-in response could not be validated. Please restart sign-in.",
  cognito_token_exchange_failed: "Cognito could not complete sign-in. Please try again.",
  cognito_staging_backend_not_configured: "The staging API is not configured for Cognito yet.",
  profile_not_found: "No matching account profile was found. Use Create an account to finish employee signup.",
  cognito_account_link_failed: "We could not connect this Cognito account to a profile. Please try again or contact support.",
};

export default function CognitoLoginPage() {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const key = new URLSearchParams(window.location.search).get("error");
    if (key) setError(LOGIN_ERRORS[key] || "Sign-in could not be completed. Please try again.");
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground px-4">
      <div className="w-full max-w-md rounded-2xl border border-border bg-card p-8 shadow-xl">
        <div className="mb-8 text-center">
          <div className="mb-3 inline-flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-foreground" />
            <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Workforce OS</span>
          </div>
          <h1 className="text-2xl font-black tracking-tight">Welcome back</h1>
          <p className="mt-2 text-sm text-muted-foreground">Sign in securely with your organization account.</p>
        </div>
        {error && (
          <div role="alert" className="mb-5 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}
        <a href="/api/auth/cognito/start" className="flex w-full items-center justify-center gap-2 rounded-lg border border-foreground bg-foreground px-4 py-3 text-xs font-bold uppercase tracking-wider text-background transition-opacity hover:opacity-90">
          <LockKeyhole className="h-4 w-4" />
          Continue with Cognito
        </a>
        <p className="mt-5 flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <ShieldCheck className="h-4 w-4" />
          Protected sign-in with Amazon Cognito
        </p>
        <p className="mt-6 text-center text-sm text-muted-foreground">
          Don&apos;t have an account? <Link href="/signup" className="font-semibold text-foreground underline underline-offset-4">Create an account</Link>
        </p>
      </div>
    </div>
  );
}
