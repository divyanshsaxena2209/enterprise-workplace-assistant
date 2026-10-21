-- Additive staging migration for Cognito identities.
-- This keeps the existing Supabase database and profiles table in place.
-- The table must only be accessed by trusted server-side service-role code.

create table if not exists public.cognito_identity_mappings (
    cognito_sub text primary key,
    profile_id uuid not null unique references public.profiles(id) on delete cascade,
    created_at timestamptz not null default now()
);

alter table public.cognito_identity_mappings enable row level security;
revoke all on public.cognito_identity_mappings from anon, authenticated;
grant select, insert on public.cognito_identity_mappings to service_role;
