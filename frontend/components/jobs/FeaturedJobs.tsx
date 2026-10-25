"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, BriefcaseBusiness, MapPin } from "lucide-react";
import { supabase } from "@/lib/supabase";

type PublicJob = {
  id: string;
  title: string;
  department: string | null;
  location: string | null;
  employment_type: string | null;
  description: string | null;
  salary_range: string | null;
  created_at: string;
};

export default function FeaturedJobs({ publicLanding = false }: { publicLanding?: boolean }) {
  const [jobs, setJobs] = useState<PublicJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadPublishedJobs() {
      try {
        const { data, error } = await supabase
          .from("published_job_cards")
          .select("id,title,department,location,employment_type,description,salary_range,created_at")
          .order("created_at", { ascending: false })
          .limit(4);
        if (error) throw error;
        if (!cancelled) setJobs((data || []) as PublicJob[]);
      } catch {
        if (!cancelled) setFailed(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadPublishedJobs();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="relative max-w-7xl mx-auto px-6 py-20 border-t border-white/5">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-5 mb-8">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground mb-3">Recruiting &amp; Hiring</p>
          <h2 className="text-3xl md:text-4xl font-black tracking-tight text-white">Current opportunities</h2>
          <p className="mt-3 max-w-xl text-sm md:text-base text-muted-foreground">
            Explore published roles with the details maintained by the hiring team.
          </p>
        </div>
        <Link
          href={publicLanding ? "/signup" : "/jobs"}
          className="inline-flex shrink-0 items-center gap-2 rounded-xl border border-white/20 px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-white transition-colors hover:bg-white/10"
        >
          {publicLanding ? "Create account to apply" : "View all jobs"}
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>

      {loading ? (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8 text-sm text-muted-foreground">
          Loading published opportunities…
        </div>
      ) : failed ? (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8 text-sm text-muted-foreground">
          Job listings are temporarily unavailable. Please try again shortly.
        </div>
      ) : jobs.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-white/15 bg-white/[0.03] p-8 text-sm text-muted-foreground">
          There are no published opportunities to show right now.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {jobs.map((job) => (
            <article key={job.id} className="flex h-full flex-col rounded-2xl border border-white/10 bg-white/[0.035] p-6 transition-all hover:border-white/25 hover:bg-white/[0.06]">
              <div className="flex items-start gap-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-black/30 text-white">
                  <BriefcaseBusiness className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-lg font-bold leading-snug text-white">{job.title}</h3>
                  <p className="mt-1 text-xs font-semibold text-muted-foreground">{job.department || "General"}</p>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2 text-[11px] font-semibold text-muted-foreground">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-black/20 px-3 py-1.5">
                  <MapPin className="h-3 w-3" /> {job.location || "Location flexible"}
                </span>
                <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1.5">
                  {job.employment_type || "Full-time"}
                </span>
                {job.salary_range && (
                  <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1.5">
                    {job.salary_range}
                  </span>
                )}
              </div>
              <p className="mt-4 line-clamp-3 whitespace-pre-line text-sm leading-relaxed text-muted-foreground">
                {job.description || "View this opportunity to learn more about the role."}
              </p>
              <div className="mt-auto pt-5">
                <Link
                  href={publicLanding ? "/signup" : `/jobs/${job.id}`}
                  className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-white hover:underline underline-offset-4"
                >
                  {publicLanding ? "Create account to apply" : "View requisition"}
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
