"use client";
import React, { createContext, useContext, useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { checkIsHired } from "@/lib/api/applications";
interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  employee_id: string;
  department: string;
  job_title: string;
  phone: string;
  location: string;
  bio: string;
  avatar_url: string;
  created_at: string;
}
interface UserContextType {
  profile: UserProfile | null;
  loading: boolean;
  isHired: boolean;
  accessToken: string | null;
  refreshProfile: () => Promise<void>;
}
const guestProfile: UserProfile = {
  id: "guest-id",
  email: "guest@company.com",
  full_name: "Guest User",
  role: "GUEST",
  employee_id: "GUEST-001",
  department: "Testing",
  job_title: "Guest Tester",
  phone: "123-456-7890",
  location: "Remote",
  bio: "Guest account for testing.",
  avatar_url: "",
  created_at: new Date().toISOString(),
};
const UserContext = createContext<UserContextType | undefined>(undefined);
export function UserProvider({ children }: { children: React.ReactNode }) {
  const supabase = createClient();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [isHired, setIsHired] = useState(false);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const fetchProfile = React.useCallback(async (sessionArg?: any) => {
    try {
      let session = sessionArg;
      if (sessionArg === undefined) {
        const { data } = await supabase.auth.getSession();
        session = data?.session;
      }
      const isGuestMode = typeof document !== 'undefined' && document.cookie.includes('guest_mode=true');
      if (!session?.user) {
        if (isGuestMode) {
          setProfile(guestProfile);
          setAccessToken("guest");
        } else {
          setProfile(null);
          setAccessToken(null);
        }
        setLoading(false);
        return;
      }
      setAccessToken(session.access_token || null);
      const { data, error } = await supabase
        .from("profiles")
        .select("*")
        .eq("id", session.user.id)
        .single();
      if (error) {
        console.error("Error fetching user profile:", error);
        setProfile(null);
        setIsHired(false);
      } else {
        setProfile(data);
        if (data.role === "EMPLOYEE" && !data.employee_id) {
          const hiredStatus = await checkIsHired();
          setIsHired(hiredStatus);
        } else if (data.role === "MANAGEMENT" || data.employee_id) {
          setIsHired(true);
        }
      }
    } catch (err) {
      console.error("Failed to fetch session/profile", err);
      setProfile(null);
    } finally {
      setLoading(false);
    }
  }, [supabase]);

  useEffect(() => {
    let mounted = true;
    let subscription: { unsubscribe: () => void } | null = null;

    const initializeAuth = async () => {
      // Finish restoring the persisted session and initial profile before
      // subscribing. Registering this listener in the same tick as getSession()
      // can deadlock Supabase auth's Web Lock when a session needs refreshing.
      await fetchProfile();
      if (!mounted) return;

      const { data } = supabase.auth.onAuthStateChange((event: any, session: any) => {
        if (event === "SIGNED_IN" || event === "TOKEN_REFRESHED") {
          // Keep the auth callback synchronous; do profile/network work after
          // Supabase has completed its internal auth lock operation.
          setTimeout(() => {
            if (mounted) void fetchProfile(session);
          }, 0);
        } else if (event === "SIGNED_OUT") {
          const isGuestMode = typeof document !== 'undefined' && document.cookie.includes('guest_mode=true');
          if (isGuestMode) {
            setProfile(guestProfile);
            setAccessToken("guest");
          } else {
            setProfile(null);
            setAccessToken(null);
          }
          setLoading(false);
        }
      });
      subscription = data.subscription;
    };

    void initializeAuth();

    return () => {
      mounted = false;
      subscription?.unsubscribe();
    };
  }, [fetchProfile, supabase]);

  return (
    <UserContext.Provider value={{ profile, loading, isHired, accessToken, refreshProfile: fetchProfile }}>
      {children}
    </UserContext.Provider>
  );
}
export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
}
