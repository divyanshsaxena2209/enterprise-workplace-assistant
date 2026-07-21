import { fetchWithAuth } from "./candidates";

export async function getApplications(page = 1, limit = 20, filters: any = {}) {
  const queryParams = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    ...filters
  });
  return fetchWithAuth(`/applications?${queryParams.toString()}`);
}

export async function getMyApplications(page = 1, limit = 20) {
  const queryParams = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    _t: Date.now().toString()
  });
  return fetchWithAuth(`/applications/my?${queryParams.toString()}`);
}

export async function getApplicationDetails(id: string) {
  return fetchWithAuth(`/applications/${id}`);
}

export async function createApplication(data: { job_id: string; candidate_id: string; resume_id: string }) {
  return fetchWithAuth("/applications/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
}

export async function rejectApplication(id: string, notes?: string) {
  return fetchWithAuth(`/applications/${id}/reject`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ notes }),
  });
}

export async function respondInterview(applicationId: string, interviewId: string, status: string, notes?: string) {
  return fetchWithAuth(`/applications/${applicationId}/interviews/${interviewId}/respond`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status, candidate_notes: notes }),
  });
}

export async function checkIsHired(): Promise<boolean> {
  try {
    const data = await getMyApplications(1, 100);
    if (!data || !data.items) return false;
    return data.items.some((app: any) => app.status === "Hired");
  } catch (err) {
    console.error("Failed to check hired status:", err);
    return false;
  }
}
