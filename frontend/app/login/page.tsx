"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Mail, Lock, Shield, Loader2, Sparkles } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const supabase = createClient();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const { data, error: loginError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (loginError) {
        throw new Error(loginError.message);
      }

      if (data?.user) {
        router.push("/dashboard");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Invalid credentials. Please verify your email and password.";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleGuestLogin = () => {
    document.cookie = "guest_mode=true; path=/";
    router.push("/dashboard");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground selection:bg-foreground selection:text-background px-4">
      <div className="max-w-md w-full p-8 bg-card rounded-2xl shadow-xl border border-border">
        
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-3">
            <Sparkles className="w-5 h-5 text-foreground animate-pulse" />
            <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Workforce OS</span>
          </div>
          <h1 className="text-2xl font-black tracking-tight text-foreground">Welcome Back</h1>
          <p className="text-xs text-muted-foreground mt-2">Sign in to your organizational portal</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-xs font-medium text-destructive flex items-center gap-3">
            <Shield className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Work Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm" 
                placeholder="you@company.com"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm" 
                placeholder="••••••••"
              />
            </div>
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full py-2.5 px-4 bg-foreground hover:bg-foreground/90 text-background rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Signing In...
              </>
            ) : (
              "Sign In"
            )}
          </button>

          <div className="relative flex py-2 items-center">
            <div className="flex-grow border-t border-border"></div>
            <span className="flex-shrink-0 mx-4 text-muted-foreground text-xs font-medium uppercase">Or</span>
            <div className="flex-grow border-t border-border"></div>
          </div>

          <button 
            type="button" 
            onClick={handleGuestLogin}
            className="w-full py-2.5 px-4 bg-secondary hover:bg-secondary/80 text-secondary-foreground rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-2 shadow-sm border border-border"
          >
            Continue as Guest (Testing)
          </button>
        </form>

        <div className="text-center mt-6">
          <p className="text-xs text-muted-foreground">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="font-bold text-foreground hover:underline">
              Create Account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
