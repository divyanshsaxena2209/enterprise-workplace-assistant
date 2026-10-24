
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

-- The initial schema's RLS policies query profiles.role. PostgreSQL will not
-- allow changing that column's enum type while those dependent policies exist.
-- Drop these legacy policies before the type change; later migrations rebuild
-- the current role-based policies after the core schema is recreated.
DROP POLICY IF EXISTS "Allow HR admins to manage jobs" ON public.jobs;
DROP POLICY IF EXISTS "Allow HR/Super admins to manage candidates" ON public.candidates;
DROP POLICY IF EXISTS "Allow HR/Super admins to manage onboarding steps" ON public.onboarding_steps;
DROP POLICY IF EXISTS "Allow HR/Super admins to view and manage all onboarding tasks" ON public.employee_onboarding_tasks;
DROP POLICY IF EXISTS "Allow HR/Super admins to manage company documents" ON public.company_documents;

ALTER TABLE public.profiles ALTER COLUMN role DROP DEFAULT;
ALTER TABLE public.profiles ALTER COLUMN role TYPE text USING role::text;
ALTER TABLE public.profiles ALTER COLUMN role SET DEFAULT 'Employee';


ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS employee_id text;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS department text;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS job_title text;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS phone text;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS location text;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS bio text;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS is_management_verified boolean DEFAULT false;


CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (
        id, email, full_name, role, employee_id, department, 
        job_title, phone, location, bio, avatar_url, is_management_verified
    )
    VALUES (
        new.id,
        new.email,
        COALESCE(new.raw_user_meta_data->>'full_name', ''),
        COALESCE(new.raw_user_meta_data->>'role', 'Employee'),
        new.raw_user_meta_data->>'employee_id',
        new.raw_user_meta_data->>'department',
        new.raw_user_meta_data->>'job_title',
        new.raw_user_meta_data->>'phone',
        new.raw_user_meta_data->>'location',
        new.raw_user_meta_data->>'bio',
        new.raw_user_meta_data->>'avatar_url',
        COALESCE((new.raw_user_meta_data->>'is_management_verified')::boolean, false)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
