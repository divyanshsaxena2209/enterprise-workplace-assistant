-- 1. Enums and Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('SUPER_ADMIN', 'HR_ADMIN', 'EMPLOYEE');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'onboarding_step_status') THEN
        CREATE TYPE onboarding_step_status AS ENUM ('PENDING', 'IN_PROGRESS', 'WAITING_VERIFICATION', 'COMPLETED');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'candidate_status') THEN
        CREATE TYPE candidate_status AS ENUM ('APPLIED', 'SCREENING', 'SHORTLISTED', 'REJECTED', 'HIRED');
    END IF;
END $$;

-- 2. Profiles Table (Linked to auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    role user_role DEFAULT 'EMPLOYEE'::user_role,
    avatar_url TEXT,
    onboarding_status VARCHAR(50) DEFAULT 'NOT_STARTED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS on Profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to profiles" 
    ON public.profiles FOR SELECT 
    USING (true);

CREATE POLICY "Allow users to update their own profile" 
    ON public.profiles FOR UPDATE 
    USING (auth.uid() = id);

-- 3. Jobs Table (Hiring module)
CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    description TEXT NOT NULL,
    requirements TEXT[] DEFAULT '{}'::TEXT[],
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_by UUID REFERENCES public.profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS on Jobs
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow read access to all profiles for jobs"
    ON public.jobs FOR SELECT
    USING (true);

CREATE POLICY "Allow HR admins to manage jobs"
    ON public.jobs FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role IN ('HR_ADMIN', 'SUPER_ADMIN')
        )
    );

-- 4. Candidates Table (Resume screening module)
CREATE TABLE IF NOT EXISTS public.candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    resume_file_path TEXT NOT NULL,
    suitability_score INT DEFAULT 0,
    match_explanation TEXT,
    parsed_skills TEXT[] DEFAULT '{}'::TEXT[],
    parsed_experience JSONB DEFAULT '{}'::JSONB,
    status candidate_status DEFAULT 'APPLIED'::candidate_status,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS on Candidates
ALTER TABLE public.candidates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow HR/Super admins to manage candidates"
    ON public.candidates FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role IN ('HR_ADMIN', 'SUPER_ADMIN')
        )
    );

-- 5. Onboarding Steps Table
CREATE TABLE IF NOT EXISTS public.onboarding_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    is_required BOOLEAN DEFAULT TRUE,
    target_role user_role DEFAULT 'EMPLOYEE'::user_role,
    order_index INT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS on Onboarding Steps
ALTER TABLE public.onboarding_steps ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all authenticated users to read onboarding steps"
    ON public.onboarding_steps FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Allow HR/Super admins to manage onboarding steps"
    ON public.onboarding_steps FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role IN ('HR_ADMIN', 'SUPER_ADMIN')
        )
    );

-- 6. Employee Onboarding Tasks Table
CREATE TABLE IF NOT EXISTS public.employee_onboarding_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    step_id UUID REFERENCES public.onboarding_steps(id) ON DELETE CASCADE,
    status onboarding_step_status DEFAULT 'PENDING'::onboarding_step_status,
    document_file_path TEXT,
    completed_at TIMESTAMP WITH TIME ZONE,
    verified_by_hr_id UUID REFERENCES public.profiles(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS on Employee Onboarding Tasks
ALTER TABLE public.employee_onboarding_tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow employees to view and update their own onboarding tasks"
    ON public.employee_onboarding_tasks FOR SELECT
    USING (auth.uid() = employee_id);

CREATE POLICY "Allow employees to update files on their own tasks"
    ON public.employee_onboarding_tasks FOR UPDATE
    USING (auth.uid() = employee_id);

CREATE POLICY "Allow HR/Super admins to view and manage all onboarding tasks"
    ON public.employee_onboarding_tasks FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role IN ('HR_ADMIN', 'SUPER_ADMIN')
        )
    );

-- 7. Company Documents Table (Knowledge RAG)
CREATE TABLE IF NOT EXISTS public.company_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    category VARCHAR(100),
    file_type VARCHAR(10),
    uploaded_by UUID REFERENCES public.profiles(id),
    chroma_collection_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS on Company Documents
ALTER TABLE public.company_documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all authenticated users to read company documents"
    ON public.company_documents FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Allow HR/Super admins to manage company documents"
    ON public.company_documents FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role IN ('HR_ADMIN', 'SUPER_ADMIN')
        )
    );



-- 10. Automatically Create Profile on User Signup (Trigger)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, role)
    VALUES (
        new.id,
        new.email,
        COALESCE(new.raw_user_meta_data->>'full_name', ''),
        COALESCE((new.raw_user_meta_data->>'role')::user_role, 'EMPLOYEE'::user_role)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
