"use client";

import Link from "next/link";
import { LockKeyhole, ShieldCheck, Sparkles } from "lucide-react";

export default function CognitoLoginPage() {
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
