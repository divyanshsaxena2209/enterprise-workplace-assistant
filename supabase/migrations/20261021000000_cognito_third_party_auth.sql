-- Cognito third-party identity support without replacing Supabase PostgreSQL.
-- Apply only to a staging Supabase project first. Existing Supabase Auth users
-- continue to work because current_profile_id() falls back to auth.uid().

create table if not exists public.cognito_identity_mappings (
    cognito_sub text primary key,
    profile_id uuid not null unique references public.profiles(id) on delete cascade,
    created_at timestamptz not null default now()
);

alter table public.cognito_identity_mappings enable row level security;
revoke all on public.cognito_identity_mappings from anon, authenticated;
grant select, insert on public.cognito_identity_mappings to service_role;

create or replace function public.current_profile_id()
returns uuid
language sql
stable
security definer
set search_path = public, auth, pg_temp
as $$
    select case
        when coalesce(auth.jwt() ->> 'iss', '') like 'https://cognito-idp.%.amazonaws.com/%' then
            (
                select m.profile_id
                from public.cognito_identity_mappings as m
                where m.cognito_sub = (auth.jwt() ->> 'sub')
                limit 1
            )
        else auth.uid()
    end;
$$;

revoke all on function public.current_profile_id() from public;
grant execute on function public.current_profile_id() to anon, authenticated, service_role;

-- Preserve the current policy definitions, roles, commands, and permissive mode,
-- but make every auth.uid() ownership check resolve to the linked Supabase
-- profile UUID for Cognito third-party JWTs. Unmapped Cognito subjects resolve
-- to no profile row and therefore gain no access to profile-owned resources.
do $$
declare
    policy_row record;
    roles_sql text;
    policy_sql text;
    using_sql text;
    check_sql text;
begin
    for policy_row in
        select *
        from pg_policies
        where schemaname = 'public'
          and (
              position('auth.uid()' in coalesce(qual, '')) > 0
              or position('auth.uid()' in coalesce(with_check, '')) > 0
          )
    loop
        execute format(
            'drop policy %I on %I.%I',
            policy_row.policyname,
            policy_row.schemaname,
            policy_row.tablename
        );

        select string_agg(
            case when role_name = 'public' then 'PUBLIC'
                 else format('%I', role_name)
            end,
            ', '
        )
        into roles_sql
        from unnest(policy_row.roles) as role_entries(role_name);

        policy_sql := format(
            'create policy %I on %I.%I as %s for %s to %s',
            policy_row.policyname,
            policy_row.schemaname,
            policy_row.tablename,
            policy_row.permissive,
            policy_row.cmd,
            coalesce(roles_sql, 'PUBLIC')
        );

        if policy_row.qual is not null then
            using_sql := replace(policy_row.qual, 'auth.uid()', 'public.current_profile_id()');
            policy_sql := policy_sql || format(' using (%s)', using_sql);
        end if;

        if policy_row.with_check is not null then
            check_sql := replace(policy_row.with_check, 'auth.uid()', 'public.current_profile_id()');
            policy_sql := policy_sql || format(' with check (%s)', check_sql);
        end if;

        execute policy_sql;
    end loop;
end;
$$;

create or replace function public.get_current_user_role()
returns text
language sql
security definer
set search_path = public, auth, pg_temp
as $$
    select role::text
    from public.profiles
    where id = public.current_profile_id();
$$;

create or replace function public.log_onboarding_history()
returns trigger
language plpgsql
security definer
set search_path = public, auth, pg_temp
as $$
begin
    if (TG_OP = 'UPDATE' and OLD.status is distinct from NEW.status) then
        insert into public.onboarding_history
            (progress_id, previous_status, new_status, updated_by)
        values
            (NEW.id, OLD.status::text, NEW.status::text, public.current_profile_id());
    elsif (TG_OP = 'INSERT') then
        insert into public.onboarding_history
            (progress_id, previous_status, new_status, updated_by)
        values
            (NEW.id, null, NEW.status::text, public.current_profile_id());
    end if;
    return NEW;
end;
$$;
