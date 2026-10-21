import os
from pathlib import Path

import psycopg


REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION = REPO_ROOT / "supabase" / "migrations" / "20261021000000_cognito_third_party_auth.sql"
PROFILE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
COGNITO_SUB = "11111111-1111-4111-8111-111111111111"
UNMAPPED_SUB = "22222222-2222-4222-8222-222222222222"
ISSUER = "https://cognito-idp.ap-south-1.amazonaws.com/ap-south-1_TestPool"


def test_cognito_migration_maps_rls_identity_without_breaking_supabase_auth():
    dsn = os.environ.get("COGNITO_TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("drop schema if exists public cascade")
        conn.execute("create schema public")
        conn.execute("grant usage on schema public to anon, authenticated, service_role")
        conn.execute("drop schema if exists auth cascade")
        conn.execute("create schema auth")
        conn.execute("create role anon nologin")
        conn.execute("create role authenticated nologin")
        conn.execute("create role service_role nologin bypassrls")
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
        conn.execute("create table public.profiles (id uuid primary key, role text not null)")
        conn.execute("create table public.test_owned (user_id uuid not null)")
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
        conn.execute("grant select on public.test_owned to authenticated")
        conn.execute("insert into public.profiles (id, role) values (%s, 'EMPLOYEE')", (PROFILE_ID,))
        conn.execute("insert into public.test_owned (user_id) values (%s), (%s)", (PROFILE_ID, COGNITO_SUB))

        migration = MIGRATION.read_text(encoding="utf-8")
        # psycopg executes the full migration as one script with prepare=False.
        conn.execute(migration, prepare=False)

        policy = conn.execute(
            "select qual, with_check from pg_policies where schemaname='public' and policyname='test_owned_rows'"
        ).fetchone()
        assert policy is not None
        assert "current_profile_id()" in (policy[0] or "")
        profile_policy = conn.execute(
            "select qual, with_check from pg_policies where schemaname='public' and policyname='profile_self_update'"
        ).fetchone()
        assert profile_policy is not None
        assert "current_profile_id()" in (profile_policy[0] or "")
        assert "current_profile_id()" in (profile_policy[1] or "")

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

        # An unlinked Cognito subject must resolve to NULL, not to its own sub.
        conn.execute(
            "select set_config('request.jwt.claims', %s, false)",
            ('{"iss":"' + ISSUER + '","sub":"' + UNMAPPED_SUB + '"}',),
        )
        assert conn.execute("select public.current_profile_id()").fetchone()[0] is None
        conn.execute("set role authenticated")
        assert conn.execute("select user_id from public.test_owned").fetchall() == []
        conn.execute("reset role")

        # Existing Supabase Auth subjects still fall back to auth.uid().
        conn.execute(
            "select set_config('request.jwt.claims', %s, false)",
            ('{"iss":"supabase","sub":"' + PROFILE_ID + '"}',),
        )
        assert str(conn.execute("select public.current_profile_id()").fetchone()[0]) == PROFILE_ID
