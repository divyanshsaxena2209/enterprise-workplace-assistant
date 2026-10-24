"use client";

import { useCallback, useEffect, useState } from "react";
import { Check, Clock3, Loader2, ShieldCheck, X } from "lucide-react";
import { fetchWithAuth } from "@/lib/api/candidates";
import { useUser } from "@/lib/context/UserContext";

type OwnRequest = {
  status: "PENDING" | "APPROVED" | "REJECTED";
  requested_role: "MANAGEMENT";
  requested_at?: string;
  reviewed_at?: string | null;
  reviewer_note?: string | null;
};

type PendingRequest = {
  profile_id: string;
  status: "PENDING";
  requested_role: "MANAGEMENT";
  requested_at?: string;
  request_note?: string | null;
  requester: {
    full_name: string;
    email: string;
    employee_id?: string | null;
    department?: string | null;
    job_title?: string | null;
    current_role: string;
  };
};

export default function SettingsPage() {
  const { profile, refreshProfile } = useUser();
  const [ownRequest, setOwnRequest] = useState<OwnRequest | null>(null);
  const [pendingRequests, setPendingRequests] = useState<PendingRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [reviewingId, setReviewingId] = useState<string | null>(null);
  const [requestSubmitting, setRequestSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loadRequests = useCallback(async () => {
    if (!profile || profile.role === "GUEST") {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const own = await fetchWithAuth("/profile/management-access-request");
      setOwnRequest(own.request || null);
      if (profile.role === "MANAGEMENT") {
        const pending = await fetchWithAuth("/profile/management-access-requests/pending");
        setPendingRequests(Array.isArray(pending.requests) ? pending.requests : []);
      } else {
        setPendingRequests([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load access requests.");
    } finally {
      setLoading(false);
    }
  }, [profile?.id, profile?.role]);

  useEffect(() => {
    void loadRequests();
  }, [loadRequests]);

  async function submitManagementRequest() {
    setRequestSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const result = await fetchWithAuth("/profile/management-access-request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      setOwnRequest(result.request || null);
      setNotice(result.message || "Management access request submitted for review.");
      await refreshProfile();
      await loadRequests();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to submit the access request.");
    } finally {
      setRequestSubmitting(false);
    }
  }

  async function reviewRequest(profileId: string, decision: "APPROVE" | "REJECT") {
    setReviewingId(profileId);
    setError(null);
    setNotice(null);
    try {
      const result = await fetchWithAuth(
        `/profile/management-access-requests/${encodeURIComponent(profileId)}/review`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ decision }),
        },
      );
      setPendingRequests((current) => current.filter((item) => item.profile_id !== profileId));
      setNotice(result.message || (decision === "APPROVE" ? "Management access approved." : "Request rejected."));
      await loadRequests();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to review this request.");
    } finally {
      setReviewingId(null);
    }
  }

  return (
    <div className="space-y-6 pb-10">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage workspace access requests and enterprise security settings.
        </p>
      </div>

      {error && (
        <div role="alert" className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {error}
        </div>
      )}
      {notice && (
        <div role="status" className="rounded-lg border border-border bg-secondary/30 p-4 text-sm text-foreground">
          {notice}
        </div>
      )}

      {profile && profile.role !== "GUEST" && (
        <section className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-start gap-3">
            <ShieldCheck className="mt-0.5 h-5 w-5 text-muted-foreground" />
            <div className="min-w-0 flex-1">
              <h2 className="text-base font-semibold text-foreground">Your access level</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Current application role: <span className="font-semibold text-foreground">{profile.role}</span>
              </p>
              {loading ? (
                <p className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" /> Checking access request…
                </p>
              ) : ownRequest ? (
                <div className="mt-4 rounded-lg border border-border bg-secondary/20 p-4">
                  <p className="flex items-center gap-2 text-sm font-semibold text-foreground">
                    {ownRequest.status === "PENDING" ? <Clock3 className="h-4 w-4" /> : ownRequest.status === "APPROVED" ? <Check className="h-4 w-4" /> : <X className="h-4 w-4" />}
                    Management request: {ownRequest.status}
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {ownRequest.status === "PENDING"
                      ? "Your account keeps Employee permissions until an existing Management user approves the request."
                      : ownRequest.status === "APPROVED"
                        ? "Your Management permissions have been approved and are now controlled by your database profile."
                        : "Your request was rejected. You can submit a new request if your responsibilities have changed."}
                  </p>
                  {ownRequest.reviewer_note && (
                    <p className="mt-2 text-sm text-muted-foreground">Reviewer note: {ownRequest.reviewer_note}</p>
                  )}
                  {profile.role === "EMPLOYEE" && ownRequest.status === "REJECTED" && (
                    <button
                      type="button"
                      disabled={requestSubmitting}
                      onClick={() => void submitManagementRequest()}
                      className="mt-3 inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-semibold text-foreground hover:bg-secondary disabled:opacity-50"
                    >
                      {requestSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                      Submit a new request
                    </button>
                  )}
                </div>
              ) : profile.role === "EMPLOYEE" ? (
                <div className="mt-3 space-y-3">
                  <p className="text-sm text-muted-foreground">
                    No Management access request is recorded for this account.
                  </p>
                  <button
                    type="button"
                    disabled={requestSubmitting}
                    onClick={() => void submitManagementRequest()}
                    className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-semibold text-foreground hover:bg-secondary disabled:opacity-50"
                  >
                    {requestSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                    Request Management access
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </section>
      )}

      {profile?.role === "MANAGEMENT" && (
        <section className="space-y-4 rounded-xl border border-border bg-card p-5">
          <div>
            <h2 className="text-base font-semibold text-foreground">Management access requests</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Approving a request changes the user’s database-backed application role. Cognito attributes and signup form values never grant Management access by themselves.
            </p>
          </div>

          {loading ? (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading pending requests…
            </p>
          ) : pendingRequests.length === 0 ? (
            <p className="rounded-lg border border-border bg-secondary/20 p-4 text-sm text-muted-foreground">
              There are no pending Management access requests.
            </p>
          ) : (
            <div className="space-y-3">
              {pendingRequests.map((item) => (
                <article key={item.profile_id} className="rounded-lg border border-border p-4">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0 space-y-1">
                      <h3 className="font-semibold text-foreground">{item.requester.full_name}</h3>
                      <p className="text-sm text-muted-foreground">{item.requester.email}</p>
                      <p className="text-sm text-muted-foreground">
                        {[item.requester.job_title, item.requester.department, item.requester.employee_id].filter(Boolean).join(" · ") || "No additional employee details"}
                      </p>
                      {item.request_note && <p className="pt-1 text-sm text-muted-foreground">Request note: {item.request_note}</p>}
                      <p className="pt-1 text-xs text-muted-foreground">
                        Requested {item.requested_at ? new Date(item.requested_at).toLocaleString() : "date unavailable"}
                      </p>
                    </div>
                    <div className="flex shrink-0 gap-2">
                      <button
                        type="button"
                        disabled={reviewingId !== null}
                        onClick={() => void reviewRequest(item.profile_id, "REJECT")}
                        className="rounded-lg border border-border px-3 py-2 text-sm font-semibold text-foreground hover:bg-secondary disabled:opacity-50"
                      >
                        {reviewingId === item.profile_id ? <Loader2 className="h-4 w-4 animate-spin" /> : "Reject"}
                      </button>
                      <button
                        type="button"
                        disabled={reviewingId !== null}
                        onClick={() => void reviewRequest(item.profile_id, "APPROVE")}
                        className="rounded-lg bg-foreground px-3 py-2 text-sm font-semibold text-background hover:opacity-90 disabled:opacity-50"
                      >
                        {reviewingId === item.profile_id ? <Loader2 className="h-4 w-4 animate-spin" /> : "Approve"}
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
