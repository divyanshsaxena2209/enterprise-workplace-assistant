"""Manual staging connectivity check; never embed service-role credentials here."""

import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
if not url or not key:
    raise SystemExit(
        "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in your environment; "
        "never hard-code Supabase service-role credentials in source."
    )

supabase = create_client(url, key)
response = supabase.table("profiles").select("id").limit(1).execute()
print(
    "Supabase connection and profiles read succeeded; "
    f"sample rows returned: {len(response.data or [])}."
)
