-- 1. Alter profiles table to add new fields and modify role column
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

-- Drop default constraint on role if exists, then change type to text
ALTER TABLE public.profiles ALTER COLUMN role DROP DEFAULT;
ALTER TABLE public.profiles ALTER COLUMN role TYPE text USING role::text;
ALTER TABLE public.profiles ALTER COLUMN role SET DEFAULT 'Employee';

-- Add new columns to profiles
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS employee_id text;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS department text;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS job_title text;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS phone text;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS location text;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS bio text;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS is_management_verified boolean DEFAULT false;

-- 2. Update trigger function to handle new metadata fields on user signup
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

-- Re-enable the trigger
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
