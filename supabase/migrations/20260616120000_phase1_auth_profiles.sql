-- =============================================================================
-- Phase 1: Auth & Profiles Infrastructure Migration
-- =============================================================================
-- Idempotent: safe to re-run.
-- Hardens the profiles table created in 20260616000000_core_overhaul.sql

-- ---------------------------------------------------------------------------
-- 1. Add missing columns if they don't exist
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    -- is_active column (required by RBAC logic)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name   = 'profiles'
          AND column_name  = 'is_active'
    ) THEN
        ALTER TABLE public.profiles
            ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;
    END IF;

    -- is_management_verified — ensure it has NOT NULL default
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name   = 'profiles'
          AND column_name  = 'is_management_verified'
    ) THEN
        ALTER TABLE public.profiles
            ADD COLUMN is_management_verified BOOLEAN NOT NULL DEFAULT false;
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 2. Apply NOT NULL constraints (safe — backfill defaults first)
-- ---------------------------------------------------------------------------

-- Ensure full_name has a sensible default before adding NOT NULL
UPDATE public.profiles
SET full_name = ''
WHERE full_name IS NULL;

ALTER TABLE public.profiles
    ALTER COLUMN full_name SET NOT NULL;

-- Ensure role has a sensible default before adding NOT NULL
UPDATE public.profiles
SET role = 'EMPLOYEE'
WHERE role IS NULL;

ALTER TABLE public.profiles
    ALTER COLUMN role SET NOT NULL;

-- ---------------------------------------------------------------------------
-- 3. Performance index on email (unique constraint already exists, but
--    an explicit index improves planner choices for partial scans)
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_profiles_email
    ON public.profiles (email);

CREATE INDEX IF NOT EXISTS idx_profiles_role
    ON public.profiles (role);

CREATE INDEX IF NOT EXISTS idx_profiles_is_active
    ON public.profiles (is_active);

-- ---------------------------------------------------------------------------
-- 4. updated_at auto-update trigger
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS profiles_set_updated_at ON public.profiles;

CREATE TRIGGER profiles_set_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
-- 5. RLS — add INSERT policy so the signup trigger can create rows
-- ---------------------------------------------------------------------------

-- Allow service role (backend) to insert profiles
DROP POLICY IF EXISTS "Allow service role to insert profiles" ON public.profiles;
CREATE POLICY "Allow service role to insert profiles"
    ON public.profiles FOR INSERT
    WITH CHECK (true);

-- Allow users to read their own profile (in addition to public read)
DROP POLICY IF EXISTS "Allow users to read their own profile" ON public.profiles;
CREATE POLICY "Allow users to read their own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

-- ---------------------------------------------------------------------------
-- 6. Update the handle_new_user trigger to include is_active
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (
        id,
        email,
        full_name,
        role,
        employee_id,
        department,
        job_title,
        phone,
        location,
        bio,
        avatar_url,
        is_management_verified,
        is_active
    )
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
        COALESCE(NEW.raw_user_meta_data->>'role', 'EMPLOYEE'),
        NEW.raw_user_meta_data->>'employee_id',
        NEW.raw_user_meta_data->>'department',
        NEW.raw_user_meta_data->>'job_title',
        NEW.raw_user_meta_data->>'phone',
        NEW.raw_user_meta_data->>'location',
        NEW.raw_user_meta_data->>'bio',
        NEW.raw_user_meta_data->>'avatar_url',
        COALESCE((NEW.raw_user_meta_data->>'is_management_verified')::boolean, false),
        true
    )
    ON CONFLICT (id) DO NOTHING;  -- Idempotent: skip if profile already exists
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Recreate trigger (DROP + CREATE is idempotent via OR REPLACE above)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();
