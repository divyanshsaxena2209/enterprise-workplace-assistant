




CREATE EXTENSION IF NOT EXISTS "uuid-ossp";




DROP TYPE IF EXISTS job_status CASCADE;
CREATE TYPE job_status AS ENUM ('Draft', 'Published', 'Closed', 'Archived');




CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    department TEXT NOT NULL,
    location TEXT,
    employment_type TEXT,
    experience_required TEXT,
    description TEXT NOT NULL,
    requirements TEXT NOT NULL,
    responsibilities TEXT,
    salary_range TEXT,
    status job_status DEFAULT 'Draft'::job_status NOT NULL,
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    is_deleted BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);


CREATE INDEX IF NOT EXISTS idx_jobs_status ON public.jobs (status);
CREATE INDEX IF NOT EXISTS idx_jobs_department ON public.jobs (department);
CREATE INDEX IF NOT EXISTS idx_jobs_is_deleted ON public.jobs (is_deleted);

CREATE INDEX IF NOT EXISTS idx_jobs_title ON public.jobs (title);


DROP TRIGGER IF EXISTS jobs_set_updated_at ON public.jobs;
CREATE TRIGGER jobs_set_updated_at
    BEFORE UPDATE ON public.jobs
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();




ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;


DROP POLICY IF EXISTS "Allow authenticated users to read published jobs" ON public.jobs;
CREATE POLICY "Allow authenticated users to read published jobs"
    ON public.jobs FOR SELECT
    USING (
        auth.role() = 'authenticated' 
        AND status = 'Published'::job_status 
        AND is_deleted = false
    );


DROP POLICY IF EXISTS "Allow management to read all jobs" ON public.jobs;
CREATE POLICY "Allow management to read all jobs"
    ON public.jobs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role = 'MANAGEMENT'
        )
    );


DROP POLICY IF EXISTS "Allow management to insert jobs" ON public.jobs;
CREATE POLICY "Allow management to insert jobs"
    ON public.jobs FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role = 'MANAGEMENT'
        )
    );

DROP POLICY IF EXISTS "Allow management to update jobs" ON public.jobs;
CREATE POLICY "Allow management to update jobs"
    ON public.jobs FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role = 'MANAGEMENT'
        )
    );


DROP POLICY IF EXISTS "Allow service role full access to jobs" ON public.jobs;
CREATE POLICY "Allow service role full access to jobs"
    ON public.jobs FOR ALL
    USING (true);
