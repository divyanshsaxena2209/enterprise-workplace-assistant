"use client";

import React, { useState, useEffect } from "react";
import { useUser } from "@/lib/context/UserContext";
import { createClient } from "@/lib/supabase/client";
import { 
  User, Mail, Briefcase, Phone, MapPin, 
  FileText, Shield, Loader2, Edit3, Check
} from "lucide-react";

export default function ProfilePage() {
  const { profile, loading, refreshProfile } = useUser();
  const supabase = createClient();
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    full_name: "",
    department: "",
    job_title: "",
    phone: "",
    location: "",
    bio: "",
    avatar_url: "",
  });

  useEffect(() => {
    if (profile) {
      setFormData({
        full_name: profile.full_name || "",
        department: profile.department || "",
        job_title: profile.job_title || "",
        phone: profile.phone || "",
        location: profile.location || "",
        bio: profile.bio || "",
        avatar_url: profile.avatar_url || "",
      });
    }
  }, [profile]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
        <h2 className="text-xl font-bold">Profile Not Found</h2>
        <p className="text-muted-foreground text-sm max-w-md">We couldn't load your profile. Please make sure you are logged in, or try refreshing the page.</p>
      </div>
    );
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const { error: updateError } = await supabase
        .from("profiles")
        .update({
          full_name: formData.full_name,
          department: formData.department,
          job_title: formData.job_title,
          phone: formData.phone,
          location: formData.location,
          bio: formData.bio,
          avatar_url: formData.avatar_url,
        })
        .eq("id", profile.id);

      if (updateError) throw updateError;
      
      await refreshProfile();
      setIsEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-6">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Personnel Profile</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage your enterprise identity and preferences.</p>
        </div>
        <button
          onClick={() => isEditing ? handleSave() : setIsEditing(true)}
          disabled={saving}
          className={`py-2 px-4 rounded-lg text-xs font-bold uppercase tracking-wider flex items-center gap-2 transition-all shadow-sm ${
            isEditing 
              ? "bg-foreground text-background hover:bg-foreground/90" 
              : "bg-secondary text-foreground hover:bg-secondary/80 border border-border"
          }`}
        >
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : isEditing ? <Check className="w-4 h-4" /> : <Edit3 className="w-4 h-4" />}
          {isEditing ? "Save Changes" : "Edit Profile"}
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-xs font-medium text-destructive flex items-center gap-3">
          <Shield className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Left Column: Avatar & Quick Info */}
        <div className="col-span-1 space-y-6">
          <div className="bg-card border border-border rounded-2xl p-6 text-center shadow-sm">
            <div className="relative w-32 h-32 mx-auto mb-4 group">
              <img 
                src={isEditing ? formData.avatar_url : (profile.avatar_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${encodeURIComponent(profile.full_name)}`)}
                alt={profile.full_name}
                className="w-full h-full rounded-full object-cover border-4 border-background shadow-md"
              />
            </div>
            
            {isEditing && (
              <div className="mb-4">
                <input
                  type="text"
                  name="avatar_url"
                  value={formData.avatar_url}
                  onChange={handleChange}
                  placeholder="Avatar URL"
                  className="w-full px-3 py-2 text-xs rounded border border-border bg-secondary/50 focus:outline-none"
                />
              </div>
            )}

            <h2 className="font-bold text-lg">{profile.full_name}</h2>
            <div className="inline-flex items-center gap-1 mt-1 text-xs font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-secondary text-secondary-foreground border border-border/50">
              <Shield className="w-3 h-3" />
              {profile.role}
            </div>
          </div>

          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-4 border-b border-border pb-2">Read-Only Details</h3>
            
            <div className="flex items-start gap-3 text-sm">
              <Mail className="w-4 h-4 text-muted-foreground mt-0.5" />
              <div>
                <p className="font-medium text-foreground">{profile.email}</p>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mt-0.5">Primary Email</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 text-sm">
              <FileText className="w-4 h-4 text-muted-foreground mt-0.5" />
              <div>
                <p className="font-medium text-foreground">{profile.employee_id || "N/A"}</p>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mt-0.5">Employee ID</p>
              </div>
            </div>

            <div className="flex items-start gap-3 text-sm">
              <User className="w-4 h-4 text-muted-foreground mt-0.5" />
              <div>
                <p className="font-medium text-foreground">{new Date(profile.created_at).toLocaleDateString()}</p>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mt-0.5">Joined Date</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Editable Info */}
        <div className="col-span-1 md:col-span-2 space-y-6">
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-6">
            <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground border-b border-border pb-2">Organizational Details</h3>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Full Name</label>
                {isEditing ? (
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleChange}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-secondary/50 text-sm focus:outline-none focus:border-ring"
                  />
                ) : (
                  <p className="text-sm font-medium">{profile.full_name}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Department</label>
                {isEditing ? (
                  <input
                    type="text"
                    name="department"
                    value={formData.department}
                    onChange={handleChange}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-secondary/50 text-sm focus:outline-none focus:border-ring"
                  />
                ) : (
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Briefcase className="w-4 h-4 text-muted-foreground" />
                    {profile.department || "Not specified"}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Job Title</label>
                {isEditing ? (
                  <input
                    type="text"
                    name="job_title"
                    value={formData.job_title}
                    onChange={handleChange}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-secondary/50 text-sm focus:outline-none focus:border-ring"
                  />
                ) : (
                  <p className="text-sm font-medium">{profile.job_title || "Not specified"}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Location</label>
                {isEditing ? (
                  <input
                    type="text"
                    name="location"
                    value={formData.location}
                    onChange={handleChange}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-secondary/50 text-sm focus:outline-none focus:border-ring"
                  />
                ) : (
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <MapPin className="w-4 h-4 text-muted-foreground" />
                    {profile.location || "Not specified"}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Phone</label>
                {isEditing ? (
                  <input
                    type="text"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-secondary/50 text-sm focus:outline-none focus:border-ring"
                  />
                ) : (
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Phone className="w-4 h-4 text-muted-foreground" />
                    {profile.phone || "Not specified"}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground border-b border-border pb-2">Biography</h3>
            
            {isEditing ? (
              <textarea
                name="bio"
                value={formData.bio}
                onChange={handleChange}
                rows={4}
                className="w-full px-3 py-2 rounded-lg border border-border bg-secondary/50 text-sm focus:outline-none focus:border-ring resize-none"
              />
            ) : (
              <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">
                {profile.bio || "No biography provided."}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
