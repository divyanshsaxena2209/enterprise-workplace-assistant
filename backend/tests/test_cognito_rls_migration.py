import os
from pathlib import Path

import psycopg


REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION = REPO_ROOT / "supabase" / "migrations" / "20261021000000_cognito_third_party_auth.sql"
SECURITY_HARDENING_MIGRATION = REPO_ROOT / "supabase" / "migrations" / "20261022000000_harden_trigger_functions.sql"
ROLE_SCOPED_POLICY_MIGRATION = REPO_ROOT / "supabase" / "migrations" / "20261022000001_restrict_role_scoped_rls_policies.sql"
PROFILE_SERVICE_ROLE_GRANTS_MIGRATION = REPO_ROOT / "supabase" / "migrations" / "20261024000000_grant_service_role_profile_privileges.sql"
JOBS_SERVICE_ROLE_GRANTS_MIGRATION = REPO_ROOT / "supabase" / "migrations" / "20261024010000_grant_service_role_jobs_select.sql"
EMPLOYEE_ID_MIGRATION = REPO_ROOT / "supabase" / "migrations" / "20261024020000_auto_assign_employee_ids.sql"
PUBLIC_SIGNUP_ROLE_MIGRATION = REPO_ROOT / "supabase" / "migrations" / "20261024030000_harden_public_signup_roles.sql"
BACKEND_TABLE_GRANTS_MIGRATION = REPO_ROOT / "supabase" / "migrations" / "20261024040000_grant_backend_service_role_table_privileges.sql"
KNOWLEDGE_DOCUMENTS_MIGRATION = REPO_ROOT / "supabase" / "migrations" / "20261024050000_knowledge_document_registry.sql"
KNOWLEDGE_DOCUMENTS_INDEX_MIGRATION = REPO_ROOT / "supabase" / "migrations" / "20261024060000_knowledge_document_registry_fk_index.sql"
KNOWLEDGE_DOCUMENTS_SCOPE_MIGRATION = REPO_ROOT / "supabase" / "migrations" / "20261024070000_knowledge_document_department_scope.sql"
KNOWLEDGE_DOCUMENTS_SCOPE_DEFAULT_MIGRATION = REPO_ROOT / "supabase" / "migrations" / "20261024080000_knowledge_document_scope_fail_closed_default.sql"
PROFILE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
COGNITO_SUB = "11111111-1111-4111-8111-111111111111"
UNMAPPED_SUB = "22222222-2222-4222-8222-222222222222"
ISSUER = "https://cognito-idp.ap-south-1.amazonaws.com/ap-south-1_TestPool"


