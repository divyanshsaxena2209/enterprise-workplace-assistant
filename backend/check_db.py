import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL", "https://ybkfkdcdhrnjmjvavyhb.supabase.co")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlia2ZrZGNkaHJuam1qdmF2eWhiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTYxNzQxNSwiZXhwIjoyMDk1MTkzNDE1fQ.5QmofOjsfZ3O3V_8NaB_nNPrMXpElIPXZt9TKUTjf5g")

supabase = create_client(url, key)

print("Fetching auth.users...")
users = supabase.auth.admin.list_users()
for u in users:
    print(f"User: {u.id} - {u.email}")

print("\nFetching public.profiles...")
profiles = supabase.table("profiles").select("*").execute()
for p in profiles.data:
    print(f"Profile: {p['id']} - {p['email']}")
