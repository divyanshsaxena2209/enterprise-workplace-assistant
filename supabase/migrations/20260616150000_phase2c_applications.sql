




CREATE EXTENSION IF NOT EXISTS "uuid-ossp";




DROP TYPE IF EXISTS application_status CASCADE;
CREATE TYPE application_status AS ENUM ('Applied', 'Under Review');




CREATE TABLE IF NOT EXISTS public.applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES public.candidates(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    status application_status DEFAULT 'Applied'::application_status NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);


ALTER TABLE public.applications
    ADD COLUMN IF NOT EXISTS status application_status DEFAULT 'Applied'::application_status NOT NULL,
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT false NOT NULL;


DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'applications_job_id_candidate_id_key'
    ) THEN
        ALTER TABLE public.applications ADD CONSTRAINT applications_job_id_candidate_id_key UNIQUE (job_id, candidate_id);
    END IF;
END $$;



CREATE INDEX IF NOT EXISTS idx_applications_job ON public.applications (job_id);
CREATE INDEX IF NOT EXISTS idx_applications_candidate ON public.applications (candidate_id);
CREATE INDEX IF NOT EXISTS idx_applications_user ON public.applications (user_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON public.applications (status);
CREATE INDEX IF NOT EXISTS idx_applications_is_deleted ON public.applications (is_deleted);


DROP TRIGGER IF EXISTS applications_set_updated_at ON public.applications;
CREATE TRIGGER applications_set_updated_at
    BEFORE UPDATE ON public.applications
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();




ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;


DROP POLICY IF EXISTS "Allow management to read all applications" ON public.applications;
CREATE POLICY "Allow management to read all applications"
    ON public.applications FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role = 'MANAGEMENT'
        )
    );


DROP POLICY IF EXISTS "Allow employees to read own applications" ON public.applications;
CREATE POLICY "Allow employees to read own applications"
    ON public.applications FOR SELECT
    USING (
        user_id = auth.uid()
    );


DROP POLICY IF EXISTS "Allow authenticated to insert applications" ON public.applications;
CREATE POLICY "Allow authenticated to insert applications"
    ON public.applications FOR INSERT
    WITH CHECK (
        auth.role() = 'authenticated'
        AND user_id = auth.uid()
    );


DROP POLICY IF EXISTS "Allow management to update applications" ON public.applications;
CREATE POLICY "Allow management to update applications"
    ON public.applications FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role = 'MANAGEMENT'
        )
    );


DROP POLICY IF EXISTS "Allow service role full access to applications" ON public.applications;
CREATE POLICY "Allow service role full access to applications"
    ON public.applications FOR ALL
    USING (true);