def test_cognito_migration_maps_rls_identity_without_breaking_supabase_auth():
    dsn = os.environ.get("COGNITO_TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("drop schema if exists public cascade")
        conn.execute("create schema public")
        conn.execute("drop schema if exists auth cascade")
        conn.execute("create schema auth")
        conn.execute("create schema storage")
        conn.execute("create table auth.users (id uuid primary key, email text not null, raw_user_meta_data jsonb, raw_app_meta_data jsonb)")
        conn.execute("create role anon nologin")
        conn.execute("create role authenticated nologin")
        conn.execute("create role service_role nologin bypassrls")
        conn.execute("grant usage on schema public, storage to anon, authenticated, service_role")
        conn.execute(
            """
            create function auth.jwt() returns jsonb
            language sql stable
            as $$ select nullif(current_setting('request.jwt.claims', true), '')::jsonb $$;
            """
        )
        conn.execute(
            """
            create function auth.uid() returns uuid
            language sql stable
            as $$ select nullif(auth.jwt() ->> 'sub', '')::uuid $$;
            """
        )
        conn.execute("create table public.profiles (id uuid primary key, email text, full_name text, role text not null, employee_id text, department text, job_title text, phone text, location text, bio text, avatar_url text, is_management_verified boolean default false, is_active boolean default true, created_at timestamptz default now(), updated_at timestamptz default now())")
        # Stand-ins for tables whose baseline migrations include legacy broad
        # service-role policies. These let this single isolated test validate
        # the full role-scoped policy hardening migration.
        for table_name in (
            "application_status_history",
            "applications",
            "candidate_scores",
            "candidates",
            "resumes",
            "jobs",
            "recruiter_notes",
        ):
            conn.execute(f"create table public.{table_name} (id uuid primary key)")
            conn.execute(f"alter table public.{table_name} enable row level security")
        conn.execute("create table public.interviews (id uuid primary key)")
        conn.execute("alter table public.interviews enable row level security")
        conn.execute(
            'create policy "Allow public read access to profiles" on public.profiles for select using (true)'
        )
        conn.execute(
            'create policy "Allow service role to insert profiles" on public.profiles for insert with check (true)'
        )
        for table_name, policy_name in (
            ("application_status_history", "Allow service role full access to status history"),
            ("applications", "Allow service role full access to applications"),
            ("candidate_scores", "Allow service role full access to scores"),
            ("candidates", "Allow service role full access to candidates"),
            ("resumes", "Allow service role full access to resumes"),
            ("jobs", "Allow service role full access to jobs"),
            ("recruiter_notes", "Allow service role full access to recruiter notes"),
        ):
            conn.execute(
                f'create policy "{policy_name}" on public.{table_name} for all using (true)'
            )
        conn.execute(
            'create policy "Allow full access to interviews" on public.interviews for all using (true)'
        )
        conn.execute("grant all on public.interviews to authenticated, service_role")
        # Model existing trigger functions from the baseline Supabase schema.
        # The Cognito migration redefines log_onboarding_history; the hardening
        # migration should secure all three trigger-only functions.
        conn.execute(
            """
            create function public.handle_new_user() returns trigger
            language plpgsql security definer
            as $fn$ begin return new; end $fn$
            """
        )
        conn.execute(
            """
            create function public.set_updated_at() returns trigger
            language plpgsql
            as $fn$ begin return new; end $fn$
            """
        )
        conn.execute("create table public.test_owned (user_id uuid not null)")
        conn.execute("create table storage.objects (owner_id uuid not null)")
        conn.execute("alter table storage.objects enable row level security")
        conn.execute("alter table public.profiles enable row level security")
        conn.execute("alter table public.test_owned enable row level security")
        conn.execute(
            """
            create policy profile_self_update on public.profiles
            for update to authenticated using (auth.uid() = id) with check (auth.uid() = id)
            """
        )
        conn.execute(
            """
            create policy test_owned_rows on public.test_owned
            for select to authenticated using (auth.uid() = user_id)
            """
        )
        conn.execute(
            """
            create policy storage_owner_rows on storage.objects
            for select to authenticated using (auth.uid() = owner_id)
            """
        )
        conn.execute("grant select on public.test_owned, storage.objects to authenticated")
        conn.execute("insert into public.profiles (id, role) values (%s, 'EMPLOYEE')", (PROFILE_ID,))
        conn.execute("insert into public.test_owned (user_id) values (%s), (%s)", (PROFILE_ID, COGNITO_SUB))
        conn.execute("insert into storage.objects (owner_id) values (%s), (%s)", (PROFILE_ID, COGNITO_SUB))

        migration = MIGRATION.read_text(encoding="utf-8")
        # psycopg executes the full migration as one script with prepare=False.
        conn.execute(migration, prepare=False)
        security_hardening = SECURITY_HARDENING_MIGRATION.read_text(encoding="utf-8")
        conn.execute(security_hardening, prepare=False)
        role_scoped_policies = ROLE_SCOPED_POLICY_MIGRATION.read_text(encoding="utf-8")
        conn.execute(role_scoped_policies, prepare=False)
        profile_service_role_grants = PROFILE_SERVICE_ROLE_GRANTS_MIGRATION.read_text(encoding="utf-8")
        conn.execute(profile_service_role_grants, prepare=False)
        jobs_service_role_grants = JOBS_SERVICE_ROLE_GRANTS_MIGRATION.read_text(encoding="utf-8")
        conn.execute(jobs_service_role_grants, prepare=False)
        employee_id_migration = EMPLOYEE_ID_MIGRATION.read_text(encoding="utf-8")
        conn.execute(employee_id_migration, prepare=False)
        public_signup_role_migration = PUBLIC_SIGNUP_ROLE_MIGRATION.read_text(encoding="utf-8")
        conn.execute(public_signup_role_migration, prepare=False)
        backend_table_grants_migration = BACKEND_TABLE_GRANTS_MIGRATION.read_text(encoding="utf-8")
        conn.execute(backend_table_grants_migration, prepare=False)
        knowledge_documents_migration = KNOWLEDGE_DOCUMENTS_MIGRATION.read_text(encoding="utf-8")
        conn.execute(knowledge_documents_migration, prepare=False)
        knowledge_documents_index_migration = KNOWLEDGE_DOCUMENTS_INDEX_MIGRATION.read_text(encoding="utf-8")
        conn.execute(knowledge_documents_index_migration, prepare=False)
        knowledge_documents_scope_migration = KNOWLEDGE_DOCUMENTS_SCOPE_MIGRATION.read_text(encoding="utf-8")
        conn.execute(knowledge_documents_scope_migration, prepare=False)
        scope_column = conn.execute(
            """
            select column_default, is_nullable
            from information_schema.columns
            where table_schema='public' and table_name='knowledge_documents'
              and column_name='department_scope'
            """
        ).fetchone()
        assert scope_column is not None
        assert "ALL" in (scope_column[0] or "")
        assert scope_column[1] == "NO"
        assert conn.execute("select to_regclass('public.knowledge_documents_department_scope_idx')").fetchone()[0]
        scope_default_migration = KNOWLEDGE_DOCUMENTS_SCOPE_DEFAULT_MIGRATION.read_text(encoding="utf-8")
        conn.execute(scope_default_migration, prepare=False)
        scope_column = conn.execute(
            """
            select column_default
            from information_schema.columns
            where table_schema='public' and table_name='knowledge_documents'
              and column_name='department_scope'
            """
        ).fetchone()
        assert scope_column is not None
        assert "REVIEW_REQUIRED" in (scope_column[0] or "")

        policy = conn.execute(
            "select qual, with_check from pg_policies where schemaname='public' and policyname='test_owned_rows'"
        ).fetchone()
        assert policy is not None
        assert "current_profile_id()" in (policy[0] or "")
        storage_policy = conn.execute(
            "select qual from pg_policies where schemaname='storage' and policyname='storage_owner_rows'"
        ).fetchone()
        assert storage_policy is not None
        assert "current_profile_id()" in (storage_policy[0] or "")
        profile_policy = conn.execute(
            "select qual, with_check from pg_policies where schemaname='public' and policyname='profile_self_update'"
        ).fetchone()
        assert profile_policy is not None
        assert "current_profile_id()" in (profile_policy[0] or "")
        assert "current_profile_id()" in (profile_policy[1] or "")

        # The identity mapping table is backend-only: client roles must not
        # read or write it directly, even though the backend service role can.
        mapping_table_rls = conn.execute(
            """
            select relrowsecurity
            from pg_class
            where oid = 'public.cognito_identity_mappings'::regclass
            """
        ).fetchone()
        assert mapping_table_rls == (True,)
        mapping_privileges = conn.execute(
            """
            select
                has_table_privilege('anon', 'public.cognito_identity_mappings', 'SELECT'),
                has_table_privilege('authenticated', 'public.cognito_identity_mappings', 'SELECT'),
                has_table_privilege('anon', 'public.cognito_identity_mappings', 'INSERT'),
                has_table_privilege('authenticated', 'public.cognito_identity_mappings', 'INSERT'),
                has_table_privilege('service_role', 'public.cognito_identity_mappings', 'SELECT'),
                has_table_privilege('service_role', 'public.cognito_identity_mappings', 'INSERT')
            """
        ).fetchone()
        assert mapping_privileges == (False, False, False, False, True, True)

        knowledge_document_security = conn.execute(
            """
            select
              c.relrowsecurity,
              has_table_privilege('service_role', 'public.knowledge_documents', 'SELECT'),
              has_table_privilege('service_role', 'public.knowledge_documents', 'INSERT'),
              has_table_privilege('service_role', 'public.knowledge_documents', 'UPDATE'),
              has_table_privilege('service_role', 'public.knowledge_documents', 'DELETE'),
              has_table_privilege('anon', 'public.knowledge_documents', 'SELECT'),
              has_table_privilege('anon', 'public.knowledge_documents', 'INSERT'),
              has_table_privilege('anon', 'public.knowledge_documents', 'UPDATE'),
              has_table_privilege('anon', 'public.knowledge_documents', 'DELETE'),
              has_table_privilege('authenticated', 'public.knowledge_documents', 'SELECT'),
              has_table_privilege('authenticated', 'public.knowledge_documents', 'INSERT'),
              has_table_privilege('authenticated', 'public.knowledge_documents', 'UPDATE'),
              has_table_privilege('authenticated', 'public.knowledge_documents', 'DELETE')
            from pg_class c
            where c.oid = 'public.knowledge_documents'::regclass
            """
        ).fetchone()
        assert knowledge_document_security == (
            True, True, True, True, True,
            False, False, False, False, False, False, False, False,
        )
        registry_uploader_index = conn.execute(
            "select to_regclass('public.knowledge_documents_uploaded_by_idx')"
        ).fetchone()
        assert registry_uploader_index == ("knowledge_documents_uploaded_by_idx",)

        # Policy rewriting must cover both application tables and Storage.
        remaining_uid_policies = conn.execute(
            """
            select count(*)
            from pg_policies
            where schemaname in ('public', 'storage')
              and (
                coalesce(qual, '') like '%auth.uid()%'
                or coalesce(with_check, '') like '%auth.uid()%'
              )
            """
        ).fetchone()[0]
        assert remaining_uid_policies == 0
        rewritten_policy_count = conn.execute(
            """
            select count(*)
            from pg_policies
            where schemaname in ('public', 'storage')
              and (
                coalesce(qual, '') like '%current_profile_id()%'
                or coalesce(with_check, '') like '%current_profile_id()%'
              )
            """
        ).fetchone()[0]
        assert rewritten_policy_count >= 3

        current_profile_function = conn.execute(
            """
            select prosecdef, proconfig
            from pg_proc
            where oid = 'public.current_profile_id()'::regprocedure
            """
        ).fetchone()
        assert current_profile_function is not None
        assert current_profile_function[0] is True
        assert "search_path=public, auth, pg_temp" in (current_profile_function[1] or [])

        # Trigger-only functions must use a fixed search_path and not be
        # executable as browser-callable PostgREST RPCs.
        for function_name in ("handle_new_user", "set_updated_at", "log_onboarding_history", "assign_employee_id"):
            function_config = conn.execute(
                "select proconfig from pg_proc where oid = %s::regprocedure",
                (f"public.{function_name}()",),
            ).fetchone()
            assert function_config is not None
            assert "search_path=pg_catalog, public, auth, pg_temp" in (function_config[0] or [])
            client_execute_privileges = conn.execute(
                """
                select
                  has_function_privilege('anon', %s, 'EXECUTE'),
                  has_function_privilege('authenticated', %s, 'EXECUTE')
                """,
                (f"public.{function_name}()", f"public.{function_name}()"),
            ).fetchone()
            assert client_execute_privileges == (False, False)

        # Security-sensitive RLS policies are narrowed to service_role;
        # management-sensitive interview rows cannot be read or modified by
        # an ordinary authenticated user via Supabase's Data API.
        for table_name, policy_name in (
            ("application_status_history", "Allow service role full access to status history"),
            ("applications", "Allow service role full access to applications"),
            ("candidate_scores", "Allow service role full access to scores"),
            ("candidates", "Allow service role full access to candidates"),
            ("resumes", "Allow service role full access to resumes"),
            ("jobs", "Allow service role full access to jobs"),
            ("recruiter_notes", "Allow service role full access to recruiter notes"),
            ("interviews", "Allow service role full access to interviews"),
        ):
            policy_roles = conn.execute(
                "select roles from pg_policies where schemaname='public' and tablename=%s and policyname=%s",
                (table_name, policy_name),
            ).fetchone()
            assert policy_roles is not None
            assert policy_roles[0] == ["service_role"]
        assert conn.execute(
            "select count(*) from pg_policies where schemaname='public' and tablename='profiles' and policyname='Allow public read access to profiles'"
        ).fetchone()[0] == 0
        assert conn.execute(
            "select count(*) from pg_policies where schemaname='public' and tablename='profiles' and policyname='Allow service role to insert profiles'"
        ).fetchone()[0] == 1
        profile_insert_roles = conn.execute(
            "select roles from pg_policies where schemaname='public' and tablename='profiles' and policyname='Allow service role to insert profiles'"
        ).fetchone()
        assert profile_insert_roles == (["service_role"],)
        # Policies do not grant SQL privileges. The trusted backend role must
        # have exactly the profile operations used by the link/provision route,
        # while browser roles must not gain profile access from this migration.
        assert conn.execute(
            """
            select
              has_table_privilege('service_role', 'public.profiles', 'SELECT'),
              has_table_privilege('service_role', 'public.profiles', 'INSERT'),
              has_table_privilege('service_role', 'public.profiles', 'UPDATE'),
              has_table_privilege('service_role', 'public.profiles', 'DELETE'),
              has_table_privilege('anon', 'public.profiles', 'SELECT'),
              has_table_privilege('authenticated', 'public.profiles', 'SELECT')
            """
        ).fetchone() == (True, True, True, False, False, False)
        assert conn.execute(
            "select has_table_privilege('authenticated', 'public.interviews', 'SELECT'), has_table_privilege('authenticated', 'public.interviews', 'INSERT'), has_table_privilege('authenticated', 'public.interviews', 'UPDATE'), has_table_privilege('authenticated', 'public.interviews', 'DELETE')"
        ).fetchone() == (False, False, False, False)
        assert conn.execute(
            "select has_table_privilege('service_role', 'public.interviews', 'SELECT'), has_table_privilege('service_role', 'public.interviews', 'INSERT'), has_table_privilege('service_role', 'public.interviews', 'UPDATE'), has_table_privilege('service_role', 'public.interviews', 'DELETE')"
        ).fetchone() == (True, True, True, True)
        assert conn.execute(
            """
            select
              has_table_privilege('service_role', 'public.jobs', 'SELECT'),
              has_table_privilege('service_role', 'public.jobs', 'INSERT'),
              has_table_privilege('service_role', 'public.jobs', 'UPDATE'),
              has_table_privilege('service_role', 'public.jobs', 'DELETE'),
              has_table_privilege('anon', 'public.jobs', 'SELECT'),
              has_table_privilege('authenticated', 'public.jobs', 'SELECT')
            """
        ).fetchone() == (True, True, True, False, False, False)
        expected_privileges = {
            "applications": (True, True, True, False),
            "candidates": (True, True, True, False),
            "resumes": (True, True, False, False),
            "candidate_scores": (True, True, True, False),
            "application_status_history": (True, True, False, False),
            "recruiter_notes": (True, True, True, True),
        }
        for table_name, expected in expected_privileges.items():
            assert conn.execute(
                """
                select
                  has_table_privilege('service_role', %s, 'SELECT'),
                  has_table_privilege('service_role', %s, 'INSERT'),
                  has_table_privilege('service_role', %s, 'UPDATE'),
                  has_table_privilege('service_role', %s, 'DELETE')
                """,
                (f"public.{table_name}",) * 4,
            ).fetchone() == expected
            assert conn.execute(
                "select has_table_privilege('anon', %s, 'SELECT'), has_table_privilege('authenticated', %s, 'SELECT')",
                (f"public.{table_name}", f"public.{table_name}"),
            ).fetchone() == (False, False)

        # Existing profiles with no ID are backfilled, while subsequent signups
        # receive deterministic-format IDs and explicit administrative IDs survive.
        assert conn.execute(
            "select employee_id from public.profiles where id = %s",
            (PROFILE_ID,),
        ).fetchone() == ("EMP-000001",)
        new_employee_id = conn.execute(
            "insert into public.profiles (id, role) values (%s, 'EMPLOYEE') returning employee_id",
            ("33333333-3333-4333-8333-333333333333",),
        ).fetchone()[0]
        assert new_employee_id == "EMP-000002"
        new_manager_id = conn.execute(
            "insert into public.profiles (id, role) values (%s, 'MANAGEMENT') returning employee_id",
            ("44444444-4444-4444-8444-444444444444",),
        ).fetchone()[0]
        assert new_manager_id == "MGR-000003"
        explicit_id = conn.execute(
            "insert into public.profiles (id, role, employee_id) values (%s, 'EMPLOYEE', 'EXT-7788') returning employee_id",
            ("55555555-5555-4555-8555-555555555555",),
        ).fetchone()[0]
        assert explicit_id == "EXT-7788"

        # Direct Supabase signup metadata is user-controlled: it cannot grant
        # MANAGEMENT or select a custom employee ID. Trusted app metadata can.
        conn.execute(
            "create trigger on_auth_user_created after insert on auth.users for each row execute function public.handle_new_user()"
        )
        conn.execute(
            """
            insert into auth.users (id, email, raw_user_meta_data, raw_app_meta_data)
            values (%s, %s, %s::jsonb, %s::jsonb)
            """,
            (
                "66666666-6666-4666-8666-666666666666",
                "public-signup@example.test",
                '{"full_name":"Public Signup","role":"MANAGEMENT","employee_id":"SPOOF-1","is_management_verified":true}',
                '{}',
            ),
        )
        public_signup = conn.execute(
            "select role, employee_id, is_management_verified from public.profiles where id = %s",
            ("66666666-6666-4666-8666-666666666666",),
        ).fetchone()
        assert public_signup[0] == "EMPLOYEE"
        assert public_signup[1].startswith("EMP-")
        assert public_signup[1] != "SPOOF-1"
        assert public_signup[2] is False

        conn.execute(
            """
            insert into auth.users (id, email, raw_user_meta_data, raw_app_meta_data)
            values (%s, %s, %s::jsonb, %s::jsonb)
            """,
            (
                "77777777-7777-4777-8777-777777777777",
                "admin-provisioned@example.test",
                '{"full_name":"Admin Provisioned","role":"EMPLOYEE","employee_id":"SPOOF-2"}',
                '{"role":"MANAGEMENT","is_management_verified":true}',
            ),
        )
        trusted_signup = conn.execute(
            "select role, employee_id, is_management_verified from public.profiles where id = %s",
            ("77777777-7777-4777-8777-777777777777",),
        ).fetchone()
        assert trusted_signup[0] == "MANAGEMENT"
        assert trusted_signup[1].startswith("MGR-")
        assert trusted_signup[1] != "SPOOF-2"
        assert trusted_signup[2] is True

        conn.execute(
            "insert into public.cognito_identity_mappings (cognito_sub, profile_id) values (%s, %s)",
            (COGNITO_SUB, PROFILE_ID),
        )
        conn.execute(
            "select set_config('request.jwt.claims', %s, false)",
            ('{"iss":"' + ISSUER + '","sub":"' + COGNITO_SUB + '"}',),
        )
        mapped_id = conn.execute("select public.current_profile_id()").fetchone()[0]
        assert str(mapped_id) == PROFILE_ID

        conn.execute("set role authenticated")
        mapped_rows = conn.execute("select user_id from public.test_owned").fetchall()
        assert [str(row[0]) for row in mapped_rows] == [PROFILE_ID]
        conn.execute("reset role")
        conn.execute("set role authenticated")
        storage_rows = conn.execute("select owner_id from storage.objects").fetchall()
        assert [str(row[0]) for row in storage_rows] == [PROFILE_ID]
        conn.execute("reset role")

        # An unlinked Cognito subject must resolve to NULL, not to its own sub.
        conn.execute(
            "select set_config('request.jwt.claims', %s, false)",
            ('{"iss":"' + ISSUER + '","sub":"' + UNMAPPED_SUB + '"}',),
        )
        assert conn.execute("select public.current_profile_id()").fetchone()[0] is None
        conn.execute("set role authenticated")
        assert conn.execute("select user_id from public.test_owned").fetchall() == []
        assert conn.execute("select owner_id from storage.objects").fetchall() == []
        conn.execute("reset role")

        # Existing Supabase Auth subjects still fall back to auth.uid().
        conn.execute(
            "select set_config('request.jwt.claims', %s, false)",
            ('{"iss":"supabase","sub":"' + PROFILE_ID + '"}',),
        )
        assert str(conn.execute("select public.current_profile_id()").fetchone()[0]) == PROFILE_ID
