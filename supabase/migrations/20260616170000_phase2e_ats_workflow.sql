-- =============================================================================
-- Phase 2E: ATS Workflow Management & Recruiter Collaboration
-- =============================================================================

-- Ensure uuid-ossp is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- 1. Alter Application Status ENUM
-- ---------------------------------------------------------------------------
-- Note: ALTER TYPE cannot run inside a transaction block in standard PG,
-- but most migration runners will execute these successfully.
ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'Shortlisted';
ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'Interview Scheduled';
ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'Interview Completed';
ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'Offer Extended';
ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'Hired';
ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'Rejected';

-- ---------------------------------------------------------------------------
-- 2. Application Status History Table
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.application_status_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID NOT NULL REFERENCES public.applications(id) ON DELETE CASCADE,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_app_status_history_application ON public.application_status_history (application_id);
CREATE INDEX IF NOT EXISTS idx_app_status_history_created_at ON public.application_status_history (created_at DESC);

-- RLS
ALTER TABLE public.application_status_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow management full access to status history" ON public.application_status_history;
CREATE POLICY "Allow management full access to status history"
    ON public.application_status_history FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role = 'MANAGEMENT'
        )
    );

DROP POLICY IF EXISTS "Allow service role full access to status history" ON public.application_status_history;
CREATE POLICY "Allow service role full access to status history"
    ON public.application_status_history FOR ALL
    USING (true);


-- ---------------------------------------------------------------------------
-- 3. Recruiter Notes Table
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.recruiter_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID NOT NULL REFERENCES public.applications(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    note TEXT NOT NULL,
    is_deleted BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_recruiter_notes_application ON public.recruiter_notes (application_id);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS recruiter_notes_set_updated_at ON public.recruiter_notes;
CREATE TRIGGER recruiter_notes_set_updated_at
    BEFORE UPDATE ON public.recruiter_notes
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- RLS
ALTER TABLE public.recruiter_notes ENABLE ROW LEVEL SECURITY;

-- Management can view and create notes
DROP POLICY IF EXISTS "Allow management to read and create notes" ON public.recruiter_notes;
CREATE POLICY "Allow management to read and create notes"
    ON public.recruiter_notes FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role = 'MANAGEMENT'
        )
    );

-- (Update and Delete are restricted in the service layer to authors or management, 
-- but the DB policy permits ALL for management, meaning the application logic will enforce the author check)

DROP POLICY IF EXISTS "Allow service role full access to recruiter notes" ON public.recruiter_notes;
CREATE POLICY "Allow service role full access to recruiter notes"
    ON public.recruiter_notes FOR ALL
    USING (true);
