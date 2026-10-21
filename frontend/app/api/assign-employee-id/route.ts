import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const MANAGEMENT_ROLES = new Set(["MANAGEMENT", "ADMIN", "HR"]);
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const EMPLOYEE_ID_PATTERN = /^SS-\d{5}$/;

function apiBaseUrl() {
  const value = process.env.NEXT_PUBLIC_API_URL;
  if (!value) return null;
  const trimmed = value.replace(/\/+$/, "");
  return trimmed.includes("/api/v1") ? trimmed : `${trimmed}/api/v1`;
}

export async function POST(request: Request) {
  const authorization = request.headers.get("authorization");
  const tokenMatch = authorization?.match(/^Bearer\s+(\S+)$/i);
  if (!tokenMatch) {
    return NextResponse.json({ error: "Authentication required." }, { status: 401 });
  }

  const apiBase = apiBaseUrl();
  if (!apiBase) {
    return NextResponse.json({ error: "Backend authentication is not configured." }, { status: 503 });
  }

  // Ask FastAPI to validate the token and resolve the caller's trusted,
  // database-backed role. Never trust a role, user ID, or permissions from the
  // request body or client-side state.
  let caller: { role?: unknown; id?: unknown };
  try {
    const response = await fetch(`${apiBase}/auth/me`, {
      method: "GET",
      headers: { Authorization: `Bearer ${tokenMatch[1]}`, Accept: "application/json" },
      cache: "no-store",
    });
    if (response.status === 401 || response.status === 403 || response.status === 404) {
      return NextResponse.json({ error: "A valid active account is required." }, { status: 401 });
    }
    if (!response.ok) {
      return NextResponse.json({ error: "Unable to verify account permissions." }, { status: 502 });
    }
    caller = await response.json();
  } catch {
    return NextResponse.json({ error: "Unable to verify account permissions." }, { status: 502 });
  }

  if (typeof caller.role !== "string" || !MANAGEMENT_ROLES.has(caller.role.toUpperCase())) {
    return NextResponse.json({ error: "Management access is required." }, { status: 403 });
  }

  let body: { employeeId?: unknown; newEmployeeId?: unknown };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON request." }, { status: 400 });
  }

  const employeeId = typeof body.employeeId === "string" ? body.employeeId.trim() : "";
  const newEmployeeId = typeof body.newEmployeeId === "string" ? body.newEmployeeId.trim() : "";
  if (!UUID_PATTERN.test(employeeId) || !EMPLOYEE_ID_PATTERN.test(newEmployeeId)) {
    return NextResponse.json({ error: "A valid employee profile ID and employee ID are required." }, { status: 400 });
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!supabaseUrl || !serviceRoleKey) {
    return NextResponse.json({ error: "Server-side profile updates are not configured." }, { status: 503 });
  }

  try {
    const supabaseAdmin = createClient(supabaseUrl, serviceRoleKey, {
      auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
    });
    const { data, error } = await supabaseAdmin
      .from("profiles")
      .update({ employee_id: newEmployeeId })
      .eq("id", employeeId)
      .eq("role", "EMPLOYEE")
      .select("id")
      .maybeSingle();

    if (error) {
      if (error.code === "23505") {
        return NextResponse.json({ error: "That employee ID is already assigned." }, { status: 409 });
      }
      return NextResponse.json({ error: "Unable to assign the employee ID." }, { status: 500 });
    }
    if (!data) {
      return NextResponse.json({ error: "Employee profile not found." }, { status: 404 });
    }

    return NextResponse.json({ success: true });
  } catch {
    return NextResponse.json({ error: "Unable to assign the employee ID." }, { status: 500 });
  }
}
