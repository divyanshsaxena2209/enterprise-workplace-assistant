"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { 
  User, Mail, Lock, Briefcase, Phone, MapPin, 
  FileText, Shield, ArrowRight, ArrowLeft, Loader2, Sparkles, CheckCircle
} from "lucide-react";

export default function SignupPage() {
  const router = useRouter();
  const supabase = createClient();
  
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [signupSuccess, setSignupSuccess] = useState(false);

  // Form Fields
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
    role: "Employee", // Management or Employee
    department: "",
    jobTitle: "",
    employeeId: "",
    phone: "",
    location: "",
    bio: "",
    avatarUrl: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const validateStep = () => {
    setError(null);
    if (step === 1) {
      if (!formData.fullName.trim()) return "Full Name is required.";
      if (!formData.email.trim() || !formData.email.includes("@")) return "A valid work email is required.";
      if (formData.password.length < 6) return "Password must be at least 6 characters.";
      if (formData.password !== formData.confirmPassword) return "Passwords do not match.";
    } else if (step === 2) {
      if (!formData.department.trim()) return "Department is required.";
      if (!formData.jobTitle.trim()) return "Job Title is required.";
      if (formData.role === "Management" && !formData.employeeId.trim()) {
        return "Employee ID is mandatory for Management accounts.";
      }
    }
    return null;
  };

  const handleNext = (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validateStep();
    if (validationError) {
      setError(validationError);
      return;
    }
    setStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setError(null);
    setStep((prev) => prev - 1);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validateStep();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const { data, error: signupError } = await supabase.auth.signUp({
        email: formData.email,
        password: formData.password,
        options: {
          data: {
            full_name: formData.fullName,
            role: formData.role,
            employee_id: formData.employeeId || null,
            department: formData.department,
            job_title: formData.jobTitle,
            phone: formData.phone,
            location: formData.location,
            bio: formData.bio,
            avatar_url: formData.avatarUrl || `https://api.dicebear.com/7.x/adventurer/svg?seed=${encodeURIComponent(formData.fullName)}`,
            is_management_verified: false,
          },
        },
      });

      if (signupError) {
        throw new Error(signupError.message);
      }

      if (data?.user) {
        document.cookie = "guest_mode=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        setSignupSuccess(true);
        setTimeout(() => {
          router.push("/login");
        }, 2500);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An unexpected error occurred during sign up.";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground selection:bg-foreground selection:text-background py-10 px-4">
      <div className="max-w-lg w-full bg-card rounded-2xl shadow-xl border border-border overflow-hidden transition-all duration-300">
        
        {/* Progress Header */}
        <div className="bg-secondary/40 border-b border-border p-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-foreground animate-pulse" />
            <h1 className="text-lg font-bold tracking-tight text-foreground">Workforce Operations Portal</h1>
          </div>
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Step {step} of 3
          </span>
        </div>

        {/* Step Indicator Bar */}
        <div className="w-full bg-secondary h-1">
          <div 
            className="bg-foreground h-1 transition-all duration-300"
            style={{ width: `${(step / 3) * 100}%` }}
          />
        </div>

        <div className="p-8">
          <div className="mb-6">
            <h2 className="text-2xl font-black tracking-tight text-foreground">
              {step === 1 && "Create Your Account"}
              {step === 2 && "Organizational Details"}
              {step === 3 && "Professional Profile"}
            </h2>
            <p className="text-sm text-muted-foreground mt-1.5">
              {step === 1 && "Start by configuring your workspace access credentials."}
              {step === 2 && "Enter your current role and position details."}
              {step === 3 && "Add contact information to complete your onboarding."}
            </p>
          </div>

          {error && !signupSuccess && (
            <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-xs font-medium text-destructive flex items-center gap-3">
              <Shield className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {signupSuccess ? (
            <div className="text-center py-10 space-y-4">
              <div className="w-16 h-16 bg-green-500/20 text-green-500 rounded-full flex items-center justify-center mx-auto mb-4 border border-green-500/30">
                <CheckCircle size={32} />
              </div>
              <h3 className="text-2xl font-bold tracking-tight text-foreground">Profile Created Successfully!</h3>
              <p className="text-sm text-muted-foreground">Redirecting you to the sign-in page...</p>
            </div>
          ) : (
            <form onSubmit={step === 3 ? handleSubmit : handleNext} className="space-y-5">
            
            {/* STEP 1: CREDENTIALS */}
            {step === 1 && (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Full Name</label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
                    <input 
                      type="text" 
                      name="fullName"
                      value={formData.fullName}
                      onChange={handleChange}
                      required
                      suppressHydrationWarning
                      className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                      placeholder="Jane Doe"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Work Email Address</label>
                  <div className="relative">
                    <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
                    <input 
                      type="email" 
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      suppressHydrationWarning
                      className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                      placeholder="jane.doe@company.com"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Password</label>
                    <div className="relative">
                      <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
                      <input 
                        type="password" 
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        required
                        suppressHydrationWarning
                        className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                        placeholder="••••••••"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Confirm Password</label>
                    <div className="relative">
                      <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
                      <input 
                        type="password" 
                        name="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        required
                        suppressHydrationWarning
                        className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                        placeholder="••••••••"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 2: ORGANIZATIONAL DETAILS */}
            {step === 2 && (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Organizational Role</label>
                  <div className="relative">
                    <Shield className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
                    <select
                      name="role"
                      value={formData.role}
                      onChange={handleChange}
                      className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all appearance-none cursor-pointer shadow-sm"
                    >
                      <option value="Employee">Employee</option>
                      <option value="Management">Management</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Department</label>
                    <div className="relative">
                      <Briefcase className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
                      <input 
                        type="text" 
                        name="department"
                        value={formData.department}
                        onChange={handleChange}
                        required
                        className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                        placeholder="Operations, HR, Tech"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Job Title</label>
                    <div className="relative">
                      <Briefcase className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
                      <input 
                        type="text" 
                        name="jobTitle"
                        value={formData.jobTitle}
                        onChange={handleChange}
                        required
                        className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                        placeholder="Lead Architect"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">
                    Employee ID {formData.role === "Management" ? "(Mandatory)" : "(Optional)"}
                  </label>
                  <div className="relative">
                    <FileText className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
                    <input 
                      type="text" 
                      name="employeeId"
                      value={formData.employeeId}
                      onChange={handleChange}
                      required={formData.role === "Management"}
                      className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                      placeholder={formData.role === "Management" ? "MGR-1004" : "EMP-4921"}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* STEP 3: CONTACT & BIO */}
            {step === 3 && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Phone Number</label>
                    <div className="relative">
                      <Phone className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
                      <input 
                        type="text" 
                        name="phone"
                        value={formData.phone}
                        onChange={handleChange}
                        className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                        placeholder="+1 (555) 000-0000"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Location</label>
                    <div className="relative">
                      <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
                      <input 
                        type="text" 
                        name="location"
                        value={formData.location}
                        onChange={handleChange}
                        className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                        placeholder="New York, NY"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Profile Image URL (Optional)</label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
                    <input 
                      type="url" 
                      name="avatarUrl"
                      value={formData.avatarUrl}
                      onChange={handleChange}
                      className="w-full pl-11 pr-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground shadow-sm"
                      placeholder="https://images.unsplash.com/photo-..."
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Short Bio (Optional)</label>
                  <textarea 
                    name="bio"
                    value={formData.bio}
                    onChange={handleChange}
                    rows={3}
                    className="w-full px-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring transition-all placeholder:text-muted-foreground resize-none shadow-sm"
                    placeholder="Brief professional summary..."
                  />
                </div>
              </div>
            )}

            {/* Navigation Controls */}
            <div className="flex gap-4 pt-4">
              {step > 1 && (
                <button
                  type="button"
                  onClick={handleBack}
                  disabled={loading}
                  suppressHydrationWarning
                  className="flex-1 py-2.5 px-4 bg-secondary hover:bg-secondary/80 border border-border text-foreground rounded-lg text-xs font-semibold uppercase tracking-wider transition-all flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
                >
                  <ArrowLeft size={14} />
                  Back
                </button>
              )}
              
              <button
                type="submit"
                disabled={loading}
                suppressHydrationWarning
                className="flex-1 py-2.5 px-4 bg-foreground hover:bg-foreground/90 text-background rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    {step === 3 ? "Complete Registration" : "Next Details"}
                    {step < 3 && <ArrowRight size={14} />}
                  </>
                )}
              </button>
            </div>
          </form>
        )}

          {!signupSuccess && (
            <div className="text-center mt-6">
              <p className="text-xs text-muted-foreground">
                Already have an enterprise account?{" "}
                <Link href="/login" className="font-bold text-foreground hover:underline">
                  Sign In
                </Link>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
