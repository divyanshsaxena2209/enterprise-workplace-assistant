"use client";

import React, { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
  User, Mail, Phone, MapPin, Briefcase, 
  FileText, Shield, Calendar, Edit3, Save, X, Loader2, Sparkles, AlertCircle
} from "lucide-react";

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

export default function ProfilePage() {
  const supabase = createClient();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Edit states
  const [editForm, setEditForm] = useState({
    fullName: "",
    phone: "",
    location: "",
    bio: "",
    department: "",
    jobTitle: "",
    avatarUrl: "",
  });

  const fetchProfile = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error("No authenticated user session found.");

      const { data, error: fetchError } = await supabase
        .from("profiles")
        .select("*")
        .eq("id", user.id)
        .single();

      if (fetchError) throw fetchError;

      setProfile(data);
      setEditForm({
        fullName: data.full_name || "",
        phone: data.phone || "",
        location: data.location || "",
        bio: data.bio || "",
        department: data.department || "",
        jobTitle: data.job_title || "",
        avatarUrl: data.avatar_url || "",
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load user profile.";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [supabase]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const handleEditChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setEditForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error("No authenticated session.");

      const { error: updateError } = await supabase
        .from("profiles")
        .update({
          full_name: editForm.fullName,
          phone: editForm.phone,
          location: editForm.location,
          bio: editForm.bio,
          department: editForm.department,
          job_title: editForm.jobTitle,
          avatar_url: editForm.avatarUrl,
          updated_at: new Date().toISOString(),
        })
        .eq("id", user.id);

      if (updateError) throw updateError;

      setSuccess("Profile settings successfully updated and saved.");
      setEditing(false);
      await fetchProfile();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to save profile changes.";
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Loading profile records...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-10">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-foreground flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-foreground" />
            Personnel Profile
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Manage credentials, organizational identifiers, and bio.</p>
        </div>
        {!editing && (
          <button
            onClick={() => setEditing(true)}
            className="flex items-center gap-2 bg-foreground hover:bg-foreground/90 text-background px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all shadow-sm"
          >
            <Edit3 size={14} />
            Modify Profile
          </button>
        )}
      </div>

      {success && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs font-semibold text-emerald-500 flex items-center gap-3">
          <Save className="w-4 h-4 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-xs font-semibold text-destructive flex items-center gap-3">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {profile && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Card Left: Profile Info Details */}
          <div className="bg-card border border-border rounded-2xl p-8 space-y-6 flex flex-col items-center text-center shadow-sm">
            <div className="relative">
              <img 
                src={profile.avatar_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${encodeURIComponent(profile.full_name)}`}
                alt={profile.full_name} 
                className="w-32 h-32 rounded-full border-2 border-border object-cover bg-secondary"
              />
              <span className={`absolute bottom-2 right-2 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm ${
                profile.role === "Management" 
                  ? "bg-foreground text-background border-border" 
                  : "bg-secondary text-muted-foreground border-border"
              }`}>
                {profile.role}
              </span>
            </div>

            <div className="space-y-1">
              <h3 className="text-xl font-bold tracking-tight text-foreground">{profile.full_name}</h3>
              <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">{profile.job_title || "Designation Pending"}</p>
              <p className="text-xs text-muted-foreground">{profile.department || "No Department Assigned"}</p>
            </div>

            <div className="w-full h-px bg-border/50"></div>

            <div className="w-full space-y-3.5 text-left text-xs font-medium text-muted-foreground">
              <div className="flex items-center gap-3">
                <Mail size={14} className="text-foreground" />
                <span className="truncate">{profile.email}</span>
              </div>
              {profile.employee_id && (
                <div className="flex items-center gap-3">
                  <FileText size={14} className="text-foreground" />
                  <span>Employee ID: <span className="font-bold text-foreground">{profile.employee_id}</span></span>
                </div>
              )}
              <div className="flex items-center gap-3">
                <Calendar size={14} className="text-foreground" />
                <span>Joined {new Date(profile.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}</span>
              </div>
            </div>
          </div>

          {/* Card Right: Profile View/Edit Form */}
          <div className="bg-card border border-border rounded-2xl p-8 lg:col-span-2 shadow-sm">
            {editing ? (
              <form onSubmit={handleSave} className="space-y-6">
                <div className="border-b border-border/50 pb-4">
                  <h3 className="font-bold text-sm uppercase tracking-wider text-foreground">Personnel Profile Modifications</h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div>
                    <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Full Name</label>
                    <div className="relative">
                      <User className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={14} />
                      <input 
                        type="text" 
                        name="fullName"
                        value={editForm.fullName}
                        onChange={handleEditChange}
                        required
                        className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Avatar Image URL</label>
                    <div className="relative">
                      <User className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={14} />
                      <input 
                        type="url" 
                        name="avatarUrl"
                        value={editForm.avatarUrl}
                        onChange={handleEditChange}
                        className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Department</label>
                    <div className="relative">
                      <Briefcase className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={14} />
                      <input 
                        type="text" 
                        name="department"
                        value={editForm.department}
                        onChange={handleEditChange}
                        className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Job Title</label>
                    <div className="relative">
                      <Briefcase className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={14} />
                      <input 
                        type="text" 
                        name="jobTitle"
                        value={editForm.jobTitle}
                        onChange={handleEditChange}
                        className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Phone Number</label>
                    <div className="relative">
                      <Phone className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={14} />
                      <input 
                        type="text" 
                        name="phone"
                        value={editForm.phone}
                        onChange={handleEditChange}
                        className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Location</label>
                    <div className="relative">
                      <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={14} />
                      <input 
                        type="text" 
                        name="location"
                        value={editForm.location}
                        onChange={handleEditChange}
                        className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Personal Biography</label>
                  <textarea 
                    name="bio"
                    value={editForm.bio}
                    onChange={handleEditChange}
                    rows={4}
                    className="w-full px-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground resize-none shadow-sm"
                  />
                </div>

                <div className="flex gap-4 pt-2">
                  <button
                    type="button"
                    onClick={() => setEditing(false)}
                    disabled={saving}
                    className="flex-1 py-2.5 px-4 bg-secondary hover:bg-secondary/80 border border-border text-foreground rounded-lg text-xs font-semibold uppercase tracking-wider transition-all flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
                  >
                    <X size={14} />
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="flex-1 py-2.5 px-4 bg-foreground hover:bg-foreground/90 text-background rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
                  >
                    {saving ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        Saving Changes...
                      </>
                    ) : (
                      <>
                        <Save size={14} />
                        Save Profile
                      </>
                    )}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-6">
                <div className="border-b border-border/50 pb-4">
                  <h3 className="font-bold text-sm uppercase tracking-wider text-foreground font-sans">Professional Summary</h3>
                </div>
                
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">Biography</h4>
                  <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                    {profile.bio || "No biography provided. Click 'Modify Profile' to share a professional overview."}
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-4">
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">Organizational Team</h4>
                    <div className="flex items-center gap-2">
                      <Briefcase size={14} className="text-foreground" />
                      <span className="text-sm text-foreground font-medium">{profile.department || "Unassigned Team"}</span>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">Official Position</h4>
                    <div className="flex items-center gap-2">
                      <Briefcase size={14} className="text-foreground" />
                      <span className="text-sm text-foreground font-medium">{profile.job_title || "Designation Pending"}</span>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">Primary Contact</h4>
                    <div className="flex items-center gap-2">
                      <Phone size={14} className="text-foreground" />
                      <span className="text-sm text-foreground font-medium">{profile.phone || "No phone linked"}</span>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">Geographic Location</h4>
                    <div className="flex items-center gap-2">
                      <MapPin size={14} className="text-foreground" />
                      <span className="text-sm text-foreground font-medium">{profile.location || "No location linked"}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

        </div>
      )}

    </div>
  );
}
