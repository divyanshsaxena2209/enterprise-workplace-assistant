"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Briefcase, Loader2, MapPin, Phone, Shield, User } from "lucide-react";

export default function CognitoSignupForm() {
  const [fullName, setFullName] = useState("");
  const [department, setDepartment] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [phone, setPhone] = useState("");
  const [location, setLocation] = useState("");
  const [bio, setBio] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/auth/cognito/start", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        credentials: "same-origin",
        cache: "no-store",
        body: JSON.stringify({
          profile: {
            full_name: fullName,
            department,
            job_title: jobTitle,
            phone: phone || undefined,
            location: location || undefined,
            bio: bio || undefined,
          },
        }),
      });
      const result = await response.json();
      if (!response.ok || typeof result.authorization_url !== "string") {
        throw new Error(result.message || "Unable to start Cognito signup.");
      }
      window.location.assign(result.authorization_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to start signup.");
      setLoading(false);
    }
  }

  const inputClass = "w-full rounded-lg border border-border bg-secondary/50 px-4 py-3 text-sm text-foreground shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring";

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground px-4 py-10">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-8 shadow-xl">
        <div className="mb-7 text-center">
          <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Workforce Operations Portal</p>
          <h1 className="mt-3 text-2xl font-black tracking-tight">Create your employee profile</h1>
          <p className="mt-2 text-sm text-muted-foreground">Your account credentials will be created securely by Amazon Cognito.</p>
        </div>
        {error && (
          <div className="mb-5 flex items-center gap-3 rounded-lg border border-destructive/20 bg-destructive/10 p-4 text-sm text-destructive">
            <Shield className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Full name</span>
            <span className="relative block">
              <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input className={inputClass + " pl-10"} value={fullName} onChange={(event) => setFullName(event.target.value)} maxLength={128} required autoComplete="name" placeholder="Jane Doe" />
            </span>
          </label>
          <label className="block space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Department</span>
            <span className="relative block">
              <Briefcase className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input className={inputClass + " pl-10"} value={department} onChange={(event) => setDepartment(event.target.value)} maxLength={100} required placeholder="Engineering" />
            </span>
          </label>
          <label className="block space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Job title</span>
            <input className={inputClass} value={jobTitle} onChange={(event) => setJobTitle(event.target.value)} maxLength={100} required placeholder="Software Engineer" />
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Phone (optional)</span>
              <span className="relative block">
                <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input className={inputClass + " pl-10"} value={phone} onChange={(event) => setPhone(event.target.value)} maxLength={30} autoComplete="tel" placeholder="+91..." />
              </span>
            </label>
            <label className="block space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Location (optional)</span>
              <span className="relative block">
                <MapPin className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input className={inputClass + " pl-10"} value={location} onChange={(event) => setLocation(event.target.value)} maxLength={128} placeholder="City / remote" />
              </span>
            </label>
          </div>
          <label className="block space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Bio (optional)</span>
            <textarea className={inputClass + " min-h-20 resize-y"} value={bio} onChange={(event) => setBio(event.target.value)} maxLength={500} placeholder="A short introduction" />
          </label>
          <div className="rounded-xl border border-border bg-secondary/30 p-4">
            <p className="mb-3 text-xs font-bold uppercase tracking-wider text-muted-foreground">Access level</p>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg border border-foreground bg-foreground px-3 py-3 text-background">
                <p className="text-sm font-bold">Employee</p>
                <p className="mt-1 text-[11px] opacity-80">Available for self-service signup</p>
              </div>
              <div className="rounded-lg border border-border bg-card px-3 py-3 text-muted-foreground">
                <p className="text-sm font-bold">Management</p>
                <p className="mt-1 text-[11px]">Assigned by an administrator</p>
              </div>
            </div>
          </div>
          <button type="submit" disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-lg border border-foreground bg-foreground px-4 py-3 text-xs font-bold uppercase tracking-wider text-background transition-opacity hover:opacity-90 disabled:opacity-50">
            {loading ? <><Loader2 className="h-4 w-4 animate-spin" /> Connecting to Cognito…</> : "Continue to secure signup"}
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-muted-foreground">
          Already have an account? <Link href="/login" className="font-semibold text-foreground underline underline-offset-4">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
