-- =============================================================================
-- Phase 2C: Candidate Applications Migration
-- =============================================================================

-- Ensure uuid-ossp is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- 1. Application Status Enum
-- ---------------------------------------------------------------------------
DROP TYPE IF EXISTS application_status CASCADE;
CREATE TYPE application_status AS ENUM ('Applied', 'Under Review');

-- ---------------------------------------------------------------------------
-- 2. Applications Table
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES public.candidates(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    status application_status DEFAULT 'Applied'::application_status NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Add columns if the table already existed from previous schema drafts
ALTER TABLE public.applications
    ADD COLUMN IF NOT EXISTS status application_status DEFAULT 'Applied'::application_status NOT NULL,
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT false NOT NULL;

-- Add unique constraint to prevent duplicate applications
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'applications_job_id_candidate_id_key'
    ) THEN
        ALTER TABLE public.applications ADD CONSTRAINT applications_job_id_candidate_id_key UNIQUE (job_id, candidate_id);
    END IF;
END $$;


-- Indexes for filtering and searching
CREATE INDEX IF NOT EXISTS idx_applications_job ON public.applications (job_id);
CREATE INDEX IF NOT EXISTS idx_applications_candidate ON public.applications (candidate_id);
CREATE INDEX IF NOT EXISTS idx_applications_user ON public.applications (user_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON public.applications (status);
CREATE INDEX IF NOT EXISTS idx_applications_is_deleted ON public.applications (is_deleted);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS applications_set_updated_at ON public.applications;
CREATE TRIGGER applications_set_updated_at
    BEFORE UPDATE ON public.applications
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
-- 3. RLS Policies
-- ---------------------------------------------------------------------------
ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;

-- Management can read all applications
DROP POLICY IF EXISTS "Allow management to read all applications" ON public.applications;
CREATE POLICY "Allow management to read all applications"
    ON public.applications FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role = 'MANAGEMENT'
        )
    );

-- Employees can read their own applications
DROP POLICY IF EXISTS "Allow employees to read own applications" ON public.applications;
CREATE POLICY "Allow employees to read own applications"
    ON public.applications FOR SELECT
    USING (
        user_id = auth.uid()
    );

-- Authenticated users (employees) can insert applications
DROP POLICY IF EXISTS "Allow authenticated to insert applications" ON public.applications;
CREATE POLICY "Allow authenticated to insert applications"
    ON public.applications FOR INSERT
    WITH CHECK (
        auth.role() = 'authenticated'
        AND user_id = auth.uid()
    );

-- Management can update applications (e.g. status)
DROP POLICY IF EXISTS "Allow management to update applications" ON public.applications;
CREATE POLICY "Allow management to update applications"
    ON public.applications FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role = 'MANAGEMENT'
        )
    );

-- Service role has full access
DROP POLICY IF EXISTS "Allow service role full access to applications" ON public.applications;
CREATE POLICY "Allow service role full access to applications"
    ON public.applications FOR ALL
    USING (true);
